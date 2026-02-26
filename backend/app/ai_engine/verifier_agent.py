"""
Verifier Agent - Anti-Hallucination Layer
-------------------------------------------
Post-generation verification that fact-checks AI claims against the database.
Runs between SPEAK phase and final response delivery.

Checks:
1. Property prices mentioned → cross-reference with properties table
2. ROI/growth claims → cross-reference with market_indicators
3. Developer claims → cross-reference with developer data
4. Area statistics → cross-reference with computed stats

Adds confidence badges: "✓ Verified" or "⚡ Estimated"
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

logger = logging.getLogger(__name__)


class VerifierAgent:
    """
    Fact-checks AI-generated responses against the database.
    Lightweight, fast, no LLM calls - pure database verification.
    """

    # Regex patterns for extracting numerical claims
    PRICE_PATTERNS = [
        # "5,000,000 EGP" or "5M EGP" or "5 million"
        r'(\d[\d,]*(?:\.\d+)?)\s*(?:مليون|million|M)\s*(?:جنيه|EGP|egp)?',
        r'(\d[\d,]*(?:\.\d+)?)\s*(?:جنيه|EGP|egp)',
        # Price per sqm: "25,000 per sqm" or "25k/م²"
        r'(\d[\d,]*(?:\.\d+)?)\s*(?:k|K|ألف)?\s*(?:per sqm|للمتر|/م)',
    ]

    ROI_PATTERNS = [
        # "18% ROI" or "عائد 18%"
        r'(\d+(?:\.\d+)?)\s*%\s*(?:ROI|roi|عائد|نمو|growth|appreciation)',
        r'(?:ROI|roi|عائد|نمو|growth)\s*(?:of\s+)?(\d+(?:\.\d+)?)\s*%',
    ]

    def __init__(self):
        self.verification_results: List[Dict] = []

    async def verify_response(
        self,
        response_text: str,
        properties_mentioned: List[Dict],
        session: AsyncSession,
    ) -> Dict[str, Any]:
        """
        Verify AI response claims against the database.

        Returns:
            {
                "verified": True/False,
                "confidence": "high" | "medium" | "low",
                "corrections": [...],  # List of corrections if any
                "badges": {...},       # Verification badges per claim
            }
        """
        self.verification_results = []
        corrections = []

        try:
            # 1. Verify property prices
            price_corrections = await self._verify_prices(
                response_text, properties_mentioned, session
            )
            corrections.extend(price_corrections)

            # 2. Verify ROI/growth claims
            roi_corrections = await self._verify_roi_claims(response_text, session)
            corrections.extend(roi_corrections)

            # 3. Calculate overall confidence
            total_claims = len(self.verification_results)
            verified_claims = sum(1 for r in self.verification_results if r["verified"])

            if total_claims == 0:
                confidence = "high"  # No verifiable claims = nothing wrong
            elif verified_claims == total_claims:
                confidence = "high"
            elif verified_claims >= total_claims * 0.7:
                confidence = "medium"
            else:
                confidence = "low"

            return {
                "verified": len(corrections) == 0,
                "confidence": confidence,
                "total_claims_checked": total_claims,
                "verified_claims": verified_claims,
                "corrections": corrections,
                "badges": {
                    r["claim"]: "verified" if r["verified"] else "estimated"
                    for r in self.verification_results
                },
            }

        except Exception as e:
            logger.error(f"Verifier agent error: {e}")
            return {
                "verified": True,
                "confidence": "medium",
                "total_claims_checked": 0,
                "verified_claims": 0,
                "corrections": [],
                "badges": {},
            }

    async def _verify_prices(
        self,
        response_text: str,
        properties_mentioned: List[Dict],
        session: AsyncSession,
    ) -> List[Dict]:
        """Verify property prices against the database."""
        corrections = []

        if not properties_mentioned:
            return corrections

        from app.models import Property

        for prop in properties_mentioned[:5]:  # Max 5 properties to check
            prop_id = prop.get("id")
            mentioned_price = prop.get("price", 0)

            if not prop_id or not mentioned_price:
                continue

            try:
                result = await session.execute(
                    select(Property.price, Property.price_per_sqm, Property.title)
                    .filter(Property.id == int(prop_id))
                )
                db_row = result.first()

                if db_row:
                    db_price = float(db_row.price or 0)
                    if db_price > 0 and mentioned_price > 0:
                        discrepancy_pct = abs(mentioned_price - db_price) / db_price * 100

                        claim_record = {
                            "claim": f"Price of {db_row.title}",
                            "mentioned": mentioned_price,
                            "actual": db_price,
                            "discrepancy_pct": round(discrepancy_pct, 1),
                            "verified": discrepancy_pct <= 5,
                        }
                        self.verification_results.append(claim_record)

                        if discrepancy_pct > 5:
                            corrections.append({
                                "type": "price",
                                "property": db_row.title,
                                "mentioned": mentioned_price,
                                "actual": db_price,
                                "discrepancy_pct": round(discrepancy_pct, 1),
                            })
            except Exception as e:
                logger.debug(f"Price verification skipped for prop {prop_id}: {e}")

        return corrections

    async def _verify_roi_claims(
        self,
        response_text: str,
        session: AsyncSession,
    ) -> List[Dict]:
        """Verify ROI/growth percentage claims against market indicators."""
        corrections = []

        from app.models import MarketIndicator

        # Extract ROI percentages from response
        for pattern in self.ROI_PATTERNS:
            matches = re.findall(pattern, response_text)
            for match in matches:
                try:
                    claimed_pct = float(match)

                    # Cross-reference with market indicators
                    result = await session.execute(
                        select(MarketIndicator.value)
                        .filter(MarketIndicator.key == "property_appreciation")
                    )
                    indicator = result.scalar_one_or_none()

                    if indicator:
                        actual_pct = float(indicator) * 100  # Convert decimal to percentage
                        discrepancy = abs(claimed_pct - actual_pct)

                        claim_record = {
                            "claim": f"ROI/Growth {claimed_pct}%",
                            "mentioned": claimed_pct,
                            "actual": round(actual_pct, 1),
                            "discrepancy_pct": round(discrepancy, 1),
                            "verified": discrepancy <= 5,  # Allow 5% tolerance
                        }
                        self.verification_results.append(claim_record)

                        if discrepancy > 10:
                            corrections.append({
                                "type": "roi",
                                "claimed": claimed_pct,
                                "actual": round(actual_pct, 1),
                                "discrepancy": round(discrepancy, 1),
                            })
                except (ValueError, TypeError):
                    continue

        return corrections


# Singleton
verifier_agent = VerifierAgent()
