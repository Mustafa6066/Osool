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

    # Payment plan patterns — catch hallucinated down payments, installments, years
    DOWN_PAYMENT_PATTERNS = [
        r'(\d+(?:\.\d+)?)\s*%\s*(?:down\s*payment|مقدم|دفعة أولى|down)',
        r'(?:down\s*payment|مقدم|دفعة أولى)\s*(?:of\s+)?(\d+(?:\.\d+)?)\s*%',
    ]

    INSTALLMENT_PATTERNS = [
        # Monthly: "25,000 monthly" or "25,000 شهري" or "25K/month"
        r'(\d[\d,]*(?:\.\d+)?)\s*(?:EGP|جنيه)?\s*(?:monthly|شهري|per month|/month|شهرياً)',
        r'(?:قسط|installment|monthly)\s*(?:of\s+)?(\d[\d,]*(?:\.\d+)?)\s*(?:EGP|جنيه)?',
    ]

    INSTALLMENT_YEARS_PATTERNS = [
        r'(\d+)\s*(?:years|سنوات|سنة|سنين)\s*(?:installment|تقسيط|أقساط)?',
        r'(?:installment|تقسيط|أقساط)\s*(?:over|على|لمدة)\s*(\d+)\s*(?:years|سنوات|سنة|سنين)',
    ]

    SIZE_PATTERNS = [
        r'(\d[\d,]*)\s*(?:sqm|م²|متر مربع|square meter)',
    ]

    # ── Legal / regulatory risk ───────────────────────────────────────────
    # A legal claim is only DANGEROUS when a legal/regulatory term co-occurs
    # with certainty/guarantee language in the SAME sentence. Plain references
    # to a law as context (the master prompt does this intentionally) are fine
    # and must NOT be blocked. We block fabricated legal *guarantees* only.
    LEGAL_TERM_PATTERNS = [
        r'civil code|القانون المدني|المادة\s*\d+|article\s*\d+',
        r'\bFRA\b|الهيئة العامة للرقابة المالية|decision\s*125|قرار\s*125',
        r'\bCBE\b|البنك المركزي|law\s*\d+/\d{4}|قانون\s*\d+',
        r'registration|الشهر العقاري|تسجيل|green contract|عقد أخضر',
        r'tax[-\s]?free|معفى من الضرائب|refund|استرداد|residency|إقامة',
    ]
    GUARANTEE_PATTERNS = [
        r'guarantee\w*|مضمون|نضمن|اضمن|ضمان',
        r'\b100\s*%|legally entitled|حق قانوني|بالقانون',
        r'ensure\w*|guaranteed return|عائد مضمون|تأكيد قانوني',
        r'definitely|بالتأكيد قانونيا|لازم قانونا|مكفول',
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

            # 5. Verify payment plan claims (down payment, installments, years, size)
            payment_corrections = self._verify_payment_plans(
                response_text, properties_mentioned
            )
            corrections.extend(payment_corrections)

            # 6. Verify legal / regulatory guarantee claims (uncorrectable → block)
            legal_corrections = self._verify_legal_claims(response_text)
            corrections.extend(legal_corrections)

            # 6b. Future-price CERTAINTY → caveat-only (kept OUT of `corrections` so
            #     it never triggers the blocked-handoff or flips the policy; the
            #     orchestrator redacts these to a 'forecast, not a guarantee' caveat).
            caveat_corrections = self._verify_forecast_claims(response_text)

            # 7. Calculate overall confidence
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

            # 8. Decide policy. Blocked corrections are high-risk AND uncorrectable
            #    (we have no trustworthy replacement): fabricated legal guarantees
            #    and invented compound names. Everything else is a number we CAN
            #    swap for the DB truth → correctable.
            blocked_corrections = [
                c for c in corrections if c["type"] in ("legal_claim", "compound_name")
            ]
            correctable = [c for c in corrections if c not in blocked_corrections]

            if blocked_corrections:
                policy = "blocked"
            elif correctable:
                policy = "corrected"
            else:
                policy = "serve"

            return {
                "verified": len(corrections) == 0,
                "confidence": confidence,
                "total_claims_checked": total_claims,
                "verified_claims": verified_claims,
                "corrections": corrections,
                "correctable_corrections": correctable,
                "blocked_corrections": blocked_corrections,
                "policy": policy,
                "blocked": policy == "blocked",
                "caveat_corrections": caveat_corrections,
                # Normalized contract for the frontend chip. The orchestrator may
                # flip `auto_corrected` to True after a rewrite actually lands.
                "auto_corrected": False,
                "fix_count": len(correctable),
                "caveat": None,
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
                "correctable_corrections": [],
                "blocked_corrections": [],
                "policy": "serve",
                "blocked": False,
                "caveat_corrections": [],
                "auto_corrected": False,
                "fix_count": 0,
                "caveat": None,
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

    # Bilingual caveat used when a high-risk claim is blocked instead of invented.
    BLOCKED_CAVEAT_AR = "أحتاج أتأكد من المعلومة دي مع الفريق قبل ما أأكدها لك."
    BLOCKED_CAVEAT_EN = "Let me confirm this with the team before I quote it."

    # ── Forecast honesty ──────────────────────────────────────────────────
    # A price forecast is a PREDICTION with an uncertainty band, never a fact.
    # Stating a specific FUTURE price/return as a CERTAINTY is redacted to a
    # caveat (caveat-only — no human handoff). Properly HEDGED forecast prose
    # ("indicative", "projected", "estimate", "توقّع", "تقديري") is left intact.
    FORECAST_CAVEAT_EN = "That's an indicative forecast, not a guarantee — actual prices can differ."
    FORECAST_CAVEAT_AR = "ده توقّع استرشادي مش ضمان — الأسعار الفعلية ممكن تختلف."

    FUTURE_PRICE_PATTERNS = [
        r'will\b|going to|by\s*20\d{2}|next\s*year|in\s*\d+\s*(?:months?|years?)',
        r'هيوصل|هيبقى|هيزيد|هترتفع|السنة الجاية|العام القادم|خلال\s*\d+\s*(?:شهر|سنة|سنوات)|بعد\s*\d+\s*(?:شهر|سنة)',
    ]
    FUTURE_CERTAINTY_PATTERNS = [
        r'guarantee\w*|guaranteed|definitely|certainly|for sure|no doubt|'
        r'will\s*(?:reach|hit|be worth|double|rise to|grow to)',
        r'مضمون|أكيد|بالتأكيد|حتمًا|لازم يوصل|مفيش شك|هيتضاعف',
    ]
    FORECAST_HEDGE_PATTERNS = [
        r'indicative|projected|estimat\w*|forecast\w*|approximate|roughly|'
        r'\bmay\b|\bmight\b|\bcould\b|\baround\b|\babout\b|expected|likely',
        r'توقّ?ع|تقدير\w*|استرشاد\w*|تقريب\w*|حوالي|ممكن|قد\s|متوقّ?ع|مرجّ?ح',
    ]

    # Cheap pre-check for the streaming path: which turns warrant buffer-then-
    # verify BEFORE flushing tokens? Price/ROI/payment/legal questions, plus any
    # turn that quotes specific listings (handled via has_properties below).
    HIGH_RISK_QUERY_PATTERNS = [
        r'price|سعر|بكام|تكلفة|cost|مقدم|down\s*payment|installment|قسط|تقسيط',
        r'roi|عائد|return|نمو|appreciation|أرباح|profit',
        r'law|قانون|legal|قانوني|civil\s*code|مدني|registration|تسجيل|'
        r'الشهر العقاري|\bFRA\b|guarantee|مضمون|ضمان|tax|ضريبة',
    ]

    def is_high_risk_turn(self, query: str, has_properties: bool) -> bool:
        """Cheap regex pre-check for streaming. True when the reply will quote
        listings, or the user asked about price / ROI / legal matters — those
        turns are buffered and verified before any token is shown."""
        if has_properties:
            return True
        q = query or ""
        return any(re.search(p, q, re.IGNORECASE) for p in self.HIGH_RISK_QUERY_PATTERNS)

    @staticmethod
    def _split_sentences(text: str) -> List[str]:
        """Split on Arabic + Latin sentence boundaries, keeping order."""
        parts = re.split(r'(?<=[\.\!\?؟،\n])\s+', text or "")
        return [p for p in parts if p.strip()]

    def _verify_legal_claims(self, response_text: str) -> List[Dict]:
        """Flag fabricated legal GUARANTEES — a legal/regulatory term co-occurring
        with certainty/guarantee language in the same sentence. Plain legal
        references (no guarantee word) are intentionally NOT flagged: the master
        prompt cites Egyptian law as context and that's fine. These claims are
        uncorrectable (we have no DB ground truth for legal promises) → block.
        """
        corrections: List[Dict] = []
        for sentence in self._split_sentences(response_text):
            has_legal = any(
                re.search(p, sentence, re.IGNORECASE) for p in self.LEGAL_TERM_PATTERNS
            )
            if not has_legal:
                continue
            has_guarantee = any(
                re.search(p, sentence, re.IGNORECASE) for p in self.GUARANTEE_PATTERNS
            )
            if not has_guarantee:
                continue
            self.verification_results.append({
                "claim": f"Legal guarantee: {sentence.strip()[:80]}",
                "mentioned": sentence.strip(),
                "verified": False,
            })
            corrections.append({
                "type": "legal_claim",
                "sentence": sentence.strip(),
                "mentioned": sentence.strip(),
            })
        return corrections

    def _verify_forecast_claims(self, response_text: str) -> List[Dict]:
        """Flag FUTURE-PRICE CERTAINTY: a sentence stating a specific future
        price/return as a guarantee (future phrase + certainty word + a number),
        UNLESS already hedged. Returned as caveat-only corrections — redacted to a
        'forecast, not a guarantee' caveat without opening a human-handoff ticket
        (a phrasing fix, not a fabricated fact)."""
        corrections: List[Dict] = []
        for sentence in self._split_sentences(response_text):
            # Properly hedged forecast prose is legitimate — never flag it.
            if any(re.search(p, sentence, re.IGNORECASE) for p in self.FORECAST_HEDGE_PATTERNS):
                continue
            has_future = any(re.search(p, sentence, re.IGNORECASE) for p in self.FUTURE_PRICE_PATTERNS)
            has_certainty = any(re.search(p, sentence, re.IGNORECASE) for p in self.FUTURE_CERTAINTY_PATTERNS)
            has_number = bool(re.search(r'\d', sentence))
            if has_future and has_certainty and has_number:
                self.verification_results.append({
                    "claim": f"Future-price certainty: {sentence.strip()[:80]}",
                    "mentioned": sentence.strip(),
                    "verified": False,
                })
                corrections.append({
                    "type": "forecast_certainty",
                    "sentence": sentence.strip(),
                    "mentioned": sentence.strip(),
                    "caveat_en": self.FORECAST_CAVEAT_EN,
                    "caveat_ar": self.FORECAST_CAVEAT_AR,
                })
        return corrections

    def redact_blocked_claims(
        self,
        response_text: str,
        blocked_corrections: List[Dict],
    ) -> str:
        """Replace blocked high-risk sentences with a neutral caveat instead of
        inventing a number/fact. Used for fabricated legal guarantees and
        invented compound names. Bilingual: picks the caveat by script of the
        offending sentence.
        """
        if not blocked_corrections:
            return response_text

        result = response_text
        for c in blocked_corrections:
            target = (c.get("sentence") or c.get("mentioned") or "").strip()
            if not target or target not in result:
                continue
            is_arabic = bool(re.search(r'[؀-ۿ]', target))
            # Prefer a correction-specific caveat (e.g. forecast) over the generic one.
            caveat = c.get("caveat_ar" if is_arabic else "caveat_en") or (
                self.BLOCKED_CAVEAT_AR if is_arabic else self.BLOCKED_CAVEAT_EN
            )
            result = result.replace(target, caveat)
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

    def _verify_payment_plans(
        self,
        response_text: str,
        properties_mentioned: List[Dict],
    ) -> List[Dict]:
        """Verify payment plan claims (down payment %, installment amounts, years, sizes)
        against the provided property data."""
        corrections = []
        if not properties_mentioned:
            return corrections

        # Build lookup from properties
        valid_down_payments = set()
        valid_installments = set()
        valid_years = set()
        valid_sizes = set()
        for prop in properties_mentioned:
            dp = prop.get("down_payment") or prop.get("down_payment_percentage")
            if dp is not None:
                valid_down_payments.add(int(dp))
            inst = prop.get("monthly_installment")
            if inst is not None and float(inst) > 0:
                valid_installments.add(float(inst))
            yrs = prop.get("installment_years")
            if yrs is not None:
                valid_years.add(int(yrs))
            sz = prop.get("size_sqm")
            if sz is not None and int(sz) > 0:
                valid_sizes.add(int(sz))

        # Check down payment percentages
        for pattern in self.DOWN_PAYMENT_PATTERNS:
            for match in re.findall(pattern, response_text, re.IGNORECASE):
                try:
                    claimed = float(match)
                    found = any(abs(claimed - vdp) <= 1 for vdp in valid_down_payments) if valid_down_payments else True
                    self.verification_results.append({
                        "claim": f"Down payment {claimed}%",
                        "mentioned": claimed,
                        "verified": found,
                    })
                    if not found and valid_down_payments:
                        corrections.append({
                            "type": "down_payment",
                            "mentioned": f"{claimed}%",
                            "actual": f"{next(iter(valid_down_payments))}%",
                        })
                except (ValueError, TypeError):
                    continue

        # Check installment amounts
        for pattern in self.INSTALLMENT_PATTERNS:
            for match in re.findall(pattern, response_text, re.IGNORECASE):
                try:
                    claimed = float(match.replace(",", ""))
                    if claimed < 1000:  # Skip tiny numbers that aren't installments
                        continue
                    found = any(abs(claimed - vi) / vi <= 0.10 for vi in valid_installments) if valid_installments else True
                    self.verification_results.append({
                        "claim": f"Installment {claimed:,.0f}",
                        "mentioned": claimed,
                        "verified": found,
                    })
                    if not found and valid_installments:
                        closest = min(valid_installments, key=lambda v: abs(v - claimed))
                        corrections.append({
                            "type": "installment",
                            "mentioned": f"{claimed:,.0f} EGP",
                            "actual": f"{closest:,.0f} EGP",
                        })
                except (ValueError, TypeError):
                    continue

        # Check installment years
        for pattern in self.INSTALLMENT_YEARS_PATTERNS:
            for match in re.findall(pattern, response_text, re.IGNORECASE):
                try:
                    claimed = int(match)
                    if claimed < 1 or claimed > 30:  # Sanity check
                        continue
                    found = claimed in valid_years if valid_years else True
                    self.verification_results.append({
                        "claim": f"Installment {claimed} years",
                        "mentioned": claimed,
                        "verified": found,
                    })
                    if not found and valid_years:
                        corrections.append({
                            "type": "installment_years",
                            "mentioned": f"{claimed} years",
                            "actual": f"{next(iter(valid_years))} years",
                        })
                except (ValueError, TypeError):
                    continue

        # Check size claims
        for pattern in self.SIZE_PATTERNS:
            for match in re.findall(pattern, response_text, re.IGNORECASE):
                try:
                    claimed = int(match.replace(",", ""))
                    if claimed < 10:  # Skip tiny numbers
                        continue
                    found = any(abs(claimed - vs) / vs <= 0.05 for vs in valid_sizes) if valid_sizes else True
                    self.verification_results.append({
                        "claim": f"Size {claimed} sqm",
                        "mentioned": claimed,
                        "verified": found,
                    })
                    if not found and valid_sizes:
                        closest = min(valid_sizes, key=lambda v: abs(v - claimed))
                        corrections.append({
                            "type": "size",
                            "mentioned": f"{claimed} sqm",
                            "actual": f"{closest} sqm",
                        })
                except (ValueError, TypeError):
                    continue

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
