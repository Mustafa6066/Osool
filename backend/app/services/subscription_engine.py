"""
subscription_engine.py
======================
Tiered-access resolver for the v1 buyer haggle product.

The product has two paid SKUs and two grandfathered states:

* free                — default; no premium features
* single_compound     — EGP 99 one-time; unlocks ONE compound for 30 days
* premium_monthly     — EGP 299/month; unlocks all compounds; auto-renews
* premium (legacy)    — pre-v1 unlimited tier; treated as no-expiry premium
* admin               — Osool staff; full access always

This module is the SINGLE source of truth for "does this user have premium
access to this compound right now?". pricing_router and any future
report/PDF/alert endpoint must route through resolve_access().

No HTTP, no DB writes (except via the explicit grant_* helpers). Pure
business logic + lightweight reads.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Literal, Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User

_logger = logging.getLogger(__name__)


Tier = Literal["free", "premium"]
Reason = Literal[
    "admin",
    "legacy_premium",
    "premium_monthly_active",
    "premium_monthly_expired",
    "single_compound_match",
    "single_compound_mismatch",
    "single_compound_expired",
    "free_default",
]


# Single-compound SKU duration. Centralised here so paymob_billing + the
# expiry cron + any tests share the same source of truth.
SINGLE_COMPOUND_DURATION = timedelta(days=30)
PREMIUM_MONTHLY_DURATION = timedelta(days=30)


@dataclass(frozen=True)
class TierResolution:
    """
    Outcome of resolve_access(user, compound).

    Includes WHY the user got their tier so the API can surface meaningful
    messages ("your single-compound pass for X expired Y days ago — renew
    to keep access").
    """
    tier: Tier
    reason: Reason
    expires_at: Optional[datetime] = None
    unlocked_compound: Optional[str] = None
    days_until_expiry: Optional[int] = None


# ---------------------------------------------------------------------------
# Resolver — the central function
# ---------------------------------------------------------------------------


def resolve_access(
    user: User,
    compound: str,
    *,
    now: Optional[datetime] = None,
) -> TierResolution:
    """
    Resolve premium-vs-free access for (user, compound).

    Precedence:
      1. admin              → premium (always)
      2. legacy 'premium'   → premium (no expiry semantics)
      3. premium_monthly    → premium if expires_at > now, else expired
      4. single_compound    → premium if unlocked matches AND expires_at > now
      5. anything else      → free

    `now` is injectable for testability; defaults to datetime.now(timezone.utc).
    """
    current_time = now or datetime.now(timezone.utc)
    tier_raw = (getattr(user, "subscription_tier", "free") or "free").lower().strip()
    expires_at = getattr(user, "subscription_expires_at", None)
    unlocked = getattr(user, "unlocked_compound_id", None)

    # ── 1. Admin: always premium ─────────────────────────────────────────
    if tier_raw == "admin":
        return TierResolution(tier="premium", reason="admin")

    # ── 2. Legacy 'premium' (pre-v1, no expiry semantics) ────────────────
    if tier_raw == "premium":
        return TierResolution(tier="premium", reason="legacy_premium")

    # ── 3. premium_monthly ───────────────────────────────────────────────
    if tier_raw == "premium_monthly":
        if expires_at and _aware(expires_at) > current_time:
            return TierResolution(
                tier="premium",
                reason="premium_monthly_active",
                expires_at=_aware(expires_at),
                days_until_expiry=_days_until(_aware(expires_at), current_time),
            )
        # Expired — fall through to free, but mark the reason so the UI
        # can prompt for renewal specifically.
        return TierResolution(
            tier="free",
            reason="premium_monthly_expired",
            expires_at=_aware(expires_at) if expires_at else None,
        )

    # ── 4. single_compound ───────────────────────────────────────────────
    if tier_raw == "single_compound":
        if not expires_at or _aware(expires_at) <= current_time:
            return TierResolution(
                tier="free",
                reason="single_compound_expired",
                expires_at=_aware(expires_at) if expires_at else None,
                unlocked_compound=unlocked,
            )
        if _compound_matches(unlocked, compound):
            return TierResolution(
                tier="premium",
                reason="single_compound_match",
                expires_at=_aware(expires_at),
                unlocked_compound=unlocked,
                days_until_expiry=_days_until(_aware(expires_at), current_time),
            )
        # Active pass, but for a different compound.
        return TierResolution(
            tier="free",
            reason="single_compound_mismatch",
            expires_at=_aware(expires_at),
            unlocked_compound=unlocked,
            days_until_expiry=_days_until(_aware(expires_at), current_time),
        )

    # ── 5. Default ───────────────────────────────────────────────────────
    return TierResolution(tier="free", reason="free_default")


# ---------------------------------------------------------------------------
# Grant helpers — called by Paymob webhook + admin override paths
# ---------------------------------------------------------------------------


async def grant_single_compound(
    db: AsyncSession,
    user: User,
    *,
    compound: str,
    duration: timedelta = SINGLE_COMPOUND_DURATION,
    now: Optional[datetime] = None,
) -> User:
    """
    Grant the EGP 99 single-compound SKU.

    If the user already has premium_monthly or admin, this is a no-op (those
    tiers are strictly broader). If they have an existing single_compound
    pass for a DIFFERENT compound, this overwrites it — the new purchase wins.

    NOTE: caller is responsible for db.commit(). This function only mutates
    the ORM object so it can be batched with billing-record writes.
    """
    current_time = now or datetime.now(timezone.utc)
    existing = resolve_access(user, compound, now=current_time)

    # Don't downgrade broader tiers
    if existing.tier == "premium" and existing.reason in {
        "admin", "legacy_premium", "premium_monthly_active",
    }:
        _logger.info(
            "grant_single_compound: user=%s already has %s; no-op",
            user.id, existing.reason,
        )
        return user

    user.subscription_tier = "single_compound"
    user.unlocked_compound_id = compound
    user.subscription_expires_at = current_time + duration
    user.subscription_auto_renew = False
    return user


async def grant_premium_monthly(
    db: AsyncSession,
    user: User,
    *,
    duration: timedelta = PREMIUM_MONTHLY_DURATION,
    auto_renew: bool = True,
    now: Optional[datetime] = None,
) -> User:
    """
    Grant the EGP 299/mo unlimited SKU.

    If extending an existing active premium_monthly, the new expiry is
    `current_expiry + duration` (stacks rather than truncates). If renewing
    after expiry, expiry = now + duration.

    NOTE: caller is responsible for db.commit().
    """
    current_time = now or datetime.now(timezone.utc)
    existing_expiry = (
        _aware(user.subscription_expires_at)
        if user.subscription_tier == "premium_monthly"
        and user.subscription_expires_at
        and _aware(user.subscription_expires_at) > current_time
        else current_time
    )

    user.subscription_tier = "premium_monthly"
    user.subscription_expires_at = existing_expiry + duration
    user.subscription_auto_renew = auto_renew
    # Clear single-compound scope if it was set previously
    user.unlocked_compound_id = None
    return user


async def cancel_auto_renew(db: AsyncSession, user: User) -> User:
    """
    Turn off auto-renew. User keeps premium until the current period expires,
    then drops to free. Caller commits.
    """
    user.subscription_auto_renew = False
    return user


# ---------------------------------------------------------------------------
# FastAPI dependency factory
# ---------------------------------------------------------------------------


def require_premium_for_compound(compound: str):
    """
    Build a FastAPI dependency that 402s the request if the user doesn't
    have premium access to `compound`.

    Usage:
        @router.post("/something")
        async def something(
            body: SomeRequest,
            user: User = Depends(require_premium_for_compound(body.compound)),
        ): ...

    The compound name comes from the request body, which is awkward for a
    dependency — most callers will just call `resolve_access` inline in the
    handler. This factory exists for endpoints where premium is a hard gate
    (PDF report, alerts setup, etc.) and the compound is in the path or
    pre-resolved.
    """
    async def _dep(user: User) -> User:
        access = resolve_access(user, compound)
        if access.tier != "premium":
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=_payment_required_detail(access, compound),
            )
        return user
    return _dep


def _payment_required_detail(access: TierResolution, compound: str) -> dict:
    """Build a bilingual 402 payload from a TierResolution."""
    if access.reason == "single_compound_mismatch":
        return {
            "error_code": "PREMIUM_REQUIRED_DIFFERENT_COMPOUND",
            "message_en": (
                f"Your single-compound pass unlocks {access.unlocked_compound}, "
                f"not {compound}. Upgrade to unlimited or buy a pass for this one."
            ),
            "message_ar": (
                f"اشتراكك يفتح كمبوند {access.unlocked_compound} فقط، "
                f"مش {compound}. ارتقي للاشتراك الكامل أو اشتري باقة الكمبوند ده."
            ),
            "unlocked_compound": access.unlocked_compound,
        }
    if access.reason in {"single_compound_expired", "premium_monthly_expired"}:
        return {
            "error_code": "PREMIUM_REQUIRED_EXPIRED",
            "message_en": "Your premium access has expired. Renew to continue.",
            "message_ar": "اشتراكك انتهى. جدد الاشتراك للمتابعة.",
            "expires_at": access.expires_at.isoformat() if access.expires_at else None,
        }
    return {
        "error_code": "PREMIUM_REQUIRED",
        "message_en": "This feature is premium-only. Choose a pass to continue.",
        "message_ar": "هذه الميزة متاحة للاشتراك المدفوع فقط. اختر باقة للمتابعة.",
    }


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------


def _aware(dt: datetime) -> datetime:
    """Ensure a datetime is timezone-aware (treat naive as UTC)."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _days_until(target: datetime, now: datetime) -> int:
    """Whole days until `target` (negative if past). Always rounds toward zero."""
    delta = target - now
    return int(delta.total_seconds() // 86400)


def _compound_matches(unlocked: Optional[str], requested: str) -> bool:
    """Case-insensitive trimmed comparison of canonical compound names."""
    if not unlocked or not requested:
        return False
    return unlocked.strip().lower() == requested.strip().lower()
