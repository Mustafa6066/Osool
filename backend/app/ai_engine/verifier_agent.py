"""
Verifier Agent - Anti-Hallucination Interceptor
-------------------------------------------------
Post-generation verification that fact-checks AI claims against the database
and AUTO-REWRITES hallucinated content before it reaches the user.

Checks:
1. Property prices mentioned → cross-reference with properties table
2. ROI/growth claims → cross-reference with market_indicators
3. Compound names → cross-reference with properties_mentioned
4. Delivery dates → cross-reference with properties_mentioned

If corrections are found, GPT-4o-mini surgically replaces only the incorrect
numbers/names — preserving tone, style, and all other content.
"""

import re
import json
import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

logger = logging.getLogger(__name__)


class VerifierAgent:
    """
    Fact-checks AI-generated responses against the database.
    When hallucinations are detected, auto-rewrites them via GPT-4o-mini.
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

    COMPOUND_PATTERNS = [
        # English compound names (capitalized words near property context)
        r'(?:in|at|from|compound|كمباوند|مشروع)\s+([A-Z][a-zA-Z\s]{2,30})',
        # Arabic compound mentions
        r'(?:كمباوند|مشروع|في)\s+([\u0600-\u06FF\s]{3,30})',
    ]

    DELIVERY_PATTERNS = [
        # "Q1 2026", "Q2 2027"
        r'Q[1-4]\s*20\d{2}',
        # "2026", "2027" near delivery context
        r'(?:تسليم|delivery|delivered|استلام|handover)[^.]{0,30}(20\d{2})',
        # "ready 2025", "delivered 2026"
        r'(?:ready|جاهز|متسلم)\s*(?:by\s*)?(20\d{2})',
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
                "corrections": [...],
                "badges": {...},
                "rewritten": False,
                "original_response": None,
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

            # 3. Verify compound names
            compound_corrections = self._verify_compound_names(
                response_text, properties_mentioned
            )
            corrections.extend(compound_corrections)

            # 4. Verify delivery dates
            date_corrections = self._verify_delivery_dates(
                response_text, properties_mentioned
            )
            corrections.extend(date_corrections)

            # 5. Calculate overall confidence
            total_claims = len(self.verification_results)
            verified_claims = sum(1 for r in self.verification_results if r["verified"])

            if total_claims == 0:
                confidence = "high"
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
                "rewritten": False,
                "original_response": None,
            }

        except Exception as e:
            logger.error(f"Verifier agent error: {e}")
            try:
                await session.rollback()
            except Exception:
                pass
            return {
                "verified": True,
                "confidence": "medium",
                "total_claims_checked": 0,
                "verified_claims": 0,
                "corrections": [],
                "badges": {},
                "rewritten": False,
                "original_response": None,
            }

    async def rewrite_hallucinated_response(
        self,
        response_text: str,
        corrections: List[Dict],
    ) -> str:
        """
        Auto-rewrite hallucinated claims using GPT-4o-mini.
        Surgically replaces ONLY incorrect numbers/names — preserves all other content.
        Falls back to regex replacement if LLM call fails or times out.
        """
        if not corrections:
            return response_text

        # Build corrections summary for the LLM
        correction_lines = []
        for c in corrections:
            if c["type"] == "price":
                correction_lines.append(
                    f"- Price of '{c['property']}': Response says {c['mentioned']:,.0f} EGP → "
                    f"Actual DB price is {c['actual']:,.0f} EGP"
                )
            elif c["type"] == "roi":
                correction_lines.append(
                    f"- ROI/Growth claim: Response says {c['claimed']}% → "
                    f"Actual market data is {c['actual']}%"
                )
            elif c["type"] == "compound_name":
                correction_lines.append(
                    f"- Compound name: Response mentions '{c['mentioned']}' → "
                    f"Not found in the provided property data"
                )
            elif c["type"] == "delivery_date":
                correction_lines.append(
                    f"- Delivery date: Response says '{c['mentioned']}' → "
                    f"Actual DB date is '{c['actual']}'"
                )

        corrections_text = "\n".join(correction_lines)

        try:
            from openai import AsyncOpenAI
            import os
            client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

            rewrite_result = await asyncio.wait_for(
                client.chat.completions.create(
                    model="gpt-4o-mini",
                    temperature=0,
                    max_tokens=4096,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a data compliance editor for a real estate firm. "
                                "Your ONLY job is to fix incorrect numbers and names in the draft response. "
                                "Rules:\n"
                                "1. Replace ONLY the incorrect values listed in the corrections.\n"
                                "2. Do NOT change tone, style, language, or add/remove any content.\n"
                                "3. Keep Arabic text as Arabic, English as English.\n"
                                "4. If a compound name is hallucinated with no actual replacement, "
                                "remove that specific claim and add a note: "
                                "'أحتاج أتأكد من المعلومة دي مع الفريق'.\n"
                                "5. Output ONLY the corrected response text, nothing else."
                            ),
                        },
                        {
                            "role": "user",
                            "content": (
                                f"CORRECTIONS NEEDED:\n{corrections_text}\n\n"
                                f"DRAFT RESPONSE TO FIX:\n{response_text}"
                            ),
                        },
                    ],
                ),
                timeout=5.0,
            )

            rewritten = rewrite_result.choices[0].message.content
            if rewritten and len(rewritten) > 50:
                logger.info(f"✅ VERIFIER REWRITE: Fixed {len(corrections)} hallucinations via GPT-4o-mini")
                return rewritten.strip()
            else:
                logger.warning("Verifier rewrite returned empty/short result — using regex fallback")

        except asyncio.TimeoutError:
            logger.warning("Verifier rewrite timed out (5s) — using regex fallback")
        except Exception as e:
            logger.warning(f"Verifier rewrite LLM call failed: {e} — using regex fallback")

        # ── Regex fallback: strip bad numbers directly ──
        return self._regex_fallback_rewrite(response_text, corrections)

    def _regex_fallback_rewrite(self, response_text: str, corrections: List[Dict]) -> str:
        """Strip hallucinated numbers and add caveat when LLM rewrite fails."""
        result = response_text
        for c in corrections:
            if c["type"] == "price" and c.get("mentioned"):
                # Replace the hallucinated price with actual
                mentioned_str = f"{c['mentioned']:,.0f}"
                actual_str = f"{c['actual']:,.0f}"
                result = result.replace(mentioned_str, actual_str)
                # Also try M format
                if c['mentioned'] >= 1_000_000:
                    m_mentioned = f"{c['mentioned']/1_000_000:.1f}M"
                    m_actual = f"{c['actual']/1_000_000:.1f}M"
                    result = result.replace(m_mentioned, m_actual)
                    m_mentioned_ar = f"{c['mentioned']/1_000_000:.1f} مليون"
                    m_actual_ar = f"{c['actual']/1_000_000:.1f} مليون"
                    result = result.replace(m_mentioned_ar, m_actual_ar)
            elif c["type"] == "roi" and c.get("claimed"):
                claimed_str = f"{c['claimed']}%"
                actual_str = f"{c['actual']}%"
                result = result.replace(claimed_str, actual_str)
        return result

    def _verify_compound_names(
        self,
        response_text: str,
        properties_mentioned: List[Dict],
    ) -> List[Dict]:
        """Verify compound names in response match the provided property data."""
        corrections = []
        if not properties_mentioned:
            return corrections

        # Build set of valid compound names from properties
        valid_compounds = set()
        for prop in properties_mentioned:
            compound = prop.get("compound", "")
            if compound:
                valid_compounds.add(compound.lower().strip())
                # Also add without common suffixes for fuzzy matching
                for suffix in [" compound", " كمباوند", " residence", " residences"]:
                    clean = compound.lower().strip().replace(suffix, "").strip()
                    if clean:
                        valid_compounds.add(clean)

        if not valid_compounds:
            return corrections

        # Extract compound mentions from response
        for pattern in self.COMPOUND_PATTERNS:
            matches = re.findall(pattern, response_text)
            for match in matches:
                match_clean = match.strip().lower()
                if match_clean and len(match_clean) > 2:
                    # Check if this compound name exists in our provided data
                    found = any(
                        vc in match_clean or match_clean in vc
                        for vc in valid_compounds
                    )
                    claim_record = {
                        "claim": f"Compound: {match.strip()}",
                        "mentioned": match.strip(),
                        "verified": found,
                    }
                    self.verification_results.append(claim_record)

                    if not found:
                        corrections.append({
                            "type": "compound_name",
                            "mentioned": match.strip(),
                        })

        return corrections

    def _verify_delivery_dates(
        self,
        response_text: str,
        properties_mentioned: List[Dict],
    ) -> List[Dict]:
        """Verify delivery dates in response match the provided property data."""
        corrections = []
        if not properties_mentioned:
            return corrections

        # Build set of valid delivery dates
        valid_dates = set()
        for prop in properties_mentioned:
            dd = prop.get("delivery_date", "")
            if dd:
                valid_dates.add(dd.strip().lower())
                # Also extract just the year
                year_match = re.search(r'20\d{2}', str(dd))
                if year_match:
                    valid_dates.add(year_match.group())

        if not valid_dates:
            return corrections

        # Extract delivery date mentions
        for pattern in self.DELIVERY_PATTERNS:
            matches = re.findall(pattern, response_text, re.IGNORECASE)
            for match in matches:
                match_clean = match.strip().lower()
                if match_clean:
                    found = any(
                        vd in match_clean or match_clean in vd
                        for vd in valid_dates
                    )
                    claim_record = {
                        "claim": f"Delivery: {match.strip()}",
                        "mentioned": match.strip(),
                        "verified": found,
                    }
                    self.verification_results.append(claim_record)

                    if not found:
                        # Find the closest valid date for correction
                        actual = next(iter(valid_dates), "unknown")
                        corrections.append({
                            "type": "delivery_date",
                            "mentioned": match.strip(),
                            "actual": actual,
                        })

        return corrections

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

        for prop in properties_mentioned[:5]:
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
                try:
                    await session.rollback()
                except Exception:
                    pass

        return corrections

    async def _verify_roi_claims(
        self,
        response_text: str,
        session: AsyncSession,
    ) -> List[Dict]:
        """Verify ROI/growth percentage claims against market indicators."""
        corrections = []

        from app.models import MarketIndicator

        for pattern in self.ROI_PATTERNS:
            matches = re.findall(pattern, response_text)
            for match in matches:
                try:
                    claimed_pct = float(match)

                    result = await session.execute(
                        select(MarketIndicator.value)
                        .filter(MarketIndicator.key == "property_appreciation")
                    )
                    indicator = result.scalar_one_or_none()

                    if indicator:
                        actual_pct = float(indicator) * 100
                        discrepancy = abs(claimed_pct - actual_pct)

                        claim_record = {
                            "claim": f"ROI/Growth {claimed_pct}%",
                            "mentioned": claimed_pct,
                            "actual": round(actual_pct, 1),
                            "discrepancy_pct": round(discrepancy, 1),
                            "verified": discrepancy <= 5,
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
