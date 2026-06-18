"""
forecast_router.py
==================
HTTP surface for scientific price-per-sqm forecasting (per developer / compound / area).

Design:
* PUBLIC-BY-TEASER — uses get_current_user_optional, never 401. Free callers get a
  teaser (direction + single 12-month % + confidence label + upsell); paid callers
  get the full multi-horizon bundle. Forecasts are available on BOTH tiers.
* COMPUTE-ONCE-THEN-SLICE — the full ForecastBundle is computed (or cache-read) once
  regardless of tier, then sliced. Free does NOT short-circuit the heavy compute, so
  there is no fast/slow timing oracle revealing which scopes have premium-grade data.
* SINGLE-COMPOUND CONTAINMENT — a single_compound pass unlocks the compound AND the
  developer/area that CONTAIN it (resolved against the Property table). Encoded once
  in _scope_access().
* CACHING — the full bundle is cached in Redis (16-day TTL) under a versioned key;
  invalidate_forecast_cache() bumps the version after each scrape so stale forecasts
  expire without a delete-by-pattern.

The free/paid boundary lives in _slice_for_tier() — single source of truth.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user_optional
from app.database import get_db
from app.middleware.rate_limiting import limiter, FORECAST_RATE_LIMIT
from app.models import Area, Developer, Property, User
from app.services.cache import cache
from app.services.subscription_engine import TierResolution, resolve_access
from app.ai_engine import forecast_series_builder as fsb

_logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/forecast", tags=["forecast"])

_FORECAST_TTL_SECONDS = 60 * 60 * 24 * 16  # 16 days (≈ biweekly scrape cadence)
_VER_KEY = "forecast:ver"
# A sentinel that can never equal a real compound name, so resolve_access() returns the
# user's underlying tier (admin/premium_monthly => premium; single_compound => mismatch
# with unlocked_compound populated) without a spurious match.
_NO_COMPOUND = "\x00__no_compound__"


# ── cache helpers ─────────────────────────────────────────────────────────────
def _cache_version() -> int:
    try:
        return int(cache.get(_VER_KEY) or 1)
    except Exception:
        return 1


def invalidate_forecast_cache() -> None:
    """Bump the cache version so every forecast key becomes a miss. Call after a scrape."""
    try:
        cache.set(_VER_KEY, _cache_version() + 1, ttl=60 * 60 * 24 * 365)
    except Exception:
        _logger.warning("forecast cache invalidation failed", exc_info=True)


def _cache_key(level: str, slug: str) -> str:
    return f"forecast:v{_cache_version()}:{level}:{slug.strip().lower()}"


async def _cached(level: str, slug: str, compute):
    key = _cache_key(level, slug)
    try:
        hit = cache.get_json(key)
        if hit:
            return hit
    except Exception:
        pass
    bundle = await compute()
    try:
        cache.set_json(key, bundle, ttl=_FORECAST_TTL_SECONDS)
    except Exception:
        pass
    return bundle


# ── slug resolution ───────────────────────────────────────────────────────────
async def _developer_name(db: AsyncSession, slug: str) -> str:
    row = (await db.execute(select(Developer.name).where(Developer.slug == slug.lower()))).first()
    return row[0] if row else slug.replace("-", " ").strip()


async def _area_name(db: AsyncSession, slug: str) -> str:
    row = (await db.execute(select(Area.name).where(Area.slug == slug.lower()))).first()
    return row[0] if row else slug.replace("-", " ").strip()


# ── tier resolution with single-compound containment ─────────────────────────
async def _compound_in_scope(db: AsyncSession, compound: str, *,
                             developer: str = None, area: str = None) -> bool:
    stmt = select(func.count()).select_from(Property).where(
        func.lower(Property.compound) == compound.strip().lower()
    )
    if developer:
        stmt = stmt.where(Property.developer.ilike(f"%{developer}%"))
    if area:
        stmt = stmt.where(Property.location.ilike(f"%{area}%"))
    try:
        return ((await db.execute(stmt)).scalar() or 0) > 0
    except Exception:
        return False


async def _scope_access(db: AsyncSession, user: Optional[User], *,
                        compound: str = None, developer: str = None,
                        area: str = None) -> TierResolution:
    """
    Resolve tier for a forecast scope. A single_compound pass unlocks its own compound
    AND the developer/area that contain it.
    """
    if user is None:
        return TierResolution(tier="free", reason="free_default")
    probe = resolve_access(user, compound or _NO_COMPOUND)
    if probe.tier == "premium":
        return probe  # admin / legacy / premium_monthly, or direct compound match
    # single_compound containment for developer/area scopes (active pass only).
    if (probe.unlocked_compound and (developer or area)
            and probe.reason in ("single_compound_match", "single_compound_mismatch")):
        if await _compound_in_scope(db, probe.unlocked_compound, developer=developer, area=area):
            return TierResolution(
                tier="premium", reason="single_compound_match",
                expires_at=probe.expires_at, unlocked_compound=probe.unlocked_compound,
                days_until_expiry=probe.days_until_expiry,
            )
    return probe


# ── free/paid slicer (single source of truth) ────────────────────────────────
def _forecast_upsell(access: TierResolution) -> dict:
    headline_en = "See the full 6/12/24-month curve, confidence bands, and what's driving it."
    headline_ar = "شاهد منحنى الـ 6/12/24 شهرًا كاملًا، ونطاقات الثقة، والعوامل المؤثرة."
    if access.reason == "single_compound_mismatch" and access.unlocked_compound:
        headline_en = f"Your pass unlocks {access.unlocked_compound}. Add this one or go unlimited."
        headline_ar = f"اشتراكك يفتح {access.unlocked_compound}. أضف هذا أو ارتقِ للاشتراك الكامل."
    return {
        "headline_en": headline_en,
        "headline_ar": headline_ar,
        "sku_options": [
            {"sku": "single_compound", "price_egp": 99,
             "label_en": "This compound, 30 days — EGP 99",
             "label_ar": "هذا الكمبوند، 30 يوم — 99 جنيه"},
            {"sku": "premium_monthly", "price_egp": 299,
             "label_en": "All forecasts, monthly — EGP 299/mo",
             "label_ar": "كل التوقعات، شهريًا — 299 جنيه/شهر"},
        ],
    }


def _access_info(access: TierResolution) -> dict:
    return {
        "tier": access.tier,
        "reason": access.reason,
        "expires_at": access.expires_at.isoformat() if access.expires_at else None,
        "days_until_expiry": access.days_until_expiry,
        "unlocked_compound": access.unlocked_compound,
    }


def _slice_for_tier(bundle: dict, access: TierResolution) -> dict:
    """FREE: teaser. PAID: full bundle. The locked boundary lives here."""
    if access.tier == "premium":
        return {"tier": "premium", "access": _access_info(access), **bundle}
    # FREE — omit (don't null) the premium numbers; withhold sample_size/horizons.
    return {
        "tier": "free",
        "access": _access_info(access),
        "entity": bundle["entity"],
        "level": bundle["level"],
        "as_of": bundle.get("as_of"),
        "base_price_per_m2": bundle.get("base_price_per_m2"),   # present-day, not a forecast
        "trend_direction": bundle.get("trend_direction"),
        "headline_12mo_pct": bundle.get("headline_12mo_pct"),
        "confidence_label": bundle.get("confidence_tier"),
        "seed_dominated": bundle.get("seed_dominated"),
        "disclaimer": bundle.get("disclaimer"),
        "locked": {
            "horizons": True, "confidence_intervals": True, "real_vs_nominal": True,
            "drivers": True, "per_unit_type": True, "export": True,
        },
        "upsell": _forecast_upsell(access),
    }


# ── routes ────────────────────────────────────────────────────────────────────
@router.get("/developer/{slug}")
@limiter.limit(FORECAST_RATE_LIMIT)
async def get_developer_forecast(
    slug: str, request: Request, response: Response,
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional),
):
    name = await _developer_name(db, slug)
    bundle = await _cached("developer", slug, lambda: fsb.forecast_developer(db, name))
    access = await _scope_access(db, user, developer=name)
    return _slice_for_tier(bundle, access)


@router.get("/area/{slug}")
@limiter.limit(FORECAST_RATE_LIMIT)
async def get_area_forecast(
    slug: str, request: Request, response: Response,
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional),
):
    name = await _area_name(db, slug)
    bundle = await _cached("area", slug, lambda: fsb.forecast_area(db, name))
    access = await _scope_access(db, user, area=name)
    return _slice_for_tier(bundle, access)


@router.get("/compound/{name:path}")
@limiter.limit(FORECAST_RATE_LIMIT)
async def get_compound_forecast(
    name: str, request: Request, response: Response,
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional),
):
    bundle = await _cached("compound", name, lambda: fsb.forecast_compound(db, name))
    # single_compound holders unlock their own compound; admin/monthly unlock all.
    access = await _scope_access(db, user, compound=name)
    return _slice_for_tier(bundle, access)
