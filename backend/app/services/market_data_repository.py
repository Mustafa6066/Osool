"""
Market Data Repository
----------------------
Single source of truth for per-area market metrics (price/sqm, growth, rental yield)
and per-developer tier ratings.

Priority order:
  1. PostgreSQL `areas` / `developers` table (set by scraper or admin)
  2. Hardcoded constants in analytical_engine.AREA_PRICES / AREA_GROWTH (fallback)

Hardcoded values exist only so the system degrades gracefully when the DB row is
missing — admin tooling should backfill these tables instead of editing code.
"""
from __future__ import annotations

import logging
import time
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Area, Developer

logger = logging.getLogger(__name__)

# Lightweight in-process cache. TTL keeps it cheap; admin refresh endpoint
# clears it to force a re-read.
_CACHE_TTL_SECONDS = 600
_cache: dict[str, tuple[float, object]] = {}


def _cache_get(key: str):
    entry = _cache.get(key)
    if not entry:
        return None
    expires_at, value = entry
    if expires_at < time.time():
        _cache.pop(key, None)
        return None
    return value


def _cache_set(key: str, value, ttl: int = _CACHE_TTL_SECONDS):
    _cache[key] = (time.time() + ttl, value)


def clear_cache() -> int:
    """Invalidate all cached area/developer lookups. Returns entries cleared."""
    n = len(_cache)
    _cache.clear()
    return n


def _normalize(s: str) -> str:
    return (s or "").lower().strip()


async def _find_area(session: AsyncSession, location: str) -> Optional[Area]:
    """Best-effort match of a free-text location string to an Area row."""
    if not location:
        return None
    needle = _normalize(location)
    cache_key = f"area:{needle}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached if cached is not False else None

    # Try exact name first (English then Arabic), then ILIKE either way
    stmt = (
        select(Area)
        .where(
            (Area.name.ilike(needle))
            | (Area.name_ar.ilike(needle))
            | (Area.slug.ilike(needle))
        )
        .limit(1)
    )
    row = (await session.execute(stmt)).scalar_one_or_none()

    if row is None:
        # Fuzzy: needle contained in either name
        stmt = (
            select(Area)
            .where(
                (Area.name.ilike(f"%{needle}%"))
                | (Area.name_ar.ilike(f"%{needle}%"))
            )
            .limit(1)
        )
        row = (await session.execute(stmt)).scalar_one_or_none()

    _cache_set(cache_key, row if row is not None else False)
    return row


async def get_area_avg_price(
    location: str, session: Optional[AsyncSession] = None
) -> Optional[float]:
    """EGP/sqm for an area. Returns None if neither DB nor constants have it."""
    if session is not None:
        area = await _find_area(session, location)
        if area and area.avg_price_per_meter:
            return float(area.avg_price_per_meter)

    # Fallback to in-code constants
    from app.ai_engine.analytical_engine import AREA_PRICES
    needle = _normalize(location)
    for area_name, price in AREA_PRICES.items():
        if area_name.lower() in needle or needle in area_name.lower():
            return float(price)
    return None


async def get_area_growth(
    location: str, session: Optional[AsyncSession] = None
) -> Optional[float]:
    """YoY appreciation rate (e.g. 1.57 = +157%). None if unknown."""
    if session is not None:
        area = await _find_area(session, location)
        if area and area.price_growth_ytd:
            return float(area.price_growth_ytd)

    from app.ai_engine.analytical_engine import AREA_GROWTH
    needle = _normalize(location)
    for area_name, rate in AREA_GROWTH.items():
        if area_name.lower() in needle or needle in area_name.lower():
            return float(rate)
    return None


async def get_area_rental_yield(
    location: str, session: Optional[AsyncSession] = None
) -> Optional[float]:
    """Rental yield as decimal (e.g. 0.075 = 7.5%). None if unknown."""
    if session is not None:
        area = await _find_area(session, location)
        if area and area.rental_yield:
            return float(area.rental_yield)

    # No matching constant table for yield — analytical_engine has inline logic
    return None


async def get_developer_score(
    developer_name: str, session: Optional[AsyncSession] = None
) -> Optional[float]:
    """Returns the developers.overall_score (0-100) for the named developer, or None."""
    if not developer_name or session is None:
        return None
    needle = _normalize(developer_name)
    cache_key = f"dev:{needle}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached if cached is not False else None

    stmt = (
        select(Developer)
        .where(
            (Developer.name.ilike(f"%{needle}%"))
            | (Developer.name_ar.ilike(f"%{needle}%"))
            | (Developer.slug.ilike(needle))
        )
        .limit(1)
    )
    dev = (await session.execute(stmt)).scalar_one_or_none()
    score = float(dev.overall_score) if dev and dev.overall_score else None
    _cache_set(cache_key, score if score is not None else False)
    return score
