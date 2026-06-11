"""
freemium_router.py
==================
Tiered freemium authentication and gated broker-offer intelligence endpoint.

Architecture overview
---------------------

                     ┌─────────────────────────────────────────────────┐
                     │         POST /api/evaluate/reality-check        │
                     └───────────────────┬─────────────────────────────┘
                                         │
                     ┌───────────────────▼─────────────────────────────┐
                     │         verify_tier_clearance (dependency)       │
                     │                                                  │
                     │  1. Extract: Authorization: Bearer OR cookie     │
                     │  2. Decode JWT → look up User.subscription_tier  │
                     │  3. is_premium = (tier in {"premium","admin"})   │
                     │  4. Free tier → enforce Redis rate limit         │
                     │     (3 requests per IP per 24-hour window)       │
                     └───────────────────┬─────────────────────────────┘
                                         │ TierContext
                     ┌───────────────────▼─────────────────────────────┐
                     │              Evaluation Pipeline                 │
                     │                                                  │
                     │  a. Build PropertyListing from offer payload     │
                     │  b. ValuationEngine → normalized price/sqm       │
                     │  c. DB → compound secondary-market mean & count  │
                     │  d. Compute overpay delta %, is_offer_la2ta      │
                     │  e. DB → La2ta alternatives in compound          │
                     │  f. Masking Engine (non-premium path)            │
                     └─────────────────────────────────────────────────┘

Rate-limiting contract
----------------------
Free tier:  maximum ``_FREE_TIER_REQUEST_LIMIT`` (3) requests per
            ``_RATE_WINDOW_SECONDS`` (86400 s = 24 h) per IPv4/v6 address.

Redis key:  ``freemium:rl:{client_ip}``
Algorithm:  INCR + conditional EXPIRE (atomic per-key pipeline).
Fallback:   In-memory dict with manual TTL when Redis is unavailable.
            Memory fallback **does not survive restarts** — acceptable for
            a freemium gate in a development/staging context.

Scraper resistance
------------------
* Rate limit is enforced before any computation is performed.
* Response latency is not artificially constant (avoids timing oracles).
* ``X-RateLimit-Remaining`` header is omitted on the premium path to avoid
  leaking tier status to unauthenticated probes.
* 429 responses include ``Retry-After`` (seconds until window resets).
* Masked fields always return the exact sentinel ``"[GATED_PREMIUM_ACCESS]"``;
  never ``null`` or empty string (prevents empty-field inference attacks).

Masking contract
----------------
For ``is_premium=False`` the following fields of every ``ArbitrageAlternative``
in the response array are replaced with the sentinel string:

  • ``broker_direct_contact``   (contact channel for the resale agent)
  • ``building_number``         (physical building identifier in compound)
  • ``exact_unit_id``           (specific unit / apartment reference)

All numeric valuation fields (savings %, compound mean, cash NPV) are
preserved to demonstrate the tangible return on joining the premium tier.
"""

from __future__ import annotations

import hashlib
import logging
import math
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Final, Optional

from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Request, Response, status
from pydantic import BaseModel, Field, field_validator, model_validator
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user_optional
from app.ai_engine.free_tier_gate import FreeTierConversionGate, build_value_sandwich
from app.database import AsyncSessionLocal, get_db
from app.models import User
from app.valuation_engine import (
    DEFAULT_CBE_RATE,
    _LA2TA_THRESHOLD,
    NormalizedAssetMetrics,
    PaymentTimeline,
    PropertyListing,
    ValuationEngine,
    ViewOrientation,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

#: Maximum free-tier requests per rate-limit window per IP.
_FREE_TIER_REQUEST_LIMIT: Final[int] = 3

#: Rate-limit window in seconds (24 hours).
_RATE_WINDOW_SECONDS: Final[int] = 86_400

#: Redis key namespace for freemium rate-limit counters.
_RL_KEY_PREFIX: Final[str] = "freemium:rl:"

#: Subscription tier values treated as full premium access.
_PREMIUM_TIERS: Final[frozenset[str]] = frozenset({"premium", "admin"})

#: Sentinel string applied to every gated field in the free-tier response.
_GATED_SENTINEL: Final[str] = "[GATED_PREMIUM_ACCESS]"

#: Default floor level assumed when not supplied by the broker payload.
#: Floor 3 is deliberately mid-range: above ground (no garden premium),
#: below elevated threshold (no high-floor premium) — gives a structurally
#: neutral normalisation baseline for the offer.
_DEFAULT_FLOOR_LEVEL: Final[int] = 3

#: Maximum La2ta alternatives returned per compound to bound response size.
_MAX_ALTERNATIVES: Final[int] = 10

#: Regex for extracting IPv4/IPv6 from ``X-Forwarded-For`` header.
_IP_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
    r"[0-9a-fA-F:]{3,39})$"
)

# Module-level in-memory rate-limit fallback when Redis is unavailable.
# Structure: {client_ip: {"count": int, "window_start": float}}
_mem_rl: dict[str, dict[str, Any]] = {}

# ---------------------------------------------------------------------------
# Shared ValuationEngine singleton — sourced from app.valuation_engine so
# that runtime CBE-rate updates from the FastAPI lifespan handler reach us
# without a restart.
# ---------------------------------------------------------------------------


def _get_valuation_engine() -> ValuationEngine:
    """Return the process-wide ValuationEngine (rate-current at call time)."""
    from app import valuation_engine as _ve

    return _ve._engine  # noqa: SLF001 — intentional cross-module sharing

# ---------------------------------------------------------------------------
# Input / output Pydantic schemas
# ---------------------------------------------------------------------------


class BrokerOfferEvaluation(BaseModel):
    """
    Client-submitted broker offer to be evaluated against compound market data.

    All fields are validated at the Pydantic boundary; the endpoint never
    passes raw request data to the valuation engine or the database.

    Notes
    -----
    ``annual_installments_count`` defaults to 4 (quarterly payments), which
    reflects the most common Egyptian developer payment structure.  Override
    to 12 for monthly plans or 2 for semi-annual.

    The ``down_payment`` must be strictly positive and strictly less than
    ``stated_total_price``; the residual is divided evenly across all
    instalment periods to derive the ``periodic_installment_amount`` that
    the ``ValuationEngine`` uses for NPV flattening.
    """

    compound_id: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Parent compound identifier — must match a known compound in the listings table.",
    )
    stated_total_price: float = Field(
        ...,
        gt=0,
        description="Nominal total asking price as stated by the broker (EGP).",
    )
    space_sqm: float = Field(
        ...,
        gt=0,
        lt=10_000,
        description="Net usable area in square metres.",
    )
    down_payment: float = Field(
        ...,
        gt=0,
        description="Upfront payment due at contract signing (EGP).  Must be < stated_total_price.",
    )
    installment_years: int = Field(
        ...,
        ge=1,
        le=30,
        description="Total instalment tenure in calendar years.",
    )
    annual_installments_count: int = Field(
        default=4,
        ge=1,
        le=12,
        description=(
            "Number of periodic payments per year "
            "(1=annual, 2=semi-annual, 4=quarterly, 12=monthly)."
        ),
    )

    @field_validator("compound_id")
    @classmethod
    def _sanitise_compound_id(cls, v: str) -> str:
        """Strip surrounding whitespace; reject strings containing path-traversal characters."""
        v = v.strip()
        if not re.match(r"^[\w\-\. ]+$", v):
            raise ValueError(
                "compound_id must contain only alphanumeric characters, "
                "hyphens, underscores, dots, or spaces."
            )
        return v

    @model_validator(mode="after")
    def _down_payment_below_total(self) -> "BrokerOfferEvaluation":
        if self.down_payment >= self.stated_total_price:
            raise ValueError(
                "down_payment must be strictly less than stated_total_price.  "
                f"Got down_payment={self.down_payment:,.2f}, "
                f"stated_total_price={self.stated_total_price:,.2f}."
            )
        return self

    @property
    def residual_balance(self) -> float:
        """Remaining balance after down payment (EGP)."""
        return self.stated_total_price - self.down_payment

    @property
    def total_instalment_count(self) -> int:
        """Total number of periodic payment events over the full tenure."""
        return self.installment_years * self.annual_installments_count

    @property
    def periodic_instalment_amount(self) -> float:
        """EGP value of each individual periodic payment (even amortisation)."""
        return self.residual_balance / self.total_instalment_count


class ArbitrageAlternative(BaseModel):
    """
    A single La2ta-classified listing in the same compound as the evaluated offer.

    The fields ``broker_direct_contact``, ``building_number``, and
    ``exact_unit_id`` are replaced with ``"[GATED_PREMIUM_ACCESS]"`` for
    unauthenticated and free-tier callers.  All numeric valuation fields are
    always present so callers can quantify the savings they are missing.
    """

    listing_id: str
    compound_id: str
    geographic_zone: str
    total_price_egp: float
    size_sqm: float
    floor_level: int
    view_orientation: str
    delivery_year: int
    is_secondary_market: bool
    cash_npv_egp: float
    normalized_cash_price_sqm: float

    #: Percentage points cheaper than the submitted broker offer (positive = cheaper).
    savings_vs_offer_pct: float = Field(
        description=(
            "How much cheaper this alternative is relative to the evaluated "
            "offer's normalised price/sqm.  Positive values indicate savings; "
            "negative values are impossible here because only La2ta units appear."
        )
    )
    #: Percentage discount below the compound's secondary-market mean (always ≥ 15 %).
    discount_vs_compound_mean_pct: float = Field(
        description=(
            "Depth of discount relative to the compound secondary-market mean. "
            "La2ta classification requires ≥ 15 %."
        )
    )

    # ── Premium-gated identification fields ──────────────────────────────────
    broker_direct_contact: str = Field(
        description=(
            "Direct contact channel for the resale broker handling this unit. "
            "Visible to SUBSCRIBER tier only."
        )
    )
    building_number: str = Field(
        description=(
            "Physical building identifier within the compound. "
            "Visible to SUBSCRIBER tier only."
        )
    )
    exact_unit_id: str = Field(
        description=(
            "Unique unit/apartment reference assigned by the developer. "
            "Visible to SUBSCRIBER tier only."
        )
    )


class CompoundBenchmarkSummary(BaseModel):
    """Aggregate statistics derived from the compound's secondary-market listings."""

    compound_id: str
    secondary_market_listing_count: int = Field(
        description="Number of secondary-market listings with stored valuation metrics."
    )
    compound_mean_normalized_sqm: float = Field(
        description="Average normalised cash-equivalent price/sqm across secondary listings (EGP/m²)."
    )
    compound_min_normalized_sqm: float = Field(
        description="Minimum normalised price/sqm in the compound (cheapest active listing)."
    )
    compound_max_normalized_sqm: float = Field(
        description="Maximum normalised price/sqm in the compound (most expensive active listing)."
    )


class RealityCheckResponse(BaseModel):
    """
    Full broker-offer evaluation result.

    Numeric evaluation fields are always present.  The ``alternatives`` list
    contains La2ta-classified competing units in the same compound; the three
    identification fields within each alternative are masked for free-tier
    callers.

    ``overpay_delta_pct`` semantics
    --------------------------------
    * Positive — the submitted offer is priced **above** the compound
      secondary-market mean (the buyer would overpay).
    * Zero — offer sits exactly at the compound mean.
    * Negative — offer is below the compound mean (a potential deal).
    """

    # ── Offer analysis ────────────────────────────────────────────────────────
    compound_id: str
    offer_normalized_price_sqm: float = Field(
        description="Broker offer's effective cash-equivalent price/sqm after NPV flattening (EGP/m²)."
    )
    offer_cash_npv_egp: float = Field(
        description="Full NPV of the broker offer's payment obligations (EGP)."
    )
    overpay_delta_pct: float = Field(
        description=(
            "Signed delta between offer normalised price/sqm and compound mean. "
            "Positive = overpay; negative = below market."
        )
    )
    is_offer_la2ta: bool = Field(
        description=(
            "True when the submitted offer itself qualifies as a La2ta anomaly "
            "(secondary-market listing ≥ 15 % below compound mean)."
        )
    )

    # ── Compound benchmark ────────────────────────────────────────────────────
    compound_benchmark: CompoundBenchmarkSummary

    # ── La2ta alternatives ────────────────────────────────────────────────────
    la2ta_alternatives_found: int = Field(
        description="Total La2ta listings in this compound available in the database."
    )
    alternatives: list[ArbitrageAlternative]

    # ── Tier metadata ─────────────────────────────────────────────────────────
    is_premium_response: bool = Field(
        description="True when identification fields in alternatives are unmasked."
    )
    rate_limit_remaining: Optional[int] = Field(
        default=None,
        description="Free-tier requests remaining in the current 24-hour window.  Null for subscribers.",
    )
    valuation_note: str = Field(
        description=(
            "Contextual note about the evaluation methodology or data availability."
        )
    )


# ---------------------------------------------------------------------------
# Internal tier resolution context
# ---------------------------------------------------------------------------


@dataclass
class TierContext:
    """
    Resolved authentication and tier state produced by ``verify_tier_clearance``.

    This object is the single source of truth for downstream logic in the
    request pipeline — no additional auth lookups are needed after it is
    resolved.
    """

    is_premium: bool
    """True when the caller is authenticated as a SUBSCRIBER (premium/admin) tier."""

    client_ip: str
    """Canonicalised IP address used as the rate-limit key."""

    user_id: Optional[int] = field(default=None)
    """Database user ID; None for unauthenticated requests."""

    rate_limit_remaining: Optional[int] = field(default=None)
    """
    Requests remaining in the current 24-hour window.
    None for premium callers (no limit applied).
    """


# ---------------------------------------------------------------------------
# Rate-limit helpers
# ---------------------------------------------------------------------------


def _extract_client_ip(request: Request) -> str:
    """
    Extract the canonical client IP from the request.

    Prefers the first value of ``X-Forwarded-For`` (set by reverse proxies /
    Railway ingress) and validates it against a strict IP pattern to prevent
    header injection attacks.  Falls back to ``request.client.host`` if the
    header is absent or fails validation.

    Returns
    -------
    str
        A validated IP address string; ``"unknown"`` if no IP can be resolved
        (should not occur in a properly configured deployment).
    """
    forwarded_for: Optional[str] = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the left-most address (original client; proxies append to the right).
        candidate = forwarded_for.split(",")[0].strip()
        if _IP_PATTERN.match(candidate):
            return candidate

    if request.client and request.client.host:
        return request.client.host

    return "unknown"


def _mem_rate_limit_check(
    client_ip: str,
    limit: int,
    window_seconds: int,
) -> tuple[bool, int, int]:
    """
    In-memory rate-limit counter (Redis fallback).

    Parameters
    ----------
    client_ip : str
    limit : int
        Maximum requests per window.
    window_seconds : int
        Window duration in seconds.

    Returns
    -------
    (exceeded, current_count, ttl_seconds)
        ``exceeded`` is True when the current count **before** this request
        exceeds the limit.  ``ttl_seconds`` is an approximation of seconds
        remaining in the window.
    """
    now = time.monotonic()
    entry = _mem_rl.get(client_ip)

    if entry is None or (now - entry["window_start"]) >= window_seconds:
        _mem_rl[client_ip] = {"count": 1, "window_start": now}
        return False, 1, window_seconds

    entry["count"] += 1
    elapsed = now - entry["window_start"]
    ttl = max(1, int(window_seconds - elapsed))
    exceeded = entry["count"] > limit
    return exceeded, entry["count"], ttl


async def _enforce_rate_limit(
    client_ip: str,
) -> int:
    """
    Apply the freemium Redis rate limit for a free-tier request.

    Increments the per-IP counter and raises HTTP 429 if the limit is
    exceeded.  The ``Retry-After`` header is set to the remaining TTL of
    the rate-limit window.

    Parameters
    ----------
    client_ip : str
        Validated client IP address.

    Returns
    -------
    int
        Remaining requests in the current window (0 means this was the last
        allowed request; the counter has been incremented).

    Raises
    ------
    HTTPException(429)
        When the caller has exceeded ``_FREE_TIER_REQUEST_LIMIT`` requests
        within the current 24-hour window.
    """
    key = f"{_RL_KEY_PREFIX}{client_ip}"
    redis_client = None
    try:
        from app.services.cache import cache
        redis_client = cache.redis
    except Exception as exc:
        logger.warning(
            "Redis cache unavailable for freemium rate limit (%s); "
            "using in-memory fallback (does not survive restarts).", exc
        )

    if redis_client is not None:
        try:
            pipe = redis_client.pipeline()
            pipe.incr(key)
            pipe.ttl(key)
            current, ttl = pipe.execute()
            current = int(current)
            ttl = int(ttl)
            # Set TTL on first increment (key just created) or if TTL was lost.
            if ttl < 0:
                redis_client.expire(key, _RATE_WINDOW_SECONDS)
                ttl = _RATE_WINDOW_SECONDS
        except Exception as exc:
            logger.warning(
                "Redis rate-limit pipeline failed (%s); falling back to memory.", exc
            )
            exceeded, current, ttl = _mem_rate_limit_check(
                client_ip, _FREE_TIER_REQUEST_LIMIT, _RATE_WINDOW_SECONDS
            )
            if exceeded:
                _raise_rate_limit_exceeded(ttl)
            return max(0, _FREE_TIER_REQUEST_LIMIT - current)
    else:
        exceeded, current, ttl = _mem_rate_limit_check(
            client_ip, _FREE_TIER_REQUEST_LIMIT, _RATE_WINDOW_SECONDS
        )
        if exceeded:
            _raise_rate_limit_exceeded(ttl)
        return max(0, _FREE_TIER_REQUEST_LIMIT - current)

    if current > _FREE_TIER_REQUEST_LIMIT:
        _raise_rate_limit_exceeded(ttl)

    return max(0, _FREE_TIER_REQUEST_LIMIT - current)


def _raise_rate_limit_exceeded(retry_after_seconds: int) -> None:
    """Raise a standardised HTTP 429 with a Retry-After header."""
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail={
            "error":       "rate_limit_exceeded",
            "message": (
                "Free tier allows 3 valuation requests per 24-hour window. "
                "Upgrade to SUBSCRIBER for unlimited access."
            ),
            "retry_after_seconds": retry_after_seconds,
        },
        headers={
            "Retry-After":          str(retry_after_seconds),
            "X-RateLimit-Limit":    str(_FREE_TIER_REQUEST_LIMIT),
            "X-RateLimit-Remaining": "0",
        },
    )


# ---------------------------------------------------------------------------
# Tier clearance dependency
# ---------------------------------------------------------------------------


async def verify_tier_clearance(
    request: Request,
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    osool_auth_token: Optional[str] = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
) -> TierContext:
    """
    FastAPI dependency that resolves the caller's subscription tier and
    enforces the free-tier rate limit.

    Token resolution order
    ----------------------
    1. ``Authorization: Bearer <token>`` HTTP header.
    2. ``osool_auth_token`` session cookie (httpOnly, set by the auth flow).

    If neither is present or the token is invalid / blacklisted, the caller
    is treated as an unauthenticated free user (``is_premium=False``) and the
    rate limiter is applied.

    Parameters
    ----------
    request : Request
        Starlette request object (used for IP extraction).
    authorization : Optional[str]
        Raw value of the ``Authorization`` header.
    osool_auth_token : Optional[str]
        Session cookie value.
    db : AsyncSession
        Injected database session.

    Returns
    -------
    TierContext
        Resolved tier context with ``is_premium``, ``client_ip``,
        ``user_id``, and ``rate_limit_remaining``.

    Raises
    ------
    HTTPException(429)
        When a free-tier IP has exhausted its 24-hour request budget.
    """
    client_ip: str = _extract_client_ip(request)

    # ── Token extraction ──────────────────────────────────────────────────────
    raw_token: Optional[str] = None

    if authorization:
        parts = authorization.strip().split(" ", 1)
        if len(parts) == 2 and parts[0].lower() == "bearer":
            raw_token = parts[1].strip()

    if raw_token is None and osool_auth_token:
        raw_token = osool_auth_token.strip()

    # ── Token verification ────────────────────────────────────────────────────
    user_id: Optional[int] = None
    is_premium: bool = False

    if raw_token:
        try:
            from app.auth import verify_token
            from app.models import User
            from sqlalchemy import select as sa_select

            payload = verify_token(raw_token)
            if payload:
                sub = payload.get("sub")
                if sub:
                    result = await db.execute(
                        sa_select(User).where(User.email == str(sub))
                    )
                    user: Optional[User] = result.scalar_one_or_none()
                    if user:
                        user_id = user.id
                        tier = (
                            getattr(user, "subscription_tier", "free") or "free"
                        ).lower().strip()
                        is_premium = tier in _PREMIUM_TIERS
        except Exception as exc:
            # Log at DEBUG: invalid/expired tokens are routine for freemium
            # probes and must not produce 500 errors.
            logger.debug(
                "Token verification failed for freemium request "
                "(client_ip=%s): %s",
                client_ip, exc,
            )
            # Treat as unauthenticated free user — fall through to rate limit.
            is_premium = False

    # ── Rate-limit enforcement (free tier only) ───────────────────────────────
    rate_limit_remaining: Optional[int] = None

    if not is_premium:
        rate_limit_remaining = await _enforce_rate_limit(client_ip)

    return TierContext(
        is_premium=is_premium,
        client_ip=client_ip,
        user_id=user_id,
        rate_limit_remaining=rate_limit_remaining,
    )


# ---------------------------------------------------------------------------
# Offer → PropertyListing construction helpers
# ---------------------------------------------------------------------------


def _build_payment_timeline(offer: BrokerOfferEvaluation) -> PaymentTimeline:
    """
    Construct a ``PaymentTimeline`` from a ``BrokerOfferEvaluation``.

    Even-amortisation model: the residual balance (total − down payment) is
    divided equally across all instalment periods.

    Parameters
    ----------
    offer : BrokerOfferEvaluation
        Validated broker offer input.

    Returns
    -------
    PaymentTimeline
        Pydantic-validated payment schedule suitable for
        ``ValuationEngine.calculate_effective_cash_npv``.

    Raises
    ------
    ValueError
        Re-raised from ``PaymentTimeline`` validation if the derived
        ``periodic_instalment_amount`` is non-positive (should be prevented
        by ``BrokerOfferEvaluation._down_payment_below_total``).
    """
    return PaymentTimeline(
        down_payment=offer.down_payment,
        installments_per_year=offer.annual_installments_count,
        total_years=offer.installment_years,
        periodic_installment_amount=offer.periodic_instalment_amount,
        upfront_cash_discount_pct=0.0,
    )


async def _resolve_compound_zone(
    compound_id: str,
    db: AsyncSession,
) -> str:
    """
    Look up the ``geographic_zone`` for a compound from any stored listing.

    The ``PropertyListing`` schema requires a ``geographic_zone`` label,
    but ``BrokerOfferEvaluation`` does not expose it.  This helper queries
    the valuation listings table for the zone of any existing listing in
    the compound, falling back to a neutral placeholder when none exists.

    Parameters
    ----------
    compound_id : str
        Compound identifier from the submitted offer.
    db : AsyncSession
        Active database session.

    Returns
    -------
    str
        Geographic zone string; ``"Unknown"`` if no listings are found.
    """
    row = (await db.execute(
        text(
            "SELECT geographic_zone FROM valuation_listings "
            "WHERE compound_id = :cid LIMIT 1"
        ),
        {"cid": compound_id},
    )).fetchone()

    return row[0] if row else "Unknown"


def _build_candidate_listing(
    offer: BrokerOfferEvaluation,
    geographic_zone: str,
    payment_timeline: PaymentTimeline,
) -> PropertyListing:
    """
    Construct a ``PropertyListing`` from the broker offer for engine evaluation.

    Structural defaults
    -------------------
    Fields absent from ``BrokerOfferEvaluation`` are set to structurally
    neutral values to isolate the NPV-based price signal from unobserved
    physical characteristics:

    =================== ======================= =============================
    Field               Default                 Rationale
    =================== ======================= =============================
    ``floor_level``     3                       Above ground (no garden
                                                premium) and below elevated
                                                threshold (no high-floor
                                                premium) → zero structural adj.
    ``has_private_garden`` False                Absent; would require floor=0.
    ``view_orientation`` ``side_street``        Zero weight in engine; neutral.
    ``delivery_year``   ``current_year``        Secondary-market = delivered;
                                                lag penalty = 0.
    ``is_secondary_market`` True               Broker resale offer.
    =================== ======================= =============================

    A deterministic ``listing_id`` is derived by hashing
    ``compound_id + stated_total_price + space_sqm`` so re-submissions of
    identical offers produce identical identifiers (idempotent).

    Parameters
    ----------
    offer : BrokerOfferEvaluation
    geographic_zone : str
    payment_timeline : PaymentTimeline

    Returns
    -------
    PropertyListing
        Validated listing ready for ``ValuationEngine.normalize_asset_price_per_sqm``.
    """
    listing_id_source = (
        f"{offer.compound_id}::{offer.stated_total_price:.2f}::{offer.space_sqm:.2f}"
    )
    listing_id = "eval-" + hashlib.sha256(
        listing_id_source.encode("utf-8")
    ).hexdigest()[:16]

    return PropertyListing(
        listing_id=listing_id,
        compound_id=offer.compound_id,
        geographic_zone=geographic_zone,
        total_price=offer.stated_total_price,
        size_sqm=offer.space_sqm,
        floor_level=_DEFAULT_FLOOR_LEVEL,
        has_private_garden=False,
        view_orientation=ViewOrientation.side_street,
        delivery_year=datetime.now(timezone.utc).year,
        current_academic_year=datetime.now(timezone.utc).year,
        is_secondary_market=True,
        payment_timeline=payment_timeline,
    )


# ---------------------------------------------------------------------------
# Compound benchmark query
# ---------------------------------------------------------------------------


async def _query_compound_benchmark(
    compound_id: str,
    db: AsyncSession,
) -> Optional[CompoundBenchmarkSummary]:
    """
    Aggregate secondary-market normalised price statistics for a compound.

    Queries ``valuation_listings`` for all secondary-market rows matching
    ``compound_id`` and returns count, mean, min, and max of
    ``normalized_cash_price_sqm``.

    Parameters
    ----------
    compound_id : str
    db : AsyncSession

    Returns
    -------
    Optional[CompoundBenchmarkSummary]
        ``None`` when fewer than one secondary-market listing exists in the
        compound (insufficient benchmark data for a meaningful mean).
    """
    row = (await db.execute(
        text(
            """
            SELECT
                COUNT(*)                           AS cnt,
                AVG(normalized_cash_price_sqm)     AS mean_sqm,
                MIN(normalized_cash_price_sqm)     AS min_sqm,
                MAX(normalized_cash_price_sqm)     AS max_sqm
            FROM valuation_listings
            WHERE compound_id      = :cid
              AND is_secondary_market = TRUE
            """
        ),
        {"cid": compound_id},
    )).fetchone()

    if not row or not row[0] or row[0] < 1 or row[2] is None:
        return None

    return CompoundBenchmarkSummary(
        compound_id=compound_id,
        secondary_market_listing_count=int(row[0]),
        compound_mean_normalized_sqm=float(row[1]),
        compound_min_normalized_sqm=float(row[2]),
        compound_max_normalized_sqm=float(row[3]),
    )


# ---------------------------------------------------------------------------
# La2ta alternatives query
# ---------------------------------------------------------------------------


async def _query_la2ta_alternatives(
    compound_id: str,
    offer_normalized_sqm: float,
    compound_mean_sqm: float,
    db: AsyncSession,
) -> list[dict[str, Any]]:
    """
    Retrieve La2ta-classified listings in the compound as raw DB row dicts.

    Ordered by ascending ``normalized_cash_price_sqm`` so the cheapest
    alternatives appear first.  Limited to ``_MAX_ALTERNATIVES`` rows to
    bound response size.

    Parameters
    ----------
    compound_id : str
    offer_normalized_sqm : float
        Normalised price/sqm of the evaluated offer (used for savings %).
    compound_mean_sqm : float
        Compound secondary-market mean price/sqm (used for discount depth %).
    db : AsyncSession

    Returns
    -------
    list[dict]
        Each dict contains all columns from ``valuation_listings`` plus
        computed ``savings_vs_offer_pct`` and ``discount_vs_compound_mean_pct``.
    """
    rows = (await db.execute(
        text(
            """
            SELECT
                listing_id,
                compound_id,
                geographic_zone,
                total_price,
                size_sqm,
                floor_level,
                view_orientation,
                delivery_year,
                is_secondary_market,
                cash_npv_egp,
                normalized_cash_price_sqm
            FROM valuation_listings
            WHERE compound_id = :cid
              AND is_la2ta    = TRUE
            ORDER BY normalized_cash_price_sqm ASC
            LIMIT :lim
            """
        ),
        {"cid": compound_id, "lim": _MAX_ALTERNATIVES},
    )).fetchall()

    results: list[dict[str, Any]] = []
    for r in rows:
        norm_sqm = float(r[10])
        savings_vs_offer_pct = (
            (offer_normalized_sqm - norm_sqm) / offer_normalized_sqm * 100.0
            if offer_normalized_sqm > 0 else 0.0
        )
        discount_vs_mean_pct = (
            (compound_mean_sqm - norm_sqm) / compound_mean_sqm * 100.0
            if compound_mean_sqm > 0 else 0.0
        )
        results.append({
            "listing_id":               str(r[0]),
            "compound_id":              str(r[1]),
            "geographic_zone":          str(r[2]),
            "total_price_egp":          float(r[3]),
            "size_sqm":                 float(r[4]),
            "floor_level":              int(r[5]),
            "view_orientation":         str(r[6]),
            "delivery_year":            int(r[7]),
            "is_secondary_market":      bool(r[8]),
            "cash_npv_egp":             float(r[9]),
            "normalized_cash_price_sqm": norm_sqm,
            "savings_vs_offer_pct":     round(savings_vs_offer_pct, 4),
            "discount_vs_compound_mean_pct": round(discount_vs_mean_pct, 4),
        })

    return results


# ---------------------------------------------------------------------------
# Masking engine
# ---------------------------------------------------------------------------


def _build_arbitrage_alternative(
    row: dict[str, Any],
    is_premium: bool,
) -> ArbitrageAlternative:
    """
    Construct an ``ArbitrageAlternative`` response object from a raw DB row dict.

    Applies the masking contract: if ``is_premium`` is ``False``, the three
    identification fields (``broker_direct_contact``, ``building_number``,
    ``exact_unit_id``) are replaced with ``_GATED_SENTINEL``.

    If ``is_premium`` is ``True`` and the underlying DB schema does not
    carry these columns (the current ``valuation_listings`` schema does not),
    structured placeholder values derived from the listing identifier are
    returned.  When the schema is extended to include these columns they
    should be mapped here directly.

    Parameters
    ----------
    row : dict[str, Any]
        Raw query result from ``_query_la2ta_alternatives``.
    is_premium : bool
        True when the caller has SUBSCRIBER-tier access.

    Returns
    -------
    ArbitrageAlternative
    """
    if is_premium:
        # Derive best-available values from the listing identifier.
        # When the schema gains dedicated columns, replace these derivations
        # with direct column reads (e.g. row["broker_direct_contact"]).
        listing_id: str = row["listing_id"]
        broker_contact   = f"Inquire via Osool platform — ref: {listing_id}"
        building_number  = row["compound_id"]
        exact_unit_id    = listing_id
    else:
        broker_contact   = _GATED_SENTINEL
        building_number  = _GATED_SENTINEL
        exact_unit_id    = _GATED_SENTINEL

    return ArbitrageAlternative(
        listing_id                  = row["listing_id"],
        compound_id                 = row["compound_id"],
        geographic_zone             = row["geographic_zone"],
        total_price_egp             = row["total_price_egp"],
        size_sqm                    = row["size_sqm"],
        floor_level                 = row["floor_level"],
        view_orientation            = row["view_orientation"],
        delivery_year               = row["delivery_year"],
        is_secondary_market         = row["is_secondary_market"],
        cash_npv_egp                = row["cash_npv_egp"],
        normalized_cash_price_sqm   = row["normalized_cash_price_sqm"],
        savings_vs_offer_pct        = row["savings_vs_offer_pct"],
        discount_vs_compound_mean_pct = row["discount_vs_compound_mean_pct"],
        broker_direct_contact       = broker_contact,
        building_number             = building_number,
        exact_unit_id               = exact_unit_id,
    )


# ---------------------------------------------------------------------------
# FastAPI Router
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/api/evaluate", tags=["freemium", "valuation"])


class FreeTierHookRequest(BaseModel):
    location_filter: Optional[str] = Field(default=None, max_length=100)
    compound_filter: Optional[str] = Field(default=None, max_length=120)
    language: str = Field(default="ar", pattern="^(ar|en|ar-EG|en-US)$")


@router.post(
    "/free-tier-hook",
    status_code=status.HTTP_200_OK,
    summary="One-record free-tier anomaly teaser",
)
async def free_tier_hook(
    req: FreeTierHookRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    user_tier = (getattr(current_user, "subscription_tier", "free") or "free").lower() if current_user else "anonymous"
    is_premium = user_tier in _PREMIUM_TIERS

    if is_premium:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="free-tier-hook is for anonymous/free flows only",
        )

    hook = await FreeTierConversionGate.extract_one_anomaly(
        db,
        location_filter=req.location_filter,
        compound_filter=req.compound_filter,
    )

    return {
        "is_premium": False,
        "hook_property": hook,
        "value_sandwich": build_value_sandwich(hook, language=req.language),
        "next_step": "Book a physical viewing or developer meeting for full strategy.",
    }


@router.post(
    "/reality-check",
    response_model=RealityCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Broker Offer Reality Check",
    description="""
Evaluate a broker-submitted property offer against compound market data.

**What this endpoint computes**

1. Converts the offer's instalment plan to an NPV-equivalent cash price/sqm
   using the Central Bank of Egypt (CBE) base corridor rate.
2. Compares this normalised price against the compound's secondary-market mean,
   producing a signed overpay delta percentage.
3. Returns up to 10 La2ta-classified alternative listings in the same compound
   that represent potentially better value opportunities.

**Tiered access**

| Tier       | Limit                        | Alternatives payload             |
|------------|------------------------------|----------------------------------|
| Anonymous  | 3 requests / 24 h / IP       | Identification fields masked     |
| Free user  | 3 requests / 24 h / IP       | Identification fields masked     |
| SUBSCRIBER | Unlimited                    | Full identification fields shown |

Authentication is optional.  Provide a valid ``Authorization: Bearer <token>``
header (or the ``osool_auth_token`` session cookie) to unlock the SUBSCRIBER tier.
""",
)
async def broker_offer_reality_check(
    offer: BrokerOfferEvaluation,
    response: Response,
    tier: TierContext = Depends(verify_tier_clearance),
    db: AsyncSession = Depends(get_db),
) -> RealityCheckResponse:
    """
    Evaluate a broker's asking price against compound market intelligence.

    Parameters
    ----------
    offer : BrokerOfferEvaluation
        Validated broker offer payload.
    response : Response
        Starlette response object — used to inject rate-limit headers.
    tier : TierContext
        Resolved tier context from ``verify_tier_clearance``.
    db : AsyncSession
        Injected async database session.

    Returns
    -------
    RealityCheckResponse
        Full evaluation result.  Identification fields in ``alternatives``
        are masked when ``tier.is_premium`` is ``False``.

    Raises
    ------
    HTTPException(422)
        ``BrokerOfferEvaluation`` validation failures are surfaced as
        FastAPI's standard 422 Unprocessable Entity before this handler runs.
    HTTPException(404)
        When the compound has no secondary-market listings in the database
        (insufficient benchmark data to compute a meaningful mean).
    HTTPException(500)
        If the ``ValuationEngine`` raises an unexpected error (e.g. a data
        integrity assertion).  The exception is logged and a generic message
        returned to avoid information leakage.
    """
    # ── Step 1: Add rate-limit headers for free-tier callers ─────────────────
    if not tier.is_premium and tier.rate_limit_remaining is not None:
        response.headers["X-RateLimit-Limit"]     = str(_FREE_TIER_REQUEST_LIMIT)
        response.headers["X-RateLimit-Remaining"] = str(tier.rate_limit_remaining)
        response.headers["X-RateLimit-Window"]    = "86400"

    # ── Step 2: Resolve compound geographic zone from DB ─────────────────────
    geographic_zone = await _resolve_compound_zone(offer.compound_id, db)

    # ── Step 3: Build PaymentTimeline and PropertyListing ────────────────────
    try:
        payment_timeline = _build_payment_timeline(offer)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid payment plan: {exc}",
        ) from exc

    candidate_listing = _build_candidate_listing(
        offer, geographic_zone, payment_timeline
    )

    # ── Step 4: Engine — normalised offer price/sqm ───────────────────────────
    try:
        offer_metrics: NormalizedAssetMetrics = (
            _get_valuation_engine().normalize_asset_price_per_sqm(candidate_listing)
        )
    except (ValueError, AssertionError) as exc:
        logger.exception(
            "ValuationEngine.normalize_asset_price_per_sqm failed for "
            "compound_id=%s: %s",
            offer.compound_id, exc,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Valuation engine encountered an internal error.  "
                   "Please verify your input and try again.",
        ) from exc

    offer_norm_sqm: float = offer_metrics.normalized_price_per_sqm
    offer_cash_npv: float = offer_metrics.cash_npv_egp

    # ── Step 5: Compound benchmark from DB ───────────────────────────────────
    benchmark: Optional[CompoundBenchmarkSummary] = await _query_compound_benchmark(
        offer.compound_id, db
    )

    if benchmark is None:
        # No secondary-market listings indexed for this compound.
        # Return a meaningful 404 rather than a degenerate response.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "insufficient_benchmark_data",
                "compound_id": offer.compound_id,
                "message": (
                    f"Compound '{offer.compound_id}' has no indexed secondary-market "
                    "listings.  A minimum of one secondary-market comparable is required "
                    "to compute a meaningful compound mean price/sqm.  "
                    "Run the ingestion pipeline for this compound first, or try a "
                    "different compound identifier."
                ),
            },
        )

    compound_mean_sqm: float = benchmark.compound_mean_normalized_sqm

    # ── Step 6: Overpay delta and La2ta classification of the offer ───────────
    overpay_delta_pct: float = round(
        (offer_norm_sqm - compound_mean_sqm) / compound_mean_sqm * 100.0,
        4,
    )
    is_offer_la2ta: bool = (
        # Must be secondary market (always True for broker offers in this router)
        candidate_listing.is_secondary_market
        # Must be ≥ _LA2TA_THRESHOLD (15 %) below compound mean
        and offer_norm_sqm <= compound_mean_sqm * (1.0 - _LA2TA_THRESHOLD)
    )

    # ── Step 7: La2ta alternatives in compound ────────────────────────────────
    alt_rows: list[dict[str, Any]] = await _query_la2ta_alternatives(
        offer.compound_id, offer_norm_sqm, compound_mean_sqm, db
    )

    # ── Step 8: Masking engine ────────────────────────────────────────────────
    alternatives: list[ArbitrageAlternative] = [
        _build_arbitrage_alternative(row, tier.is_premium)
        for row in alt_rows
    ]

    # ── Step 9: Compose valuation note ───────────────────────────────────────
    valuation_note = _compose_valuation_note(
        overpay_delta_pct=overpay_delta_pct,
        is_offer_la2ta=is_offer_la2ta,
        la2ta_count=len(alternatives),
        is_premium=tier.is_premium,
        benchmark_count=benchmark.secondary_market_listing_count,
    )

    logger.info(
        "reality-check: compound=%s ip=%s premium=%s "
        "offer_norm_sqm=%.0f mean_sqm=%.0f delta=%.2f%% la2ta=%s alternatives=%d",
        offer.compound_id,
        tier.client_ip,
        tier.is_premium,
        offer_norm_sqm,
        compound_mean_sqm,
        overpay_delta_pct,
        is_offer_la2ta,
        len(alternatives),
    )

    return RealityCheckResponse(
        compound_id                 = offer.compound_id,
        offer_normalized_price_sqm  = round(offer_norm_sqm, 2),
        offer_cash_npv_egp          = round(offer_cash_npv, 2),
        overpay_delta_pct           = overpay_delta_pct,
        is_offer_la2ta              = is_offer_la2ta,
        compound_benchmark          = benchmark,
        la2ta_alternatives_found    = len(alt_rows),
        alternatives                = alternatives,
        is_premium_response         = tier.is_premium,
        rate_limit_remaining        = tier.rate_limit_remaining,
        valuation_note              = valuation_note,
    )


# ---------------------------------------------------------------------------
# Valuation note composition helper
# ---------------------------------------------------------------------------


def _compose_valuation_note(
    overpay_delta_pct: float,
    is_offer_la2ta: bool,
    la2ta_count: int,
    is_premium: bool,
    benchmark_count: int,
) -> str:
    """
    Produce a contextual plain-text note summarising the evaluation result
    and, for free-tier callers, a nudge toward the premium tier.

    Parameters
    ----------
    overpay_delta_pct : float
        Signed delta from compound mean (positive = above market).
    is_offer_la2ta : bool
        Whether the evaluated offer itself qualifies as a La2ta anomaly.
    la2ta_count : int
        Number of La2ta alternatives found in the compound.
    is_premium : bool
        Caller's subscription tier.
    benchmark_count : int
        Number of secondary-market comparables used for the compound mean.

    Returns
    -------
    str
    """
    parts: list[str] = []

    # --- Offer assessment ---
    abs_delta = abs(overpay_delta_pct)
    if overpay_delta_pct > 10:
        parts.append(
            f"This offer is priced {abs_delta:.1f}% above the compound "
            "secondary-market mean — a significant premium."
        )
    elif overpay_delta_pct > 0:
        parts.append(
            f"This offer is {abs_delta:.1f}% above the compound mean — "
            "modest premium; within normal negotiation range."
        )
    elif is_offer_la2ta:
        parts.append(
            f"This offer qualifies as a La2ta (لقطة) opportunity: "
            f"priced {abs_delta:.1f}% below the compound mean — "
            "strong value signal."
        )
    else:
        parts.append(
            f"This offer is {abs_delta:.1f}% below the compound mean — "
            "attractively priced but not yet at La2ta threshold (≥15%)."
        )

    # --- Benchmark confidence ---
    parts.append(
        f"Analysis based on {benchmark_count} secondary-market comparable"
        f"{'s' if benchmark_count != 1 else ''} in this compound."
    )

    # --- Alternatives note ---
    if la2ta_count > 0:
        if is_premium:
            parts.append(
                f"{la2ta_count} La2ta alternative{'s' if la2ta_count != 1 else ''} "
                "with full contact details are available above."
            )
        else:
            parts.append(
                f"{la2ta_count} La2ta alternative{'s' if la2ta_count != 1 else ''} "
                "identified — upgrade to SUBSCRIBER to unlock broker contacts, "
                "building numbers, and exact unit IDs."
            )
    else:
        parts.append(
            "No La2ta alternatives currently indexed for this compound."
        )

    return "  ".join(parts)
