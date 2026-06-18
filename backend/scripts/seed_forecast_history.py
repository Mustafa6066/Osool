"""
Seed the FORECAST history corpus (real curated 2021-2026 series + CPI/FX).

This is the SEED pillar of the scientific price-forecasting feature. It loads the
curated, de-duplicated 2021-2026 series from analytical_engine into the DB history
tables WITH source citations, so price_forecast_engine has a long-run trend to fit
from day one (confidence stays "indicative" until live scrape data accrues — see
price_forecast_engine.REAL_SOURCES).

Distinct from the legacy scripts/seed_price_history.py, which generates SYNTHETIC
random-walk data (source='osool-analytics'). That synthetic data is treated as
NON-real by the engine; pass --purge-synthetic to remove it for a clean corpus.

Idempotent: deletes prior rows written by this script (by source) and re-inserts,
so citation edits take effect on re-run. Fails loudly on any duplicate
(entity, year, source) in the in-memory seed set (guards against dict-key bugs like
the historical duplicate "Red Sea" key).

Usage:
    cd backend
    python -m scripts.seed_forecast_history [--purge-synthetic]
"""
import asyncio
import os
import statistics
import sys
from collections import defaultdict
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import delete, select
from app.database import AsyncSessionLocal
from app.models import Area, DeveloperPriceHistory, MarketIndicatorHistory, PriceHistory
from app.ai_engine.analytical_engine import (
    AREA_PRICE_HISTORY, AREA_GROWTH, DEVELOPER_PRICE_HISTORY,
)
from app.ai_engine.price_forecast_engine import SEED_SOURCE

# Provenance labels this script owns (deleted + re-inserted on every run).
SEED_SOURCE_AREA = SEED_SOURCE          # PriceHistory area rows
SEED_SOURCE_DEV = SEED_SOURCE           # DeveloperPriceHistory rows
SEED_SOURCE_MACRO = "macro_seed_2026"   # MarketIndicatorHistory rows
SYNTHETIC_SOURCE = "osool-analytics"    # legacy synthetic seeder

# Arabic names + city for areas we create if missing (Area.name_ar is NOT NULL).
_AREA_META = {
    "New Cairo": ("القاهرة الجديدة", "Cairo"),
    "Sheikh Zayed": ("الشيخ زايد", "Giza"),
    "New Capital": ("العاصمة الإدارية الجديدة", "Cairo"),
    "6th October": ("السادس من أكتوبر", "Giza"),
    "North Coast": ("الساحل الشمالي", "Matrouh"),
    "Red Sea": ("البحر الأحمر", "Red Sea"),
    "Maadi": ("المعادي", "Cairo"),
    "Ain Sokhna": ("العين السخنة", "Suez"),
    "Madinaty": ("مدينتي", "Cairo"),
    "Rehab": ("الرحاب", "Cairo"),
    "New Zayed": ("زايد الجديدة", "Giza"),
    "Mostakbal City": ("مدينة المستقبل", "Cairo"),
}

# Curated Egyptian macro series (annual). APPROXIMATE seed values — the weekly
# economic_scraper (FRED + CAPMAS/CBE) refines these going forward. Citation per key.
# CPI is an INDEX LEVEL (base 2018=100); inflation_rate/egp_per_usd are levels.
_CPI_INDEX = {2018: 100.0, 2019: 109.4, 2020: 115.6, 2021: 121.6, 2022: 138.5,
              2023: 185.5, 2024: 237.4, 2025: 271.0, 2026: 306.0}
_EGP_PER_USD = {2021: 15.7, 2022: 24.5, 2023: 30.9, 2024: 48.0, 2025: 50.5, 2026: 49.0}
_INFLATION_RATE = {2021: 0.052, 2022: 0.139, 2023: 0.339, 2024: 0.281, 2025: 0.140, 2026: 0.136}
_CITATIONS = {
    "cpi_index": "https://www.capmas.gov.eg (Egypt headline CPI, rebased base 2018=100)",
    "egp_per_usd": "https://www.cbe.org.eg (CBE official USD/EGP)",
    "inflation_rate": "https://www.imf.org/en/Publications/WEO (Egypt annual CPI inflation)",
}


def _slug(name: str) -> str:
    return name.lower().strip().replace(" ", "-").replace("'", "")


def _base_developer(key: str) -> str:
    """'Emaar (Mivida)' -> 'Emaar'; 'Sky Capital' -> 'Sky Capital'."""
    return key.split(" (")[0].strip()


def _assert_unique(records, label):
    """Fail loudly on any duplicate (entity, year, source) — guards dict-key bugs."""
    seen = defaultdict(int)
    for key in records:
        seen[key] += 1
    dups = {k: c for k, c in seen.items() if c > 1}
    if dups:
        raise ValueError(f"Duplicate {label} seed keys (fix the source dict): {dups}")


def _build_area_records():
    """[(area, year, price)] from AREA_PRICE_HISTORY; assert unique (area, year)."""
    recs, keys = [], []
    for area, series in AREA_PRICE_HISTORY.items():
        for year, price in series.items():
            if isinstance(year, int):
                recs.append((area, year, float(price)))
                keys.append((area, year, SEED_SOURCE_AREA))
    _assert_unique(keys, "area-price-history")
    return recs


def _build_developer_records():
    """
    Aggregate per-project dict to (developer, unit_type, year) -> median price.

    Collapsing projects to the developer median per year gives a clean developer
    series and keeps the (developer_name, observed_at, unit_type, source) unique
    constraint satisfied (multiple Emaar projects would otherwise collide).
    """
    grouped = defaultdict(list)  # (dev, unit_type, year) -> [price]
    dev_area = {}                # (dev, unit_type) -> representative area
    for key, series in DEVELOPER_PRICE_HISTORY.items():
        dev = _base_developer(key)
        unit_type = (series.get("type") or "apartment").lower()
        area = series.get("area")
        dev_area.setdefault((dev, unit_type), area)
        for year, price in series.items():
            if isinstance(year, int):
                grouped[(dev, unit_type, year)].append(float(price))
    recs, keys = [], []
    for (dev, unit_type, year), prices in grouped.items():
        recs.append((dev, unit_type, year, statistics.median(prices), dev_area.get((dev, unit_type))))
        keys.append((dev, year, unit_type, SEED_SOURCE_DEV))
    _assert_unique(keys, "developer-price-history")
    return recs


async def _ensure_area(session, area_name) -> int:
    row = (await session.execute(select(Area).where(Area.name == area_name))).scalar_one_or_none()
    if row:
        return row.id
    name_ar, city = _AREA_META.get(area_name, (area_name, "Cairo"))
    series = AREA_PRICE_HISTORY.get(area_name, {})
    latest = max((y for y in series if isinstance(y, int)), default=None)
    area = Area(
        name=area_name, name_ar=name_ar, slug=_slug(area_name), city=city,
        avg_price_per_meter=float(series.get(latest, 0) or 0) if latest else 0,
        price_growth_ytd=float(AREA_GROWTH.get(area_name, 0.2)) * 100,
    )
    session.add(area)
    await session.flush()
    return area.id


async def seed(purge_synthetic: bool = False):
    area_recs = _build_area_records()
    dev_recs = _build_developer_records()
    print(f"📋 Validated {len(area_recs)} area points, {len(dev_recs)} developer points (no duplicates).")

    async with AsyncSessionLocal() as session:
        # --- idempotency: clear prior rows this script owns ---
        await session.execute(delete(PriceHistory).where(PriceHistory.source == SEED_SOURCE_AREA))
        await session.execute(delete(DeveloperPriceHistory).where(DeveloperPriceHistory.source == SEED_SOURCE_DEV))
        await session.execute(delete(MarketIndicatorHistory).where(MarketIndicatorHistory.source == SEED_SOURCE_MACRO))
        if purge_synthetic:
            res = await session.execute(delete(PriceHistory).where(PriceHistory.source == SYNTHETIC_SOURCE))
            print(f"🧹 Purged synthetic 'osool-analytics' rows: {res.rowcount}")

        # --- area history (PriceHistory) ---
        n_area = 0
        for area, year, price in area_recs:
            area_id = await _ensure_area(session, area)
            session.add(PriceHistory(area_id=area_id, project_id=None,
                                     date=date(year, 1, 1), price_per_m2=price,
                                     source=SEED_SOURCE_AREA))
            n_area += 1

        # --- developer history (DeveloperPriceHistory) ---
        for dev, unit_type, year, price, area in dev_recs:
            session.add(DeveloperPriceHistory(
                developer_name=dev, area=area, unit_type=unit_type,
                price_per_m2=price, observed_at=date(year, 1, 1),
                source=SEED_SOURCE_DEV,
                citation_url="analytical_engine 2026 curated market snapshot",
            ))

        # --- macro history (CPI index level + FX + inflation) ---
        n_macro = 0
        for key, series in (("cpi_index", _CPI_INDEX), ("egp_per_usd", _EGP_PER_USD),
                            ("inflation_rate", _INFLATION_RATE)):
            for year, value in series.items():
                session.add(MarketIndicatorHistory(
                    key=key, value=value, observed_at=date(year, 1, 1),
                    source=SEED_SOURCE_MACRO, citation_url=_CITATIONS[key],
                ))
                n_macro += 1

        await session.commit()
        print(f"✅ Seeded {n_area} area, {len(dev_recs)} developer, {n_macro} macro history rows.")


if __name__ == "__main__":
    asyncio.run(seed(purge_synthetic="--purge-synthetic" in sys.argv))
