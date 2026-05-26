"""
negotiation_engine.py
=====================
Egyptian-market negotiation engine — converts a compound + property-type
query into a haggle range (buyer "fair value low/median/high") and the
lever breakdown that explains where the negotiation slack lives.

Built on top of:
* app.ai_engine.comparison_service.compare_compounds — for compound aggregates
* app.ai_engine.comparison_service.best_deals_in_compound — for bargain comps
* app.models.NegotiationConstant — for admin-editable multipliers
* app.models.Property — for raw resale population (percentile computation)

This module is the BACKEND of the buyer haggle product. It is pure
business logic + DB reads; no LLM calls, no HTTP. The pricing_router
wraps it for free + premium API surfaces.
"""
from __future__ import annotations

import logging
import statistics
from dataclasses import dataclass
from typing import Final, Literal, Optional, Tuple

from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_engine.comparison_service import (
    best_deals_in_compound,
    compare_compounds,
)
from app.models import NegotiationConstant, Property

_logger = logging.getLogger(__name__)

ConfidenceTier = Literal["high", "moderate", "indicative"]
ScopeType = Literal["global", "developer", "area", "compound"]

# Default spread when there aren't enough comps to compute real percentiles.
# Anchored at the median; ±8% range is a deliberate placeholder so the
# product can ship even when only 1-2 comps exist.
_FALLBACK_RANGE_SPREAD: Final[float] = 0.08


# ---------------------------------------------------------------------------
# Response schemas (LOCKED — pricing_router depends on this shape)
# ---------------------------------------------------------------------------


class FairRangeEGP(BaseModel):
    """Buyer-facing fair-value range in EGP."""
    low: float = Field(..., description="P25 of comp distribution after normalization")
    median: float
    high: float = Field(..., description="P75 of comp distribution after normalization")


class HaggleLever(BaseModel):
    """
    Single negotiation lever explaining where slack exists.

    Free tier sees only the leverage signal (high/low/none). Premium tier
    sees the full lever table with numeric ranges and per-lever rationale.
    """
    name: str
    label_en: str
    label_ar: str
    range_low_pct: float = Field(..., description="Low end of slack (e.g. 0.05 = 5%)")
    range_high_pct: float
    rationale_en: str
    rationale_ar: str


class HaggleComp(BaseModel):
    """A single comparable closing used to build the fair range."""
    compound: str
    property_type: str
    size_sqm: Optional[float] = None
    bedrooms: Optional[int] = None
    floor: Optional[str] = None
    closing_month: str = Field(..., description="YYYY-MM")
    closing_price_egp: Optional[float] = Field(
        None,
        description=(
            "Closing price. None when masked (free tier shows everything "
            "EXCEPT this field for the single visible comp)."
        ),
    )
    source: str = Field(..., description="nawy | aqarmap | manual | admin")
    masked: bool = Field(
        False, description="True if closing_price_egp is intentionally hidden."
    )


class HaggleRange(BaseModel):
    """Top-level result of compute_haggle_range(). Locked v1 shape."""
    compound: str
    property_type: str
    size_sqm: float
    bedrooms: int

    fair_range_egp: FairRangeEGP
    confidence_tier: ConfidenceTier
    comps_used: int = Field(..., description="Number of closings in the fair-range computation")
    data_as_of: Optional[str] = Field(
        None, description="ISO date of most recent scrape contributing to this answer."
    )

    # Verdict against an optional listing price the user supplied
    listing_price_egp: Optional[float] = None
    pct_vs_market: Optional[float] = Field(
        None,
        description=(
            "If listing_price_egp supplied, signed pct delta vs median fair value. "
            "Positive = above market; negative = below."
        ),
    )
    leverage_signal: Literal["high", "moderate", "low", "none"] = "none"

    # The lever breakdown (full set; pricing_router masks for free tier)
    levers: list[HaggleLever] = Field(default_factory=list)
    comps: list[HaggleComp] = Field(
        default_factory=list,
        description="Full comp table — pricing_router truncates to 1 masked for free tier.",
    )

    # Trace fields — useful for verifier + admin audit
    constants_resolved: dict[str, float] = Field(default_factory=dict)
    notes: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Constant resolution
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ResolvedConstant:
    """A negotiation constant after scope resolution."""
    key: str
    value_min: float
    value_max: float
    unit: str
    scope_type: ScopeType
    scope_id: Optional[str]


# Precedence order: most specific wins. compound > area > developer > global.
_SCOPE_PRECEDENCE: Final[tuple[str, ...]] = (
    "compound",
    "area",
    "developer",
    "global",
)


async def resolve_constant(
    db: AsyncSession,
    constant_key: str,
    *,
    compound_id: Optional[str] = None,
    area_id: Optional[str] = None,
    developer_id: Optional[str] = None,
) -> Optional[ResolvedConstant]:
    """
    Resolve a single negotiation constant using compound > area > developer > global.

    Returns None if no row matches (caller should treat as "lever disabled").
    """
    scope_lookups: list[tuple[str, Optional[str]]] = [
        ("compound", compound_id),
        ("area", area_id),
        ("developer", developer_id),
        ("global", None),
    ]
    for scope_type, scope_id in scope_lookups:
        if scope_type != "global" and not scope_id:
            continue
        stmt = select(NegotiationConstant).where(
            NegotiationConstant.constant_key == constant_key,
            NegotiationConstant.scope_type == scope_type,
        )
        if scope_id is None:
            stmt = stmt.where(NegotiationConstant.scope_id.is_(None))
        else:
            stmt = stmt.where(NegotiationConstant.scope_id == scope_id)
        row = await db.scalar(stmt)
        if row is not None:
            return ResolvedConstant(
                key=row.constant_key,
                value_min=float(row.value_min),
                value_max=float(row.value_max),
                unit=row.unit,
                scope_type=scope_type,  # type: ignore[arg-type]
                scope_id=scope_id,
            )
    return None


# ---------------------------------------------------------------------------
# Percentile helper — pulls raw resale population for percentile computation
# ---------------------------------------------------------------------------


async def _fetch_resale_distribution(
    db: AsyncSession,
    compound: str,
    property_type: str,
) -> list[float]:
    """
    Pull the full resale-price population for a compound+type.

    Used to compute P25/P50/P75 for the fair range. compare_compounds only
    returns averages — for an honest range we need the distribution.
    """
    stmt = (
        select(Property.resale_price)
        .where(Property.compound == compound)
        .where(func.lower(Property.type) == property_type.lower())
        .where(Property.resale_price.is_not(None))
        .where(Property.is_available == True)  # noqa: E712
    )
    rows = (await db.execute(stmt)).all()
    return [float(r[0]) for r in rows if r[0] is not None and float(r[0]) > 0]


async def _fetch_all_comps(
    db: AsyncSession,
    compound: str,
    property_type: str,
    limit: int = 25,
) -> list[Property]:
    """
    Pull the full comp population (resale listings) for the comps array.

    Distinct from best_deals_in_compound which filters to bargains only.
    We want every comp visible to premium users — they decide what's
    relevant. Cap at `limit` to keep the response bounded.
    """
    stmt = (
        select(Property)
        .where(Property.compound == compound)
        .where(func.lower(Property.type) == property_type.lower())
        .where(Property.resale_price.is_not(None))
        .where(Property.is_available == True)  # noqa: E712
        .order_by(Property.scraped_at.desc())
        .limit(limit)
    )
    return list((await db.execute(stmt)).scalars().all())


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


async def compute_haggle_range(
    db: AsyncSession,
    *,
    compound: str,
    property_type: str,
    size_sqm: float,
    bedrooms: int,
    listing_price_egp: Optional[float] = None,
    developer_id: Optional[str] = None,
    area_id: Optional[str] = None,
) -> HaggleRange:
    """
    Compute the buyer's fair-value range + lever breakdown for a compound.

    Returns a HaggleRange with the LOCKED v1 schema. pricing_router decides
    how much of it to expose to free vs. premium callers — this function
    always returns the full picture.
    """
    notes: list[str] = []

    # ── Step 1: Compound aggregates from comparison_service ─────────────
    compare_result = await compare_compounds(
        [compound], db, property_types=(property_type.lower(),)
    )
    missing = compare_result.get("missing_compound")
    per_compound = compare_result.get("per_compound", [])
    aggregate = per_compound[0] if per_compound else {}
    type_bucket: Optional[dict] = aggregate.get(property_type.lower())
    data_as_of: Optional[str] = aggregate.get("data_as_of")

    # ── Step 2: Pull the raw resale distribution for percentile range ──
    distribution = await _fetch_resale_distribution(db, compound, property_type)
    fair_range, confidence_tier, comps_used = _build_fair_range(
        distribution=distribution,
        type_bucket=type_bucket,
        compound=compound,
        notes=notes,
    )

    # ── Step 3: Apply confidence haircut to narrow the range when sparse ─
    haircut = await resolve_constant(db, "confidence_haircut_pct",
                                     compound_id=compound,
                                     area_id=area_id,
                                     developer_id=developer_id)
    if haircut and confidence_tier != "high":
        steps = {"moderate": 1, "indicative": 2}.get(confidence_tier, 0)
        if steps:
            adjustment = haircut.value_min * steps
            fair_range = _apply_haircut(fair_range, adjustment)
            notes.append(
                f"Confidence haircut applied: {confidence_tier} tier, "
                f"range narrowed by {adjustment * 100:.1f}%."
            )

    # ── Step 4: Verdict vs supplied listing price ───────────────────────
    pct_vs_market: Optional[float] = None
    leverage_signal: Literal["high", "moderate", "low", "none"] = "none"
    if listing_price_egp is not None and listing_price_egp > 0 and fair_range.median > 0:
        pct_vs_market = (listing_price_egp - fair_range.median) / fair_range.median
        leverage_signal = _classify_leverage(pct_vs_market)

    # ── Step 5: Lever breakdown ─────────────────────────────────────────
    levers, constants_resolved = await _build_levers(
        db,
        compound=compound,
        area_id=area_id,
        developer_id=developer_id,
        has_resale_market=bool(distribution),
    )

    # ── Step 6: Comps (full list — router truncates for free) ───────────
    raw_comps = await _fetch_all_comps(db, compound, property_type, limit=25)
    comps = [_property_to_comp(p) for p in raw_comps]

    if missing == compound:
        notes.append(
            f"No resale comps for {compound}. Fair range is a placeholder; "
            "improve confidence by waiting for more scrapes or comparing a peer compound."
        )

    return HaggleRange(
        compound=compound,
        property_type=property_type,
        size_sqm=size_sqm,
        bedrooms=bedrooms,
        fair_range_egp=fair_range,
        confidence_tier=confidence_tier,
        comps_used=comps_used,
        data_as_of=data_as_of,
        listing_price_egp=listing_price_egp,
        pct_vs_market=pct_vs_market,
        leverage_signal=leverage_signal,
        levers=levers,
        comps=comps,
        constants_resolved=constants_resolved,
        notes=notes,
    )


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------


def _build_fair_range(
    *,
    distribution: list[float],
    type_bucket: Optional[dict],
    compound: str,
    notes: list[str],
) -> tuple[FairRangeEGP, ConfidenceTier, int]:
    """
    Build the fair-value range from the raw resale distribution.

    Strategy:
      - Population ≥ 4: use real P25/P50/P75 (statistics.quantiles, n=4)
      - Population 1-3: anchor at median; spread = _FALLBACK_RANGE_SPREAD
      - Population 0 + dev_avg available: anchor at dev_avg, spread, note it
      - Otherwise: placeholder; caller surfaces "insufficient data"
    """
    pop_size = len(distribution)
    confidence_tier: ConfidenceTier = "indicative"

    if pop_size >= 10:
        confidence_tier = "high"
    elif pop_size >= 3:
        confidence_tier = "moderate"

    if pop_size >= 4:
        sorted_prices = sorted(distribution)
        quartiles = statistics.quantiles(sorted_prices, n=4, method="inclusive")
        # quartiles[0] = P25, quartiles[1] = P50, quartiles[2] = P75
        fair_range = FairRangeEGP(
            low=round(quartiles[0], 2),
            median=round(quartiles[1], 2),
            high=round(quartiles[2], 2),
        )
        return fair_range, confidence_tier, pop_size

    if 1 <= pop_size <= 3:
        median = statistics.median(distribution)
        fair_range = FairRangeEGP(
            low=round(median * (1 - _FALLBACK_RANGE_SPREAD), 2),
            median=round(median, 2),
            high=round(median * (1 + _FALLBACK_RANGE_SPREAD), 2),
        )
        notes.append(
            f"Only {pop_size} resale comp(s) — fair range derived from median with ±"
            f"{_FALLBACK_RANGE_SPREAD * 100:.0f}% spread (not true percentile)."
        )
        return fair_range, confidence_tier, pop_size

    # pop_size == 0: fall back to dev_avg if available
    if type_bucket and type_bucket.get("dev_avg"):
        dev_avg = float(type_bucket["dev_avg"])
        fair_range = FairRangeEGP(
            low=round(dev_avg * (1 - _FALLBACK_RANGE_SPREAD), 2),
            median=round(dev_avg, 2),
            high=round(dev_avg * (1 + _FALLBACK_RANGE_SPREAD), 2),
        )
        notes.append(
            f"No resale comps in {compound}; fair range derived from developer "
            "price average. Treat as indicative until resale market develops."
        )
        return fair_range, "indicative", 0

    # Final fallback — no data at all
    notes.append(
        f"No comp data for {compound}. Cannot compute a fair range. "
        "Suggest comparing a peer compound or waiting for more scrapes."
    )
    return (
        FairRangeEGP(low=0.0, median=0.0, high=0.0),
        "indicative",
        0,
    )


def _apply_haircut(fair_range: FairRangeEGP, pct: float) -> FairRangeEGP:
    """
    Narrow the range symmetrically around the median by `pct`.

    Used when confidence is low — wider ranges feel unhelpful, narrower ones
    force the seller's hand. We narrow by reducing both tails.
    """
    median = fair_range.median
    new_low = median - (median - fair_range.low) * (1 - pct)
    new_high = median + (fair_range.high - median) * (1 - pct)
    return FairRangeEGP(
        low=round(new_low, 2),
        median=median,
        high=round(new_high, 2),
    )


def _classify_leverage(pct_vs_market: float) -> Literal["high", "moderate", "low", "none"]:
    """Map signed delta-vs-market into a buyer leverage signal."""
    if pct_vs_market >= 0.10:
        return "high"
    if pct_vs_market >= 0.04:
        return "moderate"
    if pct_vs_market >= -0.02:
        return "low"
    return "none"


async def _build_levers(
    db: AsyncSession,
    *,
    compound: str,
    area_id: Optional[str],
    developer_id: Optional[str],
    has_resale_market: bool,
) -> tuple[list[HaggleLever], dict[str, float]]:
    """
    Resolve negotiation constants from DB and build the lever objects.

    Returns (levers, constants_resolved_trace).
    """
    levers: list[HaggleLever] = []
    trace: dict[str, float] = {}

    async def _r(key: str) -> Optional[ResolvedConstant]:
        return await resolve_constant(
            db, key,
            compound_id=compound,
            area_id=area_id,
            developer_id=developer_id,
        )

    cash_discount = await _r("cash_discount_pct")
    if cash_discount:
        levers.append(HaggleLever(
            name="cash_discount_pct",
            label_en="Cash discount",
            label_ar="خصم الكاش",
            range_low_pct=cash_discount.value_min,
            range_high_pct=cash_discount.value_max,
            rationale_en=(
                "Settle in cash to capture the discount the seller would "
                "otherwise embed into the payment plan."
            ),
            rationale_ar=(
                "ادفع كاش لتأخذ الخصم الذي يخسره البائع في فارق التقسيط."
            ),
        ))
        trace["cash_discount_pct"] = (cash_discount.value_min + cash_discount.value_max) / 2

    # Resale broker commission applies only when there IS a resale market.
    # Otherwise primary-market commission (typically 0).
    broker_key = (
        "broker_commission_pct_resale" if has_resale_market
        else "broker_commission_pct_primary"
    )
    broker = await _r(broker_key)
    if broker and broker.value_max > 0:
        levers.append(HaggleLever(
            name=broker_key,
            label_en="Broker commission",
            label_ar="عمولة السمسار",
            range_low_pct=broker.value_min,
            range_high_pct=broker.value_max,
            rationale_en=(
                "Ask the seller to absorb the broker commission. It's standard "
                "to negotiate this on resale deals."
            ),
            rationale_ar=(
                "اطلب من البائع تحمل عمولة السمسار. ده طبيعي في صفقات إعادة البيع."
            ),
        ))
        trace[broker_key] = (broker.value_min + broker.value_max) / 2

    off_plan = await _r("off_plan_discount_per_year")
    if off_plan and off_plan.value_max > 0:
        levers.append(HaggleLever(
            name="off_plan_discount_per_year",
            label_en="Delivery-lag discount",
            label_ar="خصم تأخير التسليم",
            range_low_pct=off_plan.value_min,
            range_high_pct=off_plan.value_max,
            rationale_en=(
                "Off-plan units carry construction risk. Discount applied per "
                "year of delivery wait."
            ),
            rationale_ar=(
                "الوحدات قبل التسليم بتحمل مخاطر إنشاء. الخصم يطبق عن كل سنة "
                "انتظار للتسليم."
            ),
        ))
        trace["off_plan_discount_per_year"] = (off_plan.value_min + off_plan.value_max) / 2

    scarcity = await _r("scarcity_premium_pct")
    if scarcity:
        trace["scarcity_premium_pct"] = (scarcity.value_min + scarcity.value_max) / 2
        # Scarcity is a lever AGAINST the buyer when inventory is low. We
        # surface it in the trace but don't add it to the lever list (it's
        # not buyer slack, it's seller leverage).

    return levers, trace


def _property_to_comp(p: Property) -> HaggleComp:
    """Convert a Property ORM row to a HaggleComp (no masking; router decides)."""
    scraped_at = getattr(p, "scraped_at", None)
    closing_month = (
        scraped_at.strftime("%Y-%m")
        if scraped_at is not None
        else "unknown"
    )
    source = "nawy" if getattr(p, "nawy_url", None) else "manual"
    return HaggleComp(
        compound=p.compound or "",
        property_type=(p.type or "").lower(),
        size_sqm=float(p.size_sqm) if p.size_sqm else None,
        bedrooms=p.bedrooms,
        floor=getattr(p, "floor", None),
        closing_month=closing_month,
        closing_price_egp=float(p.resale_price) if p.resale_price else None,
        source=source,
        masked=False,
    )
