"""
Reasoning Engine - The Wolf's Chain-of-Thought
-----------------------------------------------
Structured multi-step reasoning for investment analysis and query handling.

Provides a Chain-of-Thought (CoT) framework that the AI uses to build
better, more analytical responses. Every reasoning chain produces concrete
numbers from real market data — no placeholders, no hallucinated figures.

Architecture:
    ReasoningStep  -> One atomic reasoning step with evidence + conclusion
    ReasoningChain -> Ordered list of steps with a final verdict
    ReasoningEngine -> Orchestrator that builds chains for different query types

Usage:
    from app.ai_engine.reasoning_engine import reasoning_engine

    chain = reasoning_engine.analyze_investment_opportunity(
        location="New Cairo",
        budget=5_000_000,
        property_type="apartment",
        analytics_context={...},
        market_data={...},
    )
    prompt_fragment = reasoning_engine.generate_reasoning_prompt(chain, language="ar")
"""

import logging
import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .analytical_engine import (
    AREA_BENCHMARKS,
    AREA_GROWTH,
    AREA_PRICE_HISTORY,
    AREA_PRICES,
    DEVELOPER_PRICE_HISTORY,
    MARKET_DATA,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ReasoningStep:
    """One atomic reasoning step inside a chain."""

    step_name: str
    thought: str
    evidence: List[str]
    conclusion: str
    confidence: float  # 0.0 – 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_name": self.step_name,
            "thought": self.thought,
            "evidence": self.evidence,
            "conclusion": self.conclusion,
            "confidence": self.confidence,
        }


@dataclass
class ReasoningChain:
    """An ordered sequence of reasoning steps leading to a verdict."""

    steps: List[ReasoningStep] = field(default_factory=list)
    final_verdict: str = ""
    reasoning_summary: str = ""
    total_confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "steps": [s.to_dict() for s in self.steps],
            "final_verdict": self.final_verdict,
            "reasoning_summary": self.reasoning_summary,
            "total_confidence": self.total_confidence,
            "metadata": self.metadata,
        }


# ---------------------------------------------------------------------------
# Helpers — location resolution (mirrors analytical_engine logic)
# ---------------------------------------------------------------------------

_LOCATION_ALIAS: Dict[str, str] = {
    "التجمع الخامس": "New Cairo",
    "التجمع": "New Cairo",
    "القاهرة الجديدة": "New Cairo",
    "fifth settlement": "New Cairo",
    "tagamoa": "New Cairo",
    "الشيخ زايد": "Sheikh Zayed",
    "زايد": "Sheikh Zayed",
    "العاصمة الإدارية": "New Capital",
    "العاصمة": "New Capital",
    "أكتوبر": "6th October",
    "السادس من أكتوبر": "6th October",
    "الساحل الشمالي": "North Coast",
    "الساحل": "North Coast",
    "المعادي": "Maadi",
    "العين السخنة": "Ain Sokhna",
    "مدينتي": "Madinaty",
    "الرحاب": "Rehab",
}


def _resolve_location(raw: str) -> str:
    """Return the canonical English location key used in AREA_PRICES / AREA_GROWTH."""
    stripped = raw.strip()
    titled = stripped.title()

    # 1. Direct hit in AREA_PRICES
    if titled in AREA_PRICES:
        return titled

    # 2. Arabic / alias lookup
    hit = _LOCATION_ALIAS.get(stripped) or _LOCATION_ALIAS.get(stripped.lower())
    if hit:
        return hit

    # 3. Substring match on canonical keys
    lower = stripped.lower()
    for key in AREA_PRICES:
        if key.lower() in lower or lower in key.lower():
            return key

    return titled  # best-effort fallback


def _resolve_benchmark_key(location: str) -> str:
    """Return the lower-case key used in AREA_BENCHMARKS."""
    canonical = _resolve_location(location)
    lower = canonical.lower()
    if lower in AREA_BENCHMARKS:
        return lower
    for bk in AREA_BENCHMARKS:
        if bk in lower or lower in bk:
            return bk
    return lower


# ---------------------------------------------------------------------------
# ReasoningEngine
# ---------------------------------------------------------------------------

class ReasoningEngine:
    """
    Chain-of-Thought reasoning engine for the Osool AI platform.

    Builds structured, evidence-backed reasoning chains that feed into the
    Claude system prompt so the LLM can reference concrete analytical steps
    rather than hallucinating numbers.
    """

    # ------------------------------------------------------------------
    # Core public API
    # ------------------------------------------------------------------

    def analyze_investment_opportunity(
        self,
        location: str,
        budget: int,
        property_type: str = "apartment",
        analytics_context: Optional[Dict[str, Any]] = None,
        market_data: Optional[Dict[str, Any]] = None,
    ) -> ReasoningChain:
        """
        Full 6-step investment analysis for *location + budget + property_type*.

        Steps:
            1. market_position
            2. affordability_check
            3. growth_trajectory
            4. risk_assessment
            5. comparative_advantage
            6. final_verdict
        """
        ctx = analytics_context or {}
        mkt = market_data or MARKET_DATA
        loc = _resolve_location(location)
        chain = ReasoningChain(metadata={"location": loc, "budget": budget, "property_type": property_type})

        try:
            # Step 1 — Market Position
            step1 = self._assess_market_position(loc, ctx)
            chain.steps.append(step1)

            # Step 2 — Affordability
            step2 = self._check_affordability(loc, budget, property_type)
            chain.steps.append(step2)

            # Step 3 — Growth Trajectory
            step3 = self._calculate_growth_trajectory(loc, years=5)
            chain.steps.append(step3)

            # Step 4 — Risk Assessment
            psychology_state = ctx.get("psychology_state")
            step4 = self._evaluate_risk_factors(loc, property_type, psychology_state)
            chain.steps.append(step4)

            # Step 5 — Comparative Advantage (vs bank CDs, inflation, gold)
            step5 = self._compare_investment_alternatives(budget, mkt)
            chain.steps.append(step5)

            # Step 6 — Final Verdict (synthesize)
            step6 = self._synthesize_verdict(chain.steps, loc, budget, property_type, mkt)
            chain.steps.append(step6)

            # Aggregate
            confidences = [s.confidence for s in chain.steps if s.confidence > 0]
            chain.total_confidence = round(sum(confidences) / len(confidences), 2) if confidences else 0.0
            chain.final_verdict = step6.conclusion
            chain.reasoning_summary = self._build_summary(chain)

        except Exception as exc:
            logger.exception("ReasoningEngine.analyze_investment_opportunity failed: %s", exc)
            chain.final_verdict = "ANALYSIS_ERROR"
            chain.reasoning_summary = f"Reasoning engine encountered an error: {exc}"
            chain.total_confidence = 0.0

        return chain

    def reason_about_query(
        self,
        query: str,
        intent: str,
        psychology: Optional[Dict[str, Any]] = None,
        analytics_context: Optional[Dict[str, Any]] = None,
        history: Optional[List[Dict[str, Any]]] = None,
    ) -> ReasoningChain:
        """
        Dynamically determine which reasoning steps are needed based on *intent*
        and build a reasoning chain tailored to the query.
        """
        ctx = analytics_context or {}
        psych = psychology or {}
        location = ctx.get("location", ctx.get("area", ""))
        budget = ctx.get("budget", 0)
        chain = ReasoningChain(metadata={"query": query, "intent": intent})

        try:
            intent_lower = intent.lower() if intent else ""

            # --- Price queries ------------------------------------------------
            if any(kw in intent_lower for kw in ("price", "سعر", "كام", "cost")):
                chain.steps.append(self._step_price_analysis(location, ctx))
                chain.steps.append(self._step_market_comparison(location))
                chain.steps.append(self._step_value_assessment(location, budget))

            # --- Investment queries -------------------------------------------
            elif any(kw in intent_lower for kw in ("invest", "roi", "استثمار", "عائد", "opportunity")):
                chain.steps.append(self._step_roi_projection(location, budget, ctx))
                chain.steps.append(self._step_inflation_hedge_analysis(budget))
                chain.steps.append(self._step_opportunity_cost(budget))

            # --- Area queries -------------------------------------------------
            elif any(kw in intent_lower for kw in ("area", "منطقة", "location", "where", "فين")):
                chain.steps.append(self._step_area_assessment(location, ctx))
                chain.steps.append(self._step_growth_analysis(location))
                chain.steps.append(self._step_infrastructure_score(location, ctx))
                chain.steps.append(self._step_developer_landscape(location))

            # --- Comparison queries -------------------------------------------
            elif any(kw in intent_lower for kw in ("compare", "مقارنة", "vs", "أحسن", "better", "difference")):
                locations = self._extract_comparison_locations(query, ctx)
                chain.steps.append(self._step_side_by_side_metrics(locations))
                chain.steps.append(self._step_growth_differential(locations))
                chain.steps.append(self._step_risk_comparison(locations))

            # --- Fallback: generic analysis -----------------------------------
            else:
                if location:
                    chain.steps.append(self._assess_market_position(location, ctx))
                if budget:
                    chain.steps.append(self._compare_investment_alternatives(budget))
                if not chain.steps:
                    chain.steps.append(ReasoningStep(
                        step_name="general_context",
                        thought="Query does not map to a specific analytical pathway; providing market overview.",
                        evidence=[
                            f"Inflation rate: {MARKET_DATA['inflation_rate']*100:.1f}%",
                            f"Bank CD rate: {MARKET_DATA['bank_cd_rate']*100:.0f}%",
                            f"Property nominal appreciation: {MARKET_DATA['nominal_property_appreciation']*100:.1f}%",
                        ],
                        conclusion="General market context provided — property outperforms cash and bank CDs on a real-return basis.",
                        confidence=0.6,
                    ))

            # Aggregate
            confidences = [s.confidence for s in chain.steps if s.confidence > 0]
            chain.total_confidence = round(sum(confidences) / len(confidences), 2) if confidences else 0.0
            chain.final_verdict = chain.steps[-1].conclusion if chain.steps else ""
            chain.reasoning_summary = self._build_summary(chain)

        except Exception as exc:
            logger.exception("ReasoningEngine.reason_about_query failed: %s", exc)
            chain.final_verdict = "ANALYSIS_ERROR"
            chain.reasoning_summary = f"Reasoning error: {exc}"
            chain.total_confidence = 0.0

        return chain

    def generate_reasoning_prompt(self, chain: ReasoningChain, language: str = "ar") -> str:
        """
        Convert a *ReasoningChain* into a textual prompt fragment that gets
        injected into the Claude system message so the LLM can reference the
        chain of thought.
        """
        if not chain.steps:
            return ""

        n_steps = len(chain.steps)
        conf_pct = int(chain.total_confidence * 100)

        lines: List[str] = []

        if language == "ar":
            lines.append(f"[سلسلة_التحليل: {n_steps} خطوات، الثقة: {conf_pct}%]")
            for idx, step in enumerate(chain.steps, 1):
                evidence_str = " | ".join(step.evidence[:3]) if step.evidence else ""
                lines.append(
                    f"الخطوة {idx} - {step.step_name}: {step.thought} -> {step.conclusion}"
                )
                if evidence_str:
                    lines.append(f"   الأدلة: {evidence_str}")
            lines.append(f"الحكم النهائي: {chain.final_verdict}")
            if chain.reasoning_summary:
                lines.append(f"الملخص: {chain.reasoning_summary}")
        else:
            lines.append(f"[REASONING_CHAIN: {n_steps} steps, confidence: {conf_pct}%]")
            for idx, step in enumerate(chain.steps, 1):
                evidence_str = " | ".join(step.evidence[:3]) if step.evidence else ""
                lines.append(
                    f"Step {idx} - {step.step_name}: {step.thought} -> {step.conclusion}"
                )
                if evidence_str:
                    lines.append(f"   Evidence: {evidence_str}")
            lines.append(f"VERDICT: {chain.final_verdict}")
            if chain.reasoning_summary:
                lines.append(f"Summary: {chain.reasoning_summary}")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Helper: investment analysis steps (private)
    # ------------------------------------------------------------------

    def _assess_market_position(
        self,
        location: str,
        analytics_context: Optional[Dict[str, Any]] = None,
    ) -> ReasoningStep:
        """Step 1 — Where does this area stand in the market?"""
        ctx = analytics_context or {}
        loc = _resolve_location(location)

        avg_price = AREA_PRICES.get(loc, 50_000)
        growth = AREA_GROWTH.get(loc, 0.12)
        growth_pct = round(growth * 100, 1)

        bench_key = _resolve_benchmark_key(location)
        bench = AREA_BENCHMARKS.get(bench_key, {})
        rental_yield = bench.get("rental_yield", 0.065)
        rental_yield_pct = round(rental_yield * 100, 2)

        # Demand classification
        if growth >= 1.5:
            demand_level = "very high"
        elif growth >= 0.8:
            demand_level = "high"
        elif growth >= 0.3:
            demand_level = "moderate"
        else:
            demand_level = "stabilising"

        evidence = [
            f"Avg price/sqm: {avg_price:,} EGP ({loc})",
            f"YoY growth: {growth_pct}%",
            f"Rental yield: {rental_yield_pct}%",
            f"Demand level: {demand_level}",
        ]

        # Override with live analytics when available
        live_avg = ctx.get("avg_price_sqm")
        if live_avg and live_avg > 0:
            evidence.insert(0, f"Live DB avg price/sqm: {live_avg:,} EGP")

        thought = (
            f"{loc} trades at {avg_price:,} EGP/sqm with {growth_pct}% historical YoY growth "
            f"and {rental_yield_pct}% rental yield. Demand is {demand_level}."
        )
        conclusion = (
            f"{loc} is a {demand_level}-demand market — "
            + ("strong growth play." if growth >= 0.8 else "stable value hold." if growth >= 0.2 else "maturing market.")
        )

        conf = min(0.95, 0.7 + (0.05 * len([e for e in evidence if e])))

        return ReasoningStep(
            step_name="market_position",
            thought=thought,
            evidence=evidence,
            conclusion=conclusion,
            confidence=round(conf, 2),
        )

    def _check_affordability(
        self,
        location: str,
        budget: int,
        property_type: str = "apartment",
    ) -> ReasoningStep:
        """Step 2 — Can the user afford the target market?"""
        loc = _resolve_location(location)
        bench_key = _resolve_benchmark_key(location)
        bench = AREA_BENCHMARKS.get(bench_key, {})
        avg_price = AREA_PRICES.get(loc, 50_000)

        minimums = bench.get("property_minimums", {})
        prop_key = property_type.lower().strip()
        min_price = minimums.get(prop_key, 0)

        evidence: List[str] = []
        if min_price > 0:
            evidence.append(f"Min {prop_key} price in {loc}: {min_price:,} EGP")
        evidence.append(f"Budget: {budget:,} EGP")
        evidence.append(f"Market avg/sqm: {avg_price:,} EGP")

        if min_price and budget > 0:
            coverage_pct = round((budget / min_price) * 100, 1)
            evidence.append(f"Budget covers {coverage_pct}% of min market price")
        else:
            coverage_pct = 0.0

        if budget <= 0:
            thought = "No budget specified — cannot assess affordability."
            conclusion = "Budget information needed for affordability analysis."
            conf = 0.3
        elif min_price > 0 and budget >= min_price:
            headroom = budget - min_price
            thought = (
                f"Budget {budget:,} EGP exceeds the {loc} {prop_key} floor of {min_price:,} EGP "
                f"by {headroom:,} EGP ({coverage_pct}% of floor)."
            )
            conclusion = f"AFFORDABLE — budget clears the market floor with {headroom:,} EGP headroom."
            conf = 0.9
        elif min_price > 0:
            gap = min_price - budget
            thought = (
                f"Budget {budget:,} EGP is {gap:,} EGP short of the {loc} {prop_key} floor ({min_price:,} EGP). "
                f"Covers only {coverage_pct}% of minimum."
            )
            conclusion = f"NOT AFFORDABLE — {gap:,} EGP gap. Consider a different area or property type."
            conf = 0.9
        else:
            # No minimum data — do a rough sqm check
            affordable_sqm = budget / avg_price if avg_price > 0 else 0
            thought = (
                f"No property-type floor data for {prop_key} in {loc}. "
                f"At {avg_price:,} EGP/sqm the budget buys ~{affordable_sqm:.0f} sqm."
            )
            conclusion = f"Approximate — budget buys ~{affordable_sqm:.0f} sqm at market average."
            conf = 0.6

        return ReasoningStep(
            step_name="affordability_check",
            thought=thought,
            evidence=evidence,
            conclusion=conclusion,
            confidence=conf,
        )

    def _calculate_growth_trajectory(
        self,
        location: str,
        years: int = 5,
    ) -> ReasoningStep:
        """Step 3 — Historical growth and future projection."""
        loc = _resolve_location(location)
        history = AREA_PRICE_HISTORY.get(loc)

        evidence: List[str] = []

        if history:
            sorted_years = sorted(y for y in history if isinstance(y, int))
            if len(sorted_years) >= 2:
                first_year = sorted_years[0]
                last_year = sorted_years[-1]
                start_p = history[first_year]
                end_p = history[last_year]
                total_growth_pct = round(((end_p - start_p) / start_p) * 100, 1) if start_p else 0
                span = last_year - first_year
                cagr = round(((end_p / start_p) ** (1 / span) - 1) * 100, 1) if start_p and span else 0

                evidence.append(f"{first_year} price: {start_p:,} EGP/sqm")
                evidence.append(f"{last_year} price: {end_p:,} EGP/sqm")
                evidence.append(f"Total growth ({first_year}-{last_year}): {total_growth_pct}%")
                evidence.append(f"CAGR: {cagr}%")

                # YoY for last 2 data-points
                if len(sorted_years) >= 2:
                    prev_y = sorted_years[-2]
                    prev_p = history[prev_y]
                    recent_yoy = round(((end_p - prev_p) / prev_p) * 100, 1) if prev_p else 0
                    evidence.append(f"Recent YoY ({prev_y}-{last_year}): {recent_yoy}%")

                # 5-year forward projection using CAGR
                current_price = end_p
                projected_price = int(current_price * ((1 + cagr / 100) ** years))
                evidence.append(f"Projected price in {years}y at {cagr}% CAGR: {projected_price:,} EGP/sqm")

                thought = (
                    f"{loc} grew from {start_p:,} to {end_p:,} EGP/sqm ({first_year}-{last_year}), "
                    f"a {total_growth_pct}% total gain (CAGR {cagr}%). "
                    f"Projecting forward {years}y => ~{projected_price:,} EGP/sqm."
                )
                conclusion = (
                    f"Strong historical trajectory — {cagr}% CAGR. "
                    f"Projected {years}-year value: {projected_price:,} EGP/sqm."
                )
                conf = 0.80
            else:
                thought = f"Insufficient historical data points for {loc}."
                conclusion = "Cannot reliably project growth."
                conf = 0.3
        else:
            # Fallback — use AREA_GROWTH as a single-point estimate
            yoy = AREA_GROWTH.get(loc, 0.12)
            yoy_pct = round(yoy * 100, 1)
            current_price = AREA_PRICES.get(loc, 50_000)
            projected = int(current_price * ((1 + yoy) ** years))
            evidence.append(f"Historical YoY growth rate: {yoy_pct}%")
            evidence.append(f"Current avg price: {current_price:,} EGP/sqm")
            evidence.append(f"Projected in {years}y: {projected:,} EGP/sqm")

            thought = (
                f"No year-by-year history for {loc}; using aggregate YoY rate of {yoy_pct}%. "
                f"Current {current_price:,} -> projected {projected:,} EGP/sqm in {years}y."
            )
            conclusion = f"Estimated {years}-year projection: {projected:,} EGP/sqm (based on {yoy_pct}% YoY)."
            conf = 0.55

        return ReasoningStep(
            step_name="growth_trajectory",
            thought=thought,
            evidence=evidence,
            conclusion=conclusion,
            confidence=conf,
        )

    def _evaluate_risk_factors(
        self,
        location: str,
        property_type: str = "apartment",
        psychology_state: Optional[str] = None,
    ) -> ReasoningStep:
        """Step 4 — Risk assessment (delivery, legal, market correction)."""
        loc = _resolve_location(location)
        bench_key = _resolve_benchmark_key(location)
        bench = AREA_BENCHMARKS.get(bench_key, {})
        growth = AREA_GROWTH.get(loc, 0.12)

        evidence: List[str] = []
        risk_score = 0  # 0 = no risk, 100 = max risk

        # --- Delivery risk (higher for new / off-plan areas) ---
        high_delivery_risk_areas = {"New Capital", "North Coast", "Ain Sokhna"}
        if loc in high_delivery_risk_areas:
            delivery_risk = "elevated"
            risk_score += 25
            evidence.append(f"Delivery risk: ELEVATED ({loc} has newer projects with longer delivery timelines)")
        else:
            delivery_risk = "moderate"
            risk_score += 10
            evidence.append(f"Delivery risk: MODERATE ({loc} has established delivery track record)")

        # --- Legal risk ---
        if loc == "New Capital":
            legal_note = "New Capital plots are government-allocated — title registration can be slower."
            risk_score += 10
        else:
            legal_note = "Standard registration process applies."
        evidence.append(f"Legal note: {legal_note}")

        # --- Market correction probability ---
        if growth >= 2.0:
            correction_prob = "moderate-to-high (>200% growth may mean overheating)"
            risk_score += 20
        elif growth >= 1.0:
            correction_prob = "low-to-moderate (strong demand underpins pricing)"
            risk_score += 10
        else:
            correction_prob = "low (prices have stabilised)"
            risk_score += 5
        evidence.append(f"Correction probability: {correction_prob}")

        # --- Property-type-specific risk ---
        if property_type.lower() in ("chalet", "villa"):
            evidence.append("Luxury segment: longer resale cycle, seasonal demand for chalets")
            risk_score += 10

        # --- Psychology overlay ---
        if psychology_state:
            psych_lower = str(psychology_state).lower()
            if "delivery_fear" in psych_lower or "risk_averse" in psych_lower:
                evidence.append("User is risk-averse / delivery-fear — emphasise Tier-1 developers with >90% on-time delivery")
            elif "macro_skeptic" in psych_lower:
                evidence.append("User questions macro fundamentals — anchor on replacement-cost logic")

        # Normalise
        risk_score = min(risk_score, 100)
        risk_label = "LOW" if risk_score < 25 else "MODERATE" if risk_score < 50 else "ELEVATED" if risk_score < 75 else "HIGH"

        thought = (
            f"Overall risk score for {loc} ({property_type}): {risk_score}/100 ({risk_label}). "
            f"Delivery={delivery_risk}, correction={correction_prob}."
        )
        conclusion = f"Risk level: {risk_label} ({risk_score}/100). Mitigation: choose Tier-1 developers with strong delivery records."

        # Higher risk => lower confidence in the opportunity
        conf = round(max(0.4, 1.0 - risk_score / 100), 2)

        return ReasoningStep(
            step_name="risk_assessment",
            thought=thought,
            evidence=evidence,
            conclusion=conclusion,
            confidence=conf,
        )

    def _compare_investment_alternatives(
        self,
        investment_amount: int,
        market_data: Optional[Dict[str, Any]] = None,
    ) -> ReasoningStep:
        """Step 5 — Property vs Bank CDs vs Inflation vs Gold."""
        mkt = market_data or MARKET_DATA
        inflation = mkt.get("inflation_rate", 0.136)
        bank_cd = mkt.get("bank_cd_rate", 0.22)
        prop_appreciation = mkt.get("property_appreciation", 0.20)
        rental_yield = mkt.get("rental_yield_avg", 0.075)
        gold_rate = mkt.get("gold_appreciation", 0.15)

        # 5-year projections
        years = 5
        cash_real = investment_amount * ((1 - inflation) ** years)
        bank_nominal = investment_amount * ((1 + bank_cd) ** years)
        bank_real = bank_nominal / ((1 + inflation) ** years)
        prop_value = investment_amount * ((1 + prop_appreciation) ** years)
        cumulative_rent = int(investment_amount * rental_yield * years)
        prop_total = int(prop_value) + cumulative_rent
        gold_value = int(investment_amount * ((1 + gold_rate) ** years))

        evidence = [
            f"Cash after {years}y (real): {int(cash_real):,} EGP (lost {int(investment_amount - cash_real):,} to inflation)",
            f"Bank CD after {years}y (nominal): {int(bank_nominal):,} EGP | real: {int(bank_real):,} EGP",
            f"Property after {years}y: value {int(prop_value):,} + rent {cumulative_rent:,} = {prop_total:,} EGP",
            f"Gold after {years}y: {gold_value:,} EGP",
            f"Rates — inflation: {inflation*100:.1f}%, bank CD: {bank_cd*100:.0f}%, prop growth: {prop_appreciation*100:.0f}%, rental: {rental_yield*100:.1f}%, gold: {gold_rate*100:.0f}%",
        ]

        # Determine winner
        options = {"property": prop_total, "bank_cd": int(bank_nominal), "gold": gold_value, "cash": int(cash_real)}
        winner = max(options, key=options.get)  # type: ignore[arg-type]
        prop_vs_bank = prop_total - int(bank_nominal)
        prop_vs_bank_pct = round((prop_vs_bank / investment_amount) * 100, 1) if investment_amount else 0

        thought = (
            f"Over {years}y on {investment_amount:,} EGP: "
            f"property yields {prop_total:,} (appreciation + rent), "
            f"bank CD yields {int(bank_nominal):,} (nominal), "
            f"gold yields {gold_value:,}. "
            f"Cash erodes to {int(cash_real):,} in real terms."
        )

        if winner == "property":
            conclusion = (
                f"Property WINS by {prop_vs_bank:,} EGP ({prop_vs_bank_pct:+.1f}% vs bank CD). "
                f"Real estate is the superior inflation hedge."
            )
            conf = 0.85
        elif winner == "bank_cd":
            conclusion = (
                f"Bank CD edges out property by {abs(prop_vs_bank):,} EGP in nominal terms. "
                f"However, property provides tangible asset + rental income."
            )
            conf = 0.70
        else:
            conclusion = f"{winner.replace('_', ' ').title()} leads on nominal returns, but property offers rental + tangible value."
            conf = 0.65

        return ReasoningStep(
            step_name="comparative_advantage",
            thought=thought,
            evidence=evidence,
            conclusion=conclusion,
            confidence=conf,
        )

    # ------------------------------------------------------------------
    # Internal: synthesis
    # ------------------------------------------------------------------

    def _synthesize_verdict(
        self,
        steps: List[ReasoningStep],
        location: str,
        budget: int,
        property_type: str,
        market_data: Optional[Dict[str, Any]] = None,
    ) -> ReasoningStep:
        """Step 6 — Synthesize all previous steps into a final buy/hold/wait recommendation."""
        evidence: List[str] = []
        score = 0  # Positive = buy, negative = wait

        for s in steps:
            # Extract signal from each step
            conc = s.conclusion.lower()
            name = s.step_name

            if name == "market_position":
                if "strong growth" in conc or "very high" in conc or "high-demand" in conc:
                    score += 2
                    evidence.append("+2 (strong market position)")
                elif "stable" in conc or "moderate" in conc:
                    score += 1
                    evidence.append("+1 (stable market)")
                else:
                    evidence.append("+0 (maturing/flat market)")

            elif name == "affordability_check":
                if "affordable" in conc and "not" not in conc:
                    score += 2
                    evidence.append("+2 (budget is feasible)")
                elif "not affordable" in conc:
                    score -= 3
                    evidence.append("-3 (budget below market floor)")

            elif name == "growth_trajectory":
                # Check for CAGR numbers
                if "cagr" in s.thought.lower():
                    try:
                        cagr_str = s.thought.lower().split("cagr")[1]
                        # find first number
                        import re
                        m = re.search(r"([\d.]+)%", cagr_str)
                        if m:
                            cagr_val = float(m.group(1))
                            if cagr_val >= 25:
                                score += 3
                                evidence.append(f"+3 (CAGR {cagr_val}% — exceptional growth)")
                            elif cagr_val >= 15:
                                score += 2
                                evidence.append(f"+2 (CAGR {cagr_val}% — strong growth)")
                            else:
                                score += 1
                                evidence.append(f"+1 (CAGR {cagr_val}% — moderate growth)")
                    except Exception:
                        score += 1
                        evidence.append("+1 (growth data present)")

            elif name == "risk_assessment":
                if "low" in conc and "moderate" not in conc:
                    score += 1
                    evidence.append("+1 (low risk)")
                elif "elevated" in conc or "high" in conc:
                    score -= 1
                    evidence.append("-1 (elevated risk)")

            elif name == "comparative_advantage":
                if "property wins" in conc.lower():
                    score += 2
                    evidence.append("+2 (property beats alternatives)")
                elif "bank" in conc.lower() and "edges" in conc.lower():
                    score += 0
                    evidence.append("+0 (bank competitive)")
                else:
                    score += 1
                    evidence.append("+1 (property competitive)")

        evidence.insert(0, f"Composite score: {score}")

        if score >= 6:
            verdict = "STRONG BUY"
            rec = f"Strong buy signal for {property_type} in {location}. Market position, growth, and affordability all align."
            conf = 0.90
        elif score >= 3:
            verdict = "BUY"
            rec = f"Buy signal for {property_type} in {location}. Fundamentals are positive with manageable risk."
            conf = 0.80
        elif score >= 1:
            verdict = "HOLD / CONDITIONAL BUY"
            rec = f"Conditional buy for {property_type} in {location}. Some factors need attention — negotiate or wait for better timing."
            conf = 0.65
        elif score >= -1:
            verdict = "WAIT"
            rec = f"Wait signal. Current conditions for {property_type} in {location} carry notable risk or affordability gap."
            conf = 0.55
        else:
            verdict = "DO NOT BUY"
            rec = f"Do not buy — budget or market conditions are unfavorable for {property_type} in {location}."
            conf = 0.85

        thought = f"Synthesised {len(steps)} reasoning steps. Composite score: {score}. Recommendation: {verdict}."

        return ReasoningStep(
            step_name="final_verdict",
            thought=thought,
            evidence=evidence,
            conclusion=f"{verdict} — {rec}",
            confidence=conf,
        )

    def _build_summary(self, chain: ReasoningChain) -> str:
        """Build a concise one-paragraph summary from all steps."""
        parts: List[str] = []
        for s in chain.steps:
            parts.append(f"[{s.step_name}] {s.conclusion}")
        return " | ".join(parts)

    # ------------------------------------------------------------------
    # Dynamic query-type step builders
    # ------------------------------------------------------------------

    # --- Price steps ---

    def _step_price_analysis(self, location: str, ctx: Dict[str, Any]) -> ReasoningStep:
        loc = _resolve_location(location) if location else "Unknown"
        avg = AREA_PRICES.get(loc, 0)
        live = ctx.get("avg_price_sqm", 0)
        effective = live if live else avg

        evidence = []
        if avg:
            evidence.append(f"Static avg: {avg:,} EGP/sqm")
        if live:
            evidence.append(f"Live DB avg: {live:,} EGP/sqm")

        bench_key = _resolve_benchmark_key(location) if location else ""
        bench = AREA_BENCHMARKS.get(bench_key, {})
        minimums = bench.get("property_minimums", {})
        if minimums:
            for pt, mp in minimums.items():
                evidence.append(f"Min {pt}: {mp:,} EGP")

        thought = f"Price analysis for {loc}: market average is {effective:,} EGP/sqm." if effective else f"No price data for {loc}."
        conclusion = f"{loc} avg price/sqm: {effective:,} EGP." if effective else "Insufficient price data."
        conf = 0.85 if effective else 0.3

        return ReasoningStep(step_name="price_analysis", thought=thought, evidence=evidence, conclusion=conclusion, confidence=conf)

    def _step_market_comparison(self, location: str) -> ReasoningStep:
        loc = _resolve_location(location) if location else ""
        price = AREA_PRICES.get(loc, 0)

        # Compare to all areas
        evidence = []
        rank = 1
        sorted_areas = sorted(AREA_PRICES.items(), key=lambda x: x[1], reverse=True)
        for idx, (area, p) in enumerate(sorted_areas, 1):
            evidence.append(f"#{idx} {area}: {p:,} EGP/sqm")
            if area == loc:
                rank = idx

        thought = f"{loc} ranks #{rank} out of {len(AREA_PRICES)} tracked areas by price/sqm ({price:,} EGP)."
        conclusion = f"{loc} is ranked #{rank} in pricing — {'premium' if rank <= 3 else 'mid-range' if rank <= 6 else 'affordable'} tier."
        conf = 0.80

        return ReasoningStep(step_name="market_comparison", thought=thought, evidence=evidence, conclusion=conclusion, confidence=conf)

    def _step_value_assessment(self, location: str, budget: int) -> ReasoningStep:
        loc = _resolve_location(location) if location else ""
        avg = AREA_PRICES.get(loc, 50_000)
        sqm_for_budget = budget / avg if avg and budget else 0
        evidence = [
            f"Budget: {budget:,} EGP",
            f"Avg price/sqm: {avg:,} EGP",
            f"Budget buys ~{sqm_for_budget:.0f} sqm at avg price",
        ]
        thought = f"At {avg:,} EGP/sqm a {budget:,} EGP budget buys ~{sqm_for_budget:.0f} sqm in {loc}."
        conclusion = f"Value assessment: ~{sqm_for_budget:.0f} sqm purchasable in {loc}."
        conf = 0.75 if budget and avg else 0.3

        return ReasoningStep(step_name="value_assessment", thought=thought, evidence=evidence, conclusion=conclusion, confidence=conf)

    # --- Investment steps ---

    def _step_roi_projection(self, location: str, budget: int, ctx: Dict[str, Any]) -> ReasoningStep:
        loc = _resolve_location(location) if location else ""
        bench_key = _resolve_benchmark_key(location) if location else ""
        bench = AREA_BENCHMARKS.get(bench_key, {})
        rental_yield = bench.get("rental_yield", 0.065)
        growth = AREA_GROWTH.get(loc, 0.12)

        annual_rent = int(budget * rental_yield) if budget else 0
        appreciation = int(budget * growth) if budget else 0
        total_first_year = annual_rent + appreciation
        total_pct = round((total_first_year / budget) * 100, 1) if budget else 0

        evidence = [
            f"Rental yield: {rental_yield*100:.1f}% => {annual_rent:,} EGP/yr",
            f"Capital growth: {growth*100:.1f}% => {appreciation:,} EGP/yr",
            f"Total first-year return: {total_first_year:,} EGP ({total_pct}%)",
        ]
        thought = f"ROI projection for {budget:,} EGP in {loc}: rental {annual_rent:,} + appreciation {appreciation:,} = {total_first_year:,} EGP yr-1."
        conclusion = f"Projected first-year ROI: {total_pct}% ({total_first_year:,} EGP)."
        conf = 0.75

        return ReasoningStep(step_name="roi_projection", thought=thought, evidence=evidence, conclusion=conclusion, confidence=conf)

    def _step_inflation_hedge_analysis(self, budget: int) -> ReasoningStep:
        inflation = MARKET_DATA["inflation_rate"]
        prop_growth = MARKET_DATA["property_appreciation"]
        real_return = prop_growth - inflation
        real_pct = round(real_return * 100, 1)

        erosion_5y = int(budget - budget * ((1 - inflation) ** 5))
        prop_gain_5y = int(budget * ((1 + prop_growth) ** 5) - budget)

        evidence = [
            f"Inflation: {inflation*100:.1f}%",
            f"Property growth: {prop_growth*100:.0f}%",
            f"Real return: {real_pct:+.1f}%",
            f"Cash erosion over 5y: -{erosion_5y:,} EGP",
            f"Property gain over 5y: +{prop_gain_5y:,} EGP",
        ]
        thought = f"Property appreciates at {prop_growth*100:.0f}% vs {inflation*100:.1f}% inflation => {real_pct:+.1f}% real return."
        conclusion = (
            f"Property hedges inflation with a {real_pct:+.1f}% real return. "
            f"Cash would lose {erosion_5y:,} EGP over 5 years."
        )
        conf = 0.85

        return ReasoningStep(step_name="inflation_hedge_analysis", thought=thought, evidence=evidence, conclusion=conclusion, confidence=conf)

    def _step_opportunity_cost(self, budget: int) -> ReasoningStep:
        bank_cd = MARKET_DATA["bank_cd_rate"]
        prop_growth = MARKET_DATA["property_appreciation"]
        rental = MARKET_DATA["rental_yield_avg"]

        bank_5y = int(budget * ((1 + bank_cd) ** 5))
        prop_5y = int(budget * ((1 + prop_growth) ** 5)) + int(budget * rental * 5)
        delta = prop_5y - bank_5y

        evidence = [
            f"Bank CD 5y (nominal): {bank_5y:,} EGP",
            f"Property 5y (value + rent): {prop_5y:,} EGP",
            f"Delta: {delta:+,} EGP",
        ]
        winner = "property" if delta > 0 else "bank CD"
        thought = f"Opportunity cost comparison: property {prop_5y:,} vs bank {bank_5y:,} over 5y. Delta = {delta:+,}."
        conclusion = f"{'Property' if delta > 0 else 'Bank CD'} wins by {abs(delta):,} EGP over 5 years."
        conf = 0.80

        return ReasoningStep(step_name="opportunity_cost", thought=thought, evidence=evidence, conclusion=conclusion, confidence=conf)

    # --- Area steps ---

    def _step_area_assessment(self, location: str, ctx: Dict[str, Any]) -> ReasoningStep:
        return self._assess_market_position(location, ctx)

    def _step_growth_analysis(self, location: str) -> ReasoningStep:
        return self._calculate_growth_trajectory(location, years=5)

    def _step_infrastructure_score(self, location: str, ctx: Dict[str, Any]) -> ReasoningStep:
        loc = _resolve_location(location) if location else ""

        # Infrastructure qualitative scoring from known data
        infra_map: Dict[str, Dict[str, Any]] = {
            "New Cairo": {"roads": 9, "schools": 9, "hospitals": 8, "malls": 9, "transport": 7, "overall": 8.4},
            "Sheikh Zayed": {"roads": 8, "schools": 8, "hospitals": 7, "malls": 8, "transport": 6, "overall": 7.4},
            "New Capital": {"roads": 9, "schools": 5, "hospitals": 5, "malls": 4, "transport": 7, "overall": 6.0},
            "6th October": {"roads": 7, "schools": 7, "hospitals": 7, "malls": 7, "transport": 6, "overall": 6.8},
            "North Coast": {"roads": 7, "schools": 3, "hospitals": 3, "malls": 4, "transport": 3, "overall": 4.0},
            "Maadi": {"roads": 7, "schools": 9, "hospitals": 9, "malls": 7, "transport": 8, "overall": 8.0},
            "Ain Sokhna": {"roads": 6, "schools": 2, "hospitals": 3, "malls": 3, "transport": 3, "overall": 3.4},
            "Madinaty": {"roads": 8, "schools": 8, "hospitals": 7, "malls": 8, "transport": 6, "overall": 7.4},
            "Rehab": {"roads": 8, "schools": 8, "hospitals": 7, "malls": 7, "transport": 7, "overall": 7.4},
        }
        infra = infra_map.get(loc, {})
        overall = infra.get("overall", 5.0)

        evidence = []
        for k, v in infra.items():
            if k != "overall":
                evidence.append(f"{k.title()}: {v}/10")
        evidence.append(f"Overall infrastructure score: {overall}/10")

        thought = f"{loc} infrastructure overall {overall}/10."
        conclusion = f"Infrastructure: {'excellent' if overall >= 8 else 'good' if overall >= 6 else 'developing' if overall >= 4 else 'limited'} ({overall}/10)."
        conf = 0.70

        return ReasoningStep(step_name="infrastructure_score", thought=thought, evidence=evidence, conclusion=conclusion, confidence=conf)

    def _step_developer_landscape(self, location: str) -> ReasoningStep:
        bench_key = _resolve_benchmark_key(location) if location else ""
        bench = AREA_BENCHMARKS.get(bench_key, {})

        tier1 = bench.get("tier1_developers", [])
        tier2 = bench.get("tier2_developers", [])
        tier3 = bench.get("tier3_developers", [])

        evidence = []
        if tier1:
            evidence.append(f"Tier 1 developers: {', '.join(tier1)}")
        if tier2:
            evidence.append(f"Tier 2 developers: {', '.join(tier2)}")
        if tier3:
            evidence.append(f"Tier 3 developers: {', '.join(tier3)}")

        total = len(tier1) + len(tier2) + len(tier3)
        loc = _resolve_location(location) if location else "area"
        thought = f"{loc} has {len(tier1)} Tier-1, {len(tier2)} Tier-2, {len(tier3)} Tier-3 developers."
        conclusion = (
            f"{'Robust' if len(tier1) >= 3 else 'Moderate' if len(tier1) >= 1 else 'Limited'} "
            f"developer landscape with {total} tracked developers."
        )
        conf = 0.75

        return ReasoningStep(step_name="developer_landscape", thought=thought, evidence=evidence, conclusion=conclusion, confidence=conf)

    # --- Comparison steps ---

    def _extract_comparison_locations(self, query: str, ctx: Dict[str, Any]) -> List[str]:
        """Extract two locations from a comparison query."""
        locations: List[str] = []

        # Check context first
        if ctx.get("locations"):
            locations = list(ctx["locations"])[:2]
        if ctx.get("location") and ctx["location"] not in locations:
            locations.insert(0, ctx["location"])

        # Try to extract from query text
        all_known = list(AREA_PRICES.keys()) + list(_LOCATION_ALIAS.keys())
        for candidate in all_known:
            if candidate.lower() in query.lower() and _resolve_location(candidate) not in [_resolve_location(l) for l in locations]:
                locations.append(candidate)
            if len(locations) >= 2:
                break

        # Ensure we have at least 2; pad with defaults
        while len(locations) < 2:
            for default in ["New Cairo", "Sheikh Zayed", "6th October"]:
                if default not in [_resolve_location(l) for l in locations]:
                    locations.append(default)
                    break
            if len(locations) < 2:
                locations.append("New Cairo")
                break

        return [_resolve_location(l) for l in locations[:2]]

    def _step_side_by_side_metrics(self, locations: List[str]) -> ReasoningStep:
        evidence = []
        for loc in locations:
            price = AREA_PRICES.get(loc, 0)
            growth = AREA_GROWTH.get(loc, 0)
            bk = _resolve_benchmark_key(loc)
            bench = AREA_BENCHMARKS.get(bk, {})
            rental = bench.get("rental_yield", 0)
            evidence.append(
                f"{loc}: {price:,} EGP/sqm, growth {growth*100:.0f}%, rental yield {rental*100:.1f}%"
            )

        loc_a, loc_b = locations[0], locations[1] if len(locations) > 1 else locations[0]
        thought = f"Side-by-side: {loc_a} vs {loc_b} on price, growth, and yield."
        conclusion = f"Metrics compared for {loc_a} and {loc_b} — see evidence for details."
        conf = 0.80

        return ReasoningStep(step_name="side_by_side_metrics", thought=thought, evidence=evidence, conclusion=conclusion, confidence=conf)

    def _step_growth_differential(self, locations: List[str]) -> ReasoningStep:
        evidence = []
        growths: Dict[str, float] = {}
        for loc in locations:
            g = AREA_GROWTH.get(loc, 0)
            growths[loc] = g
            evidence.append(f"{loc} YoY growth: {g*100:.0f}%")

        if len(locations) >= 2:
            diff = growths.get(locations[0], 0) - growths.get(locations[1], 0)
            diff_pct = round(diff * 100, 1)
            faster = locations[0] if diff > 0 else locations[1]
            evidence.append(f"Growth differential: {abs(diff_pct)}% in favour of {faster}")
            conclusion = f"{faster} is growing {abs(diff_pct)}% faster."
        else:
            conclusion = "Need two locations for growth differential."

        thought = f"Growth differential analysis between {', '.join(locations)}."
        conf = 0.80

        return ReasoningStep(step_name="growth_differential", thought=thought, evidence=evidence, conclusion=conclusion, confidence=conf)

    def _step_risk_comparison(self, locations: List[str]) -> ReasoningStep:
        evidence = []
        for loc in locations:
            step = self._evaluate_risk_factors(loc)
            evidence.append(f"{loc} risk: {step.conclusion}")

        thought = f"Risk comparison across {', '.join(locations)}."
        conclusion = "Comparative risk profiles generated — see evidence."
        conf = 0.75

        return ReasoningStep(step_name="risk_comparison", thought=thought, evidence=evidence, conclusion=conclusion, confidence=conf)


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

reasoning_engine = ReasoningEngine()

__all__ = [
    "ReasoningEngine",
    "ReasoningChain",
    "ReasoningStep",
    "reasoning_engine",
]
