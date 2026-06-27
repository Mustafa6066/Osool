"""
Comparison engine for the free-path funnel.

Two modes:

- `compare_compounds` — 2 or 3 compounds. For each compound × property type
    computes avg developer price and avg resale price, gap = dev_avg − res_avg.
    Winner is the compound with the largest positive gap across its types.

- `best_deals_in_compound` — single compound. Ranks individual resale listings
  by how far below the compound's developer-price average they are. Returns
  the top K (default 3).

Both functions normalize property type to lowercase ("apartment", "villa")
because the `properties.type` column historically stores mixed casing.
"""
from typing import Any, Optional, Tuple

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Property


# Minimum dev-price samples in single-compound mode to compute a benchmark.
_MIN_SINGLE_DEV_SAMPLE_SIZE = 3

# Tiers: indicative = any data (1+), moderate = 3–9, high = 10+.
_TIER_MODERATE = 3
_TIER_HIGH = 10

# R7: data freshness CAPS confidence regardless of sample count — a thick sample
# scraped months ago is not "high confidence" for a price comparison a buyer acts on.
_FRESH_DAYS_FOR_HIGH = 60        # data older than this can't be "high"
_STALE_DAYS_TO_INDICATIVE = 180  # data older than this is only "indicative"


# Sentinel: caller supplied NO freshness info (count-only). Distinct from a
# supplied None (a DB row with NULL scraped_at, whose age is genuinely unknown).
_FRESHNESS_UNKNOWN = object()


def _confidence_tier(dev_n: int, res_n: int, latest_scraped: Any = _FRESHNESS_UNKNOWN) -> str:
    """
    Data confidence from the smaller of the two sample counts, then CAPPED by how
    fresh the data is (R7): the gap was computed but never used, so 15+15 samples
    scraped 8 months ago were labeled "high".
    """
    min_n = min(dev_n, res_n)
    if min_n >= _TIER_HIGH:
        base = "high"
    elif min_n >= _TIER_MODERATE:
        base = "moderate"
    else:
        base = "indicative"

    # Caller gave no freshness (count-only callers) — keep count-based.
    if latest_scraped is _FRESHNESS_UNKNOWN:
        return base
    # Freshness supplied but NULL (legacy rows with no scraped_at): age is unknown,
    # so don't certify "high" on count alone. [R7 review]
    if latest_scraped is None:
        return "moderate" if base == "high" else base

    from datetime import datetime, timezone

    ts = latest_scraped
    if getattr(ts, "tzinfo", None) is None:
        ts = ts.replace(tzinfo=timezone.utc)
    age_days = (datetime.now(timezone.utc) - ts).days
    if age_days > _STALE_DAYS_TO_INDICATIVE:
        return "indicative"
    if age_days > _FRESH_DAYS_FOR_HIGH and base == "high":
        return "moderate"
    return base


def _type_filter_clause(property_types: Tuple[str, ...]):
    """
    Build a case-insensitive type filter. The DB stores values like "Apartment",
    "Villa" — we accept lowercase canonical from the caller.
    """
    lowered = [t.lower() for t in property_types]
    return func.lower(Property.type).in_(lowered)


async def similar_compounds(
    compound_name: str,
    db: AsyncSession,
    limit: int = 3,
) -> list[str]:
    """
    Return up to `limit` compounds that share the same developer as
    `compound_name` and have resale data. Used for MISSING_DATA recovery chips.
    Falls back to any compounds with resale data if no developer match found.
    """
    # Find the developer of the compound in question.
    dev_stmt = (
        select(Property.developer)
        .where(Property.compound == compound_name)
        .where(Property.developer.is_not(None))
        .limit(1)
    )
    dev_result = (await db.execute(dev_stmt)).scalar_one_or_none()

    if dev_result:
        stmt = (
            select(Property.compound, func.count(Property.resale_price).label("res_n"))
            .where(Property.developer == dev_result)
            .where(Property.compound != compound_name)
            .where(Property.resale_price.is_not(None))
            .where(Property.is_available == True)  # noqa: E712
            .group_by(Property.compound)
            .having(func.count(Property.resale_price) > 0)
            .order_by(func.count(Property.resale_price).desc())
            .limit(limit)
        )
    else:
        stmt = (
            select(Property.compound, func.count(Property.resale_price).label("res_n"))
            .where(Property.compound != compound_name)
            .where(Property.resale_price.is_not(None))
            .where(Property.is_available == True)  # noqa: E712
            .group_by(Property.compound)
            .having(func.count(Property.resale_price) > 0)
            .order_by(func.count(Property.resale_price).desc())
            .limit(limit)
        )

    rows = (await db.execute(stmt)).all()
    return [r.compound for r in rows]


async def compare_compounds(
    compound_names: list[str],
    db: AsyncSession,
    property_types: Tuple[str, ...] = ("apartment", "villa"),
) -> dict[str, Any]:
    """
    Aggregate dev/resale prices for 2-3 named compounds and pick a winner.

    Returns a dict with shape:
        {
          "per_compound": [
            {"compound": str,
             "apartment": {dev_avg, res_avg, gap_egp, dev_n, res_n, confidence} | None,
             "villa":     {...} | None,
             "max_gap_egp": float | None,
             "data_as_of": str | None},    # ISO date of most recent scraped_at
            ...
          ],
          "winner": str | None,
          "missing_compound": str | None,  # only when a compound has zero resale rows
        }

    Segments with at least _MIN_SINGLE_DEV_SAMPLE_SIZE dev samples AND 1 resale
    sample are included; low-sample dev buckets are dropped (set to None).
    confidence field ("indicative" | "moderate" | "high") labels the remaining
    buckets. Only compounds with zero resale rows trigger missing_compound
    (the dialog asks the user to swap that compound).
    """
    if not compound_names:
        return {"per_compound": [], "winner": None, "missing_compound": None}

    stmt = (
        select(
            Property.compound,
            func.lower(Property.type).label("ptype"),
            func.avg(Property.developer_price).label("dev_avg"),
            func.count(Property.developer_price).label("dev_n"),
            func.avg(Property.resale_price).label("res_avg"),
            func.count(Property.resale_price).label("res_n"),
            func.max(Property.scraped_at).label("latest_scraped"),
        )
        .where(Property.compound.in_(compound_names))
        .where(_type_filter_clause(property_types))
        .where(Property.is_available == True)  # noqa: E712
        .group_by(Property.compound, func.lower(Property.type))
    )
    rows = (await db.execute(stmt)).all()

    # Build lookup keyed by (compound, ptype).
    bucket: dict[tuple[str, str], dict[str, Any]] = {}
    for r in rows:
        bucket[(r.compound, r.ptype)] = {
            "dev_avg": float(r.dev_avg) if r.dev_avg is not None else None,
            "dev_n": int(r.dev_n or 0),
            "res_avg": float(r.res_avg) if r.res_avg is not None else None,
            "res_n": int(r.res_n or 0),
            "latest_scraped": r.latest_scraped,
        }

    per_compound: list[dict[str, Any]] = []
    missing_compound: Optional[str] = None

    for name in compound_names:
        entry: dict[str, Any] = {"compound": name}
        max_gap: Optional[float] = None
        max_gap_pct: Optional[float] = None  # R8: rank by % discount, not absolute EGP
        any_resale_present = False
        latest_scraped_for_compound = None

        for ptype in property_types:
            data = bucket.get((name, ptype.lower()))
            segment: Optional[dict[str, Any]] = None

            if data and data["dev_n"] >= _MIN_SINGLE_DEV_SAMPLE_SIZE and data["res_n"] > 0 and data["dev_avg"] is not None and data["res_avg"] is not None:
                gap = data["dev_avg"] - data["res_avg"]
                # R8: rank by PERCENTAGE gap, not absolute EGP. Absolute gap scales
                # with price, so an expensive compound with a SMALLER % discount would
                # wrongly win; % also makes comparing across types (villa vs apartment)
                # fair instead of letting a high-priced villa's EGP gap dominate.
                gap_pct = (gap / data["dev_avg"]) if data["dev_avg"] else 0.0
                tier = _confidence_tier(data["dev_n"], data["res_n"], data.get("latest_scraped"))
                segment = {
                    "dev_avg": data["dev_avg"],
                    "res_avg": data["res_avg"],
                    "gap_egp": gap,
                    "gap_pct": gap_pct,
                    "dev_n": data["dev_n"],
                    "res_n": data["res_n"],
                    "confidence": tier,
                }
                if gap > 0 and (max_gap_pct is None or gap_pct > max_gap_pct):
                    max_gap_pct = gap_pct
                    max_gap = gap  # absolute gap at the best-% segment, for display

            if data and data["res_n"] > 0:
                any_resale_present = True
                ts = data.get("latest_scraped")
                if ts and (latest_scraped_for_compound is None or ts > latest_scraped_for_compound):
                    latest_scraped_for_compound = ts

            entry[ptype] = segment

        entry["max_gap_egp"] = max_gap
        entry["max_gap_pct"] = max_gap_pct
        entry["data_as_of"] = (
            latest_scraped_for_compound.date().isoformat()
            if latest_scraped_for_compound is not None
            else None
        )
        per_compound.append(entry)

        if not any_resale_present and missing_compound is None:
            missing_compound = name

    if missing_compound:
        return {
            "per_compound": per_compound,
            "winner": None,
            "missing_compound": missing_compound,
        }

    # Pick the winner by largest % discount (R8), not largest absolute EGP gap.
    rankable = [c for c in per_compound if c.get("max_gap_pct") is not None and c["max_gap_pct"] > 0]
    rankable.sort(key=lambda c: c["max_gap_pct"], reverse=True)
    winner = rankable[0]["compound"] if rankable else None

    return {
        "per_compound": per_compound,
        "winner": winner,
        "missing_compound": None,
    }


async def best_deals_in_compound(
    compound_name: str,
    db: AsyncSession,
    property_types: Tuple[str, ...] = ("apartment", "villa"),
    top_k: int = 3,
) -> dict[str, Any]:
    """
    Return the top-K resale listings in `compound_name` ranked by the gap
    between the compound's per-type developer-price average and the listing's
    actual resale_price.

    Result shape:
        {
          "compound": str,
          "dev_avg_by_type": {"apartment": float, "villa": float, ...},
          "top_listings": [
            {"property_id", "type", "size_sqm", "resale_price",
             "dev_avg", "gap_egp", "nawy_url", "title"},
            ...
          ],
          "missing": False | "no_resale_listings" | "no_dev_benchmark",
        }
    """
    # 1) Per-type developer-price averages for this compound.
    dev_stmt = (
        select(
            func.lower(Property.type).label("ptype"),
            func.avg(Property.developer_price).label("dev_avg"),
            func.count(Property.developer_price).label("dev_n"),
        )
        .where(Property.compound == compound_name)
        .where(_type_filter_clause(property_types))
        .where(Property.is_available == True)  # noqa: E712
        .group_by(func.lower(Property.type))
    )
    dev_rows = (await db.execute(dev_stmt)).all()
    dev_avg_by_type: dict[str, float] = {}
    for r in dev_rows:
        if r.dev_avg is not None and (r.dev_n or 0) >= _MIN_SINGLE_DEV_SAMPLE_SIZE:
            dev_avg_by_type[r.ptype] = float(r.dev_avg)

    if not dev_avg_by_type:
        return {
            "compound": compound_name,
            "dev_avg_by_type": {},
            "top_listings": [],
            "missing": "no_dev_benchmark",
        }

    # 2) Pull resale listings whose type has a benchmark.
    listings_stmt = (
        select(Property)
        .where(Property.compound == compound_name)
        .where(_type_filter_clause(tuple(dev_avg_by_type.keys())))
        .where(Property.resale_price.is_not(None))
        .where(Property.is_available == True)  # noqa: E712
    )
    listings = (await db.execute(listings_stmt)).scalars().all()

    deals: list[dict[str, Any]] = []
    for p in listings:
        ptype = (p.type or "").lower()
        dev_avg = dev_avg_by_type.get(ptype)
        if dev_avg is None or p.resale_price is None:
            continue
        gap = dev_avg - float(p.resale_price)
        # Surface only true bargains: skip listings where resale ≥ developer benchmark.
        if gap <= 0:
            continue
        deals.append({
            "property_id": p.id,
            "type": ptype,
            "size_sqm": p.size_sqm,
            "bedrooms": p.bedrooms,
            "resale_price": float(p.resale_price),
            "price_per_sqm": float(p.price_per_sqm) if p.price_per_sqm else None,
            "dev_avg": dev_avg,
            "gap_egp": gap,
            "gap_pct": (gap / dev_avg) * 100.0 if dev_avg else None,
            "nawy_url": p.nawy_url,
            "image_url": p.image_url,
            "developer": p.developer,
            "compound": p.compound,
            "title": p.title,
        })

    if not deals:
        return {
            "compound": compound_name,
            "dev_avg_by_type": dev_avg_by_type,
            "top_listings": [],
            "missing": "no_resale_listings",
        }

    deals.sort(key=lambda d: d["gap_egp"], reverse=True)
    return {
        "compound": compound_name,
        "dev_avg_by_type": dev_avg_by_type,
        "top_listings": deals[:top_k],
        "missing": False,
    }
