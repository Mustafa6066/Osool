"""
Comparison engine for the free-path funnel.

Two modes:

- `compare_compounds` — 2 or 3 compounds. For each compound × property type
  computes avg developer price and avg resale price, gap = dev_avg − res_avg.
  Winner is the compound with the largest gap across its types.

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


# Minimum number of rows required on each side (dev/resale) of a (compound, type)
# bucket for the bucket to count as having data. Below this we treat the bucket
# as missing rather than reporting a single-listing average.
_MIN_BUCKET_SAMPLE_SIZE = 3

# Minimum dev-price samples needed in single-compound mode to compute a
# benchmark against which resale listings are ranked.
_MIN_SINGLE_DEV_SAMPLE_SIZE = 3


def _type_filter_clause(property_types: Tuple[str, ...]):
    """
    Build a case-insensitive type filter. The DB stores values like "Apartment",
    "Villa" — we accept lowercase canonical from the caller.
    """
    lowered = [t.lower() for t in property_types]
    return func.lower(Property.type).in_(lowered)


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
             "apartment": {dev_avg, res_avg, gap_egp, dev_n, res_n} | None,
             "villa":     {...} | None,
             "max_gap_egp": float | None},
            ...
          ],
          "winner": str | None,
          "missing_compound": str | None,
        }
    If any compound has zero resale listings across all types,
    `missing_compound` is set to that compound's name and the caller should
    abort the comparison (the dialog asks the user to swap that compound).
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
        )
        .where(Property.compound.in_(compound_names))
        .where(_type_filter_clause(property_types))
        .where(Property.is_available == True)  # noqa: E712
        .group_by(Property.compound, func.lower(Property.type))
    )
    rows = (await db.execute(stmt)).all()

    # Build a lookup keyed by (compound, ptype).
    bucket: dict[tuple[str, str], dict[str, float]] = {}
    for r in rows:
        bucket[(r.compound, r.ptype)] = {
            "dev_avg": float(r.dev_avg) if r.dev_avg is not None else None,
            "dev_n": int(r.dev_n or 0),
            "res_avg": float(r.res_avg) if r.res_avg is not None else None,
            "res_n": int(r.res_n or 0),
        }

    per_compound: list[dict[str, Any]] = []
    missing_compound: Optional[str] = None

    for name in compound_names:
        entry: dict[str, Any] = {"compound": name}
        max_gap: Optional[float] = None
        any_resale_present = False

        for ptype in property_types:
            data = bucket.get((name, ptype.lower()))
            segment: Optional[dict[str, float]] = None
            if (
                data
                and data["dev_n"] >= _MIN_BUCKET_SAMPLE_SIZE
                and data["res_n"] >= _MIN_BUCKET_SAMPLE_SIZE
                and data["dev_avg"] is not None
                and data["res_avg"] is not None
            ):
                gap = data["dev_avg"] - data["res_avg"]
                segment = {
                    "dev_avg": data["dev_avg"],
                    "res_avg": data["res_avg"],
                    "gap_egp": gap,
                    "dev_n": data["dev_n"],
                    "res_n": data["res_n"],
                }
                if max_gap is None or gap > max_gap:
                    max_gap = gap
            if data and data["res_n"] > 0:
                any_resale_present = True
            entry[ptype] = segment

        entry["max_gap_egp"] = max_gap
        per_compound.append(entry)

        if not any_resale_present and missing_compound is None:
            missing_compound = name

    if missing_compound:
        return {
            "per_compound": per_compound,
            "winner": None,
            "missing_compound": missing_compound,
        }

    # Pick the winner: largest max_gap_egp. If all are None (no comparable
    # data anywhere) the winner is None and the caller falls back to upsell.
    rankable = [c for c in per_compound if c["max_gap_egp"] is not None]
    rankable.sort(key=lambda c: c["max_gap_egp"], reverse=True)
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
        # A negative gap would otherwise render as "best deal: -2M below developer",
        # which kills trust in the comparison.
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
