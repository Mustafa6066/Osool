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

from sqlalchemy import case, func, select
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

    if row is None and len(needle) >= 3:
        # R6: substring match, ordered DETERMINISTICALLY by specificity (shortest
        # name containing the needle = closest match, then alphabetical). A bare
        # LIMIT 1 with no ORDER BY returned an ARBITRARY of {Cairo, New Cairo, Cairo
        # Festival City} for "cairo". Needles < 3 chars are rejected (they match half
        # the table) — the exact path above still handles short canonical names.
        stmt = (
            select(Area)
            .where(
                (Area.name.ilike(f"%{needle}%"))
                | (Area.name_ar.ilike(f"%{needle}%"))
            )
            .order_by(
                func.length(func.coalesce(Area.name, Area.name_ar)).asc(),
                Area.name.asc(),
            )
            .limit(1)
        )
        row = (await session.execute(stmt)).scalar_one_or_none()
        if row is not None:
            logger.info("[market-data] fuzzy area resolve: %r → %r", location, row.name)

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
        # R13: a real 0.0 (a flat market) is NOT missing — `if ...price_growth_ytd:`
        # treated it as falsy and fell back to the hardcoded AREA_GROWTH constant
        # (e.g. +157%), fabricating appreciation for a market that didn't move.
        if area and area.price_growth_ytd is not None:
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
        if area and area.rental_yield is not None:  # R13: 0.0 is valid, not missing
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
    if len(needle) < 3:
        return None  # R6: a 1-2 char needle matches half the table — reject it
    cache_key = f"dev:{needle}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached if cached is not False else None

    # R6: deterministic specificity ordering — "nasr" must not return an ARBITRARY
    # of {Nasr City, Nasrallah}. Rank an EXACT slug/name match first, then the
    # shortest matching name (closest), then alphabetical. (The <3 reject above
    # gates the whole lookup, unlike _find_area which only gates its fuzzy block —
    # no real Egyptian developer has a 1-2 char slug, so the asymmetry is harmless.)
    stmt = (
        select(Developer)
        .where(
            (Developer.name.ilike(f"%{needle}%"))
            | (Developer.name_ar.ilike(f"%{needle}%"))
            | (Developer.slug.ilike(needle))
        )
        .order_by(
            case(
                (Developer.slug.ilike(needle), 0),
                (func.lower(Developer.name) == needle, 0),
                else_=1,
            ).asc(),
            func.length(func.coalesce(Developer.name, Developer.name_ar)).asc(),
            Developer.name.asc(),
        )
        .limit(1)
    )
    dev = (await session.execute(stmt)).scalar_one_or_none()
    # R13: a legitimate 0.0 score (worst-rated developer) is NOT missing data.
    score = float(dev.overall_score) if dev and dev.overall_score is not None else None
    _cache_set(cache_key, score if score is not None else False)
    return score
