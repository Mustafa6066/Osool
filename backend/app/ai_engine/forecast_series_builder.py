"""
Data-access layer for the price forecast engine.

Assembles the raw (date, nominal price/m², provenance) point lists an entity needs
by UNIONing the SEED history (PriceHistory / developer_price_history) with the
ACCUMULATE path (monthly aggregates of PropertyPriceSnapshot), plus the CPI
index-level deflator series — then hands them to price_forecast_engine.compute_forecast.

Kept separate from the math so the engine stays unit-testable without a DB.
All queries are defensive: a missing table/row yields an empty series (the engine
then shrinks to the parent / regime prior) rather than raising.

National parent = median-of-area-medians (a fixed-composition index) to avoid the
portfolio mix-shift artifact a raw AVG over all snapshots would introduce.
"""
from __future__ import annotations

import logging
import statistics
from collections import defaultdict
from datetime import date, datetime
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Area, DeveloperPriceHistory, MarketIndicatorHistory, PriceHistory,
    Property, PropertyPriceSnapshot, SEOProject,
)
from app.ai_engine.price_forecast_engine import SeriesPoint, CpiPoint, compute_forecast
from app.services.market_data_repository import _find_area

logger = logging.getLogger(__name__)


def _as_date(d) -> date:
    if isinstance(d, datetime):
        return d.date()
    return d


# ── CPI deflator series ───────────────────────────────────────────────────────
async def fetch_cpi_series(session: AsyncSession) -> list[CpiPoint]:
    """CPI INDEX LEVEL series for real-vs-nominal deflation. Empty -> engine caps confidence."""
    try:
        rows = (await session.execute(
            select(MarketIndicatorHistory.observed_at, MarketIndicatorHistory.value)
            .where(MarketIndicatorHistory.key == "cpi_index")
            .order_by(MarketIndicatorHistory.observed_at)
        )).all()
        return [CpiPoint(_as_date(r[0]), float(r[1])) for r in rows if r[1]]
    except Exception:  # table may not exist yet pre-migration
        logger.warning("CPI history unavailable; forecasts run on nominal trend", exc_info=True)
        return []


async def latest_inflation_rate(session: AsyncSession) -> Optional[float]:
    try:
        row = (await session.execute(
            select(MarketIndicatorHistory.value)
            .where(MarketIndicatorHistory.key == "inflation_rate")
            .order_by(MarketIndicatorHistory.observed_at.desc()).limit(1)
        )).first()
        return float(row[0]) if row else None
    except Exception:
        return None


# ── Accumulate path: monthly snapshot aggregates ──────────────────────────────
async def _snapshot_monthly(session: AsyncSession, *, compound: str = None,
                            developer: str = None, location: str = None) -> list[SeriesPoint]:
    """Monthly AVG(price_per_sqm) over accumulated PropertyPriceSnapshot rows (real data)."""
    try:
        month = func.date_trunc("month", PropertyPriceSnapshot.observed_at)
        stmt = (
            select(month, func.avg(PropertyPriceSnapshot.price_per_sqm))
            .join(Property, Property.id == PropertyPriceSnapshot.property_id)
            .where(PropertyPriceSnapshot.price_per_sqm.isnot(None))
            .where(PropertyPriceSnapshot.source != "backfill")  # n=1 anchors add no trend signal
        )
        if compound:
            stmt = stmt.where(func.lower(Property.compound) == compound.lower())
        if developer:
            stmt = stmt.where(Property.developer.ilike(f"%{developer}%"))
        if location:
            stmt = stmt.where(Property.location.ilike(f"%{location}%"))
        stmt = stmt.group_by(month).order_by(month)
        rows = (await session.execute(stmt)).all()
        return [SeriesPoint(_as_date(r[0]), float(r[1]), "nawy") for r in rows if r[1]]
    except Exception:
        logger.warning("snapshot aggregate failed", exc_info=True)
        return []


# ── Seed path: history tables ─────────────────────────────────────────────────
async def _price_history_area(session: AsyncSession, area_name: str) -> list[SeriesPoint]:
    area = await _find_area(session, area_name)
    if not area:
        return []
    rows = (await session.execute(
        select(PriceHistory.date, PriceHistory.price_per_m2, PriceHistory.source)
        .where(PriceHistory.area_id == area.id).order_by(PriceHistory.date)
    )).all()
    return [SeriesPoint(_as_date(r[0]), float(r[1]), r[2] or "manual") for r in rows if r[1]]


async def _price_history_compound(session: AsyncSession, compound: str) -> list[SeriesPoint]:
    proj = (await session.execute(
        select(SEOProject.id).where(
            (SEOProject.name.ilike(compound)) | (SEOProject.name_ar.ilike(compound))
        ).limit(1)
    )).first()
    if not proj:
        return []
    rows = (await session.execute(
        select(PriceHistory.date, PriceHistory.price_per_m2, PriceHistory.source)
        .where(PriceHistory.project_id == proj[0]).order_by(PriceHistory.date)
    )).all()
    return [SeriesPoint(_as_date(r[0]), float(r[1]), r[2] or "manual") for r in rows if r[1]]


async def _developer_history(session: AsyncSession, developer_name: str) -> list[SeriesPoint]:
    rows = (await session.execute(
        select(DeveloperPriceHistory.observed_at, DeveloperPriceHistory.price_per_m2,
               DeveloperPriceHistory.source)
        .where(DeveloperPriceHistory.developer_name.ilike(f"%{developer_name}%"))
        .order_by(DeveloperPriceHistory.observed_at)
    )).all()
    return [SeriesPoint(_as_date(r[0]), float(r[1]), r[2] or "manual") for r in rows if r[1]]


async def _national_points(session: AsyncSession) -> list[SeriesPoint]:
    """Median-of-area-medians per year — a fixed-composition index (mix-shift resistant)."""
    try:
        rows = (await session.execute(
            select(PriceHistory.area_id, PriceHistory.date, PriceHistory.price_per_m2)
            .where(PriceHistory.area_id.isnot(None))
        )).all()
    except Exception:
        return []
    by_year_area: dict[int, dict[int, list[float]]] = defaultdict(lambda: defaultdict(list))
    for area_id, d, p in rows:
        if p:
            by_year_area[_as_date(d).year][area_id].append(float(p))
    pts: list[SeriesPoint] = []
    for year, areas in sorted(by_year_area.items()):
        area_medians = [statistics.median(v) for v in areas.values() if v]
        if area_medians:
            pts.append(SeriesPoint(date(year, 1, 1), statistics.median(area_medians),
                                   "analytical_engine_seed_2026"))
    return pts


# ── Context resolution ─────────────────────────────────────────────────────────
async def _resolve_compound_context(session: AsyncSession, compound: str):
    """Return (area/location, developer) for a compound from the Property table."""
    row = (await session.execute(
        select(Property.location, Property.developer)
        .where(func.lower(Property.compound) == compound.lower())
        .where(Property.location.isnot(None))
        .limit(1)
    )).first()
    return (row[0], row[1]) if row else (None, None)


async def _developer_primary_area(session: AsyncSession, developer_name: str) -> Optional[str]:
    row = (await session.execute(
        select(Property.location, func.count())
        .where(Property.developer.ilike(f"%{developer_name}%"))
        .where(Property.location.isnot(None))
        .group_by(Property.location).order_by(func.count().desc()).limit(1)
    )).first()
    return row[0] if row else None


# ── Public builders: assemble compute_forecast(**kwargs) ──────────────────────
async def forecast_area(session: AsyncSession, area_name: str, horizons=(6, 12, 24)) -> dict:
    own = (await _price_history_area(session, area_name)) + (await _snapshot_monthly(session, location=area_name))
    return compute_forecast(
        entity=area_name, level="area", own_points=own,
        parent_chain=[await _national_points(session)],
        cpi_points=await fetch_cpi_series(session),
        location=area_name,
        latest_inflation=await latest_inflation_rate(session),
        horizons=horizons,
    )


async def forecast_developer(session: AsyncSession, developer_name: str, horizons=(6, 12, 24)) -> dict:
    own = (await _developer_history(session, developer_name)) + (await _snapshot_monthly(session, developer=developer_name))
    area = await _developer_primary_area(session, developer_name)
    parents = [await _national_points(session)]
    if area:
        parents.append((await _price_history_area(session, area)) + (await _snapshot_monthly(session, location=area)))
    return compute_forecast(
        entity=developer_name, level="developer", own_points=own, parent_chain=parents,
        cpi_points=await fetch_cpi_series(session),
        location=area or "", developer_name=developer_name,
        latest_inflation=await latest_inflation_rate(session), horizons=horizons,
    )


async def forecast_compound(session: AsyncSession, compound: str, horizons=(6, 12, 24)) -> dict:
    location, developer = await _resolve_compound_context(session, compound)
    own = (await _price_history_compound(session, compound)) + (await _snapshot_monthly(session, compound=compound))
    parents = [await _national_points(session)]
    if location:
        parents.append((await _price_history_area(session, location)) + (await _snapshot_monthly(session, location=location)))
    if developer:
        parents.append((await _developer_history(session, developer)) + (await _snapshot_monthly(session, developer=developer)))
    return compute_forecast(
        entity=compound, level="compound", own_points=own, parent_chain=parents,
        cpi_points=await fetch_cpi_series(session),
        location=location or "", developer_name=developer or "",
        latest_inflation=await latest_inflation_rate(session), horizons=horizons,
    )
