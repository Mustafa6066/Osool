"""
Compound + developer name dictionaries — Redis-cached, DB-backed.

The zero-token intent extractor needs lists of every compound and
developer name currently in the inventory so it can match user
prompts ("Mountain View", "Palm Hills", "SODIC") against
StructuredQuery.compounds / .developers fields.

Pulling SELECT DISTINCT on every chat turn would be wasteful: the
list changes on the order of new-scrape cadence (hours), not per
request. We cache in Redis with a 1-hour TTL, fall back to in-
memory `cache.RedisClient` for dev environments where Redis isn't
configured.

All loaders are async (need a DB session). The sync-style
zero_token_intent.extract_query accepts the pre-loaded lists as
arguments so the extractor itself stays zero-I/O.
"""
from __future__ import annotations

import json
import logging
import os
import time
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.cache import cache

logger = logging.getLogger(__name__)


# Redis keys (separate prefix so the retrieval cache invalidator
# never accidentally drops these).
_KEY_COMPOUNDS = "retrieval:dict:compounds"
_KEY_DEVELOPERS = "retrieval:dict:developers"
_KEY_LOCATIONS = "retrieval:dict:locations"

# 1 hour TTL — long enough to be free at scale, short enough that a
# new compound landing via the scraper shows up in extraction within
# a chat turn or two.
_TTL_S = int(os.getenv("RETRIEVAL_DICT_TTL", "3600"))

# In-process LRU. The Redis fallback is good enough for prod; this
# is mostly a hot path optimization for hundreds of concurrent calls
# in the same process tick.
_LOCAL_CACHE: dict[str, tuple[list[str], float]] = {}
_LOCAL_TTL_S = 30  # short — cross-process Redis is the source of truth


def _local_get(key: str) -> Optional[list[str]]:
    entry = _LOCAL_CACHE.get(key)
    if not entry:
        return None
    values, expires_at = entry
    if expires_at < time.time():
        del _LOCAL_CACHE[key]
        return None
    return values


def _local_set(key: str, values: list[str]) -> None:
    _LOCAL_CACHE[key] = (values, time.time() + _LOCAL_TTL_S)


async def _load_from_db(
    db: AsyncSession, sql: str, dedupe: bool = True
) -> list[str]:
    """Run a single SELECT and return a deduped, sorted list of strings."""
    try:
        rows = (await db.execute(text(sql))).fetchall()
    except Exception as exc:
        logger.warning("[dictionaries] DB load failed: %s", exc)
        return []
    out: list[str] = []
    seen: set[str] = set() if dedupe else set()  # noqa: F841 (placeholder)
    for r in rows:
        v = r[0]
        if not v:
            continue
        s = str(v).strip()
        if not s:
            continue
        if dedupe:
            key = s.lower()
            if key in seen:
                continue
            seen.add(key)
        out.append(s)
    # Sort by length desc so longest-match-first works downstream
    # ("Mountain View Hyde Park" should beat "Mountain View")
    out.sort(key=len, reverse=True)
    return out


async def get_compounds(db: AsyncSession) -> list[str]:
    """
    Distinct compound names currently in the inventory. Cached in Redis (1hr)
    + in-process (30s). Returns [] on any failure (extraction skips that path).
    """
    local = _local_get(_KEY_COMPOUNDS)
    if local is not None:
        return local
    # Redis
    try:
        cached = cache.get_json(_KEY_COMPOUNDS)
        if cached:
            _local_set(_KEY_COMPOUNDS, cached)
            return cached
    except Exception:
        pass
    # DB
    values = await _load_from_db(
        db,
        "SELECT DISTINCT compound FROM properties "
        "WHERE compound IS NOT NULL AND compound <> '' AND is_available = true",
    )
    if values:
        try:
            cache.set_json(_KEY_COMPOUNDS, values, ttl=_TTL_S)
        except Exception:
            pass
        _local_set(_KEY_COMPOUNDS, values)
    return values


async def get_developers(db: AsyncSession) -> list[str]:
    """Distinct developer names. Same caching as get_compounds."""
    local = _local_get(_KEY_DEVELOPERS)
    if local is not None:
        return local
    try:
        cached = cache.get_json(_KEY_DEVELOPERS)
        if cached:
            _local_set(_KEY_DEVELOPERS, cached)
            return cached
    except Exception:
        pass
    values = await _load_from_db(
        db,
        "SELECT DISTINCT developer FROM properties "
        "WHERE developer IS NOT NULL AND developer <> '' AND is_available = true",
    )
    if values:
        try:
            cache.set_json(_KEY_DEVELOPERS, values, ttl=_TTL_S)
        except Exception:
            pass
        _local_set(_KEY_DEVELOPERS, values)
    return values


async def get_locations(db: AsyncSession) -> list[str]:
    """
    Distinct location strings as they appear in the DB. These are NOT
    canonical zones — LOCATION_ZONE_MAP in deterministic_normalizer maps
    raw values like 'Fifth Settlement' -> 'New Cairo'. Useful when the
    user types a non-canonical spelling that's still in the inventory.
    """
    local = _local_get(_KEY_LOCATIONS)
    if local is not None:
        return local
    try:
        cached = cache.get_json(_KEY_LOCATIONS)
        if cached:
            _local_set(_KEY_LOCATIONS, cached)
            return cached
    except Exception:
        pass
    values = await _load_from_db(
        db,
        "SELECT DISTINCT location FROM properties "
        "WHERE location IS NOT NULL AND location <> '' AND is_available = true",
    )
    if values:
        try:
            cache.set_json(_KEY_LOCATIONS, values, ttl=_TTL_S)
        except Exception:
            pass
        _local_set(_KEY_LOCATIONS, values)
    return values


def invalidate_all() -> None:
    """Drop both Redis and local cache. Called after a major scrape ingestion."""
    _LOCAL_CACHE.clear()
    try:
        if cache.redis is not None:
            cache.redis.delete(_KEY_COMPOUNDS, _KEY_DEVELOPERS, _KEY_LOCATIONS)
    except Exception:
        pass
