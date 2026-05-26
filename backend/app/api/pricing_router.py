"""
pricing_router.py
=================
HTTP surface for the v1 buyer haggle engine.

* POST /api/pricing/analyze
    Returns a free-tier or premium-tier slice of HaggleRange depending on
    the caller's subscription_tier. Account required (auth is enforced).

* POST /api/pricing/report.pdf  (premium only)
    Stub — returns 501 until the PDF renderer ships.

Design notes
------------
* Zero LLM tokens on the free path (negotiation_engine + haggle_template).
* Wolf narration is premium-only and handled by the chat router, NOT here.
* The free-vs-premium decision lives in _slice_for_tier(). Single source of
  truth — if you change the boundary, change it there.
"""
from __future__ import annotations

import logging
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.middleware.rate_limiting import limiter
from app.models import User
from app.services.haggle_template import render_both
from app.services.negotiation_engine import (
    HaggleComp,
    HaggleLever,
    HaggleRange,
    compute_haggle_range,
)
from app.services.subscription_engine import TierResolution, resolve_access

_logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/pricing", tags=["pricing"])


# ---------------------------------------------------------------------------
# Tier resolution — delegated to subscription_engine
# ---------------------------------------------------------------------------
# resolve_access(user, compound) is the single source of truth. It returns
# a TierResolution with tier + reason + expiry metadata so the response can
# surface meaningful upsell prompts (e.g. "your pass for X expired 3 days
# ago" vs "your pass unlocks X, not Y").


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------


class AnalyzeRequest(BaseModel):
    compound: str = Field(
        ...,
        description=(
            "Canonical compound name as it appears in the properties table "
            "(e.g. 'Mountain View Hyde Park'). Frontend maps URL slugs to "
            "this canonical name before calling the API."
        ),
    )
    property_type: str = Field("apartment", description="apartment|villa|townhouse|duplex|penthouse|studio")
    size_sqm: float = Field(..., gt=10, lt=5000)
    bedrooms: int = Field(..., ge=0, le=10)
    listing_price_egp: Optional[float] = Field(
        None, gt=0, description="Optional — supply to get a verdict vs market"
    )
    developer_id: Optional[str] = None
    area_id: Optional[str] = None
    language: Literal["en", "ar", "both"] = "both"


class AccessInfo(BaseModel):
    """Surfaces WHY the user got their tier — used by the UI for tailored upsell."""
    tier: Literal["free", "premium"]
    reason: str = Field(
        ...,
        description=(
            "free_default | single_compound_match | single_compound_mismatch | "
            "single_compound_expired | premium_monthly_active | premium_monthly_expired | "
            "legacy_premium | admin"
        ),
    )
    expires_at: Optional[str] = Field(
        None, description="ISO 8601 if the tier has an expiry; otherwise None."
    )
    days_until_expiry: Optional[int] = None
    unlocked_compound: Optional[str] = Field(
        None,
        description=(
            "For single_compound_mismatch responses: the compound the user "
            "ALREADY has access to, so the UI can offer a one-click switch."
        ),
    )


class AnalyzeResponse(BaseModel):
    tier: Literal["free", "premium"]
    access: AccessInfo
    haggle: HaggleRange
    verdict: dict[str, str] = Field(
        default_factory=dict,
        description="Bilingual one-liner verdict ({'en': ..., 'ar': ...})",
    )
    upsell: Optional["UpsellHint"] = None


class UpsellHint(BaseModel):
    """Sent on free-tier responses to advertise what premium unlocks."""
    comps_locked_count: int
    report_locked: bool = True
    alerts_locked: bool = True
    coach_locked: bool = True
    trend_chart_locked: bool = True
    sku_options: list["UpsellSku"]
    headline_en: str = Field(
        "Unlock the comps, levers, and coach.",
        description="Variant copy chosen by reason (expired vs mismatch vs default).",
    )
    headline_ar: str = Field("افتح الأرقام كاملة، الأدوات، والمستشار.")


class UpsellSku(BaseModel):
    sku: Literal["single_compound", "premium_monthly"]
    price_egp: int
    label_en: str
    label_ar: str


AnalyzeResponse.model_rebuild()


def _access_info_from(resolution: TierResolution) -> AccessInfo:
    return AccessInfo(
        tier=resolution.tier,
        reason=resolution.reason,
        expires_at=(
            resolution.expires_at.isoformat() if resolution.expires_at else None
        ),
        days_until_expiry=resolution.days_until_expiry,
        unlocked_compound=resolution.unlocked_compound,
    )


# ---------------------------------------------------------------------------
# Free-vs-premium slicer (single source of truth for the boundary)
# ---------------------------------------------------------------------------


def _slice_for_tier(
    full: HaggleRange,
    tier: Literal["free", "premium"],
) -> HaggleRange:
    """
    Apply the LOCKED v1 free/premium boundary to a HaggleRange.

    Free: fair_range + verdict + 1 partially-masked comp + confidence tier.
    Premium: everything (the input is returned unchanged).

    See the launch narrative for the rationale behind each masked field.
    """
    if tier == "premium":
        return full

    # ── FREE TIER ────────────────────────────────────────────────────────
    # Drop the lever breakdown (premium only)
    sliced_levers: list[HaggleLever] = []

    # Show ONE comp with closing_price_egp masked
    sliced_comps: list[HaggleComp] = []
    if full.comps:
        # Pick the median-priced comp as the representative — least sensational
        sorted_comps = sorted(
            full.comps,
            key=lambda c: (c.closing_price_egp or 0),
        )
        median_idx = len(sorted_comps) // 2
        representative = sorted_comps[median_idx]
        sliced_comps = [
            representative.model_copy(
                update={"closing_price_egp": None, "masked": True}
            )
        ]

    return full.model_copy(
        update={
            "levers": sliced_levers,
            "comps": sliced_comps,
            # Trace fields stripped on free tier to avoid leaking weights
            "constants_resolved": {},
            "notes": [],
        }
    )


def _build_upsell(full: HaggleRange, access: TierResolution) -> UpsellHint:
    """
    Generate the upsell hint shown to free-tier callers.

    Headline copy varies by why they're free:
      * single_compound_mismatch → "You unlocked X; this is Y"
      * single_compound_expired  → "Your pass for X expired — renew"
      * premium_monthly_expired  → "Your unlimited expired — renew"
      * everyone else            → default upsell
    """
    headline_en = "Unlock the comps, levers, and coach."
    headline_ar = "افتح الأرقام كاملة، الأدوات، والمستشار."

    if access.reason == "single_compound_mismatch" and access.unlocked_compound:
        headline_en = (
            f"Your pass unlocks {access.unlocked_compound}. "
            f"Buy a pass for this one too, or go unlimited."
        )
        headline_ar = (
            f"اشتراكك يفتح {access.unlocked_compound}. "
            f"اشتري باقة للكمبوند ده، أو ارتقي للاشتراك الكامل."
        )
    elif access.reason == "single_compound_expired":
        headline_en = "Your single-compound pass expired. Renew to keep access."
        headline_ar = "باقة الكمبوند انتهت. جدد للحفاظ على الاطلاع."
    elif access.reason == "premium_monthly_expired":
        headline_en = "Your unlimited subscription expired. Resubscribe to continue."
        headline_ar = "اشتراكك الكامل انتهى. جدد للمتابعة."

    return UpsellHint(
        comps_locked_count=max(0, len(full.comps) - 1),
        sku_options=[
            UpsellSku(
                sku="single_compound",
                price_egp=99,
                label_en="This compound, 30 days — EGP 99",
                label_ar="هذا الكمبوند، 30 يوم — 99 جنيه",
            ),
            UpsellSku(
                sku="premium_monthly",
                price_egp=299,
                label_en="All compounds, monthly — EGP 299/mo",
                label_ar="كل الكمبوندات، شهرياً — 299 جنيه/شهر",
            ),
        ],
        headline_en=headline_en,
        headline_ar=headline_ar,
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post("/analyze", response_model=AnalyzeResponse)
@limiter.limit("250/day")
async def analyze_compound_price(
    body: AnalyzeRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AnalyzeResponse:
    """
    Compute the fair-value range + verdict for a compound + property combination.

    Account required (the free path is NOT anonymous — see plan revision 3).
    Rate limit: 250/day per authed free user. Premium gets the same decorator
    here; per-tier scaling moves to middleware in a follow-up.
    """
    full = await compute_haggle_range(
        db,
        compound=body.compound,
        property_type=body.property_type,
        size_sqm=body.size_sqm,
        bedrooms=body.bedrooms,
        listing_price_egp=body.listing_price_egp,
        developer_id=body.developer_id,
        area_id=body.area_id,
    )

    access = resolve_access(user, body.compound)
    sliced = _slice_for_tier(full, access.tier)

    verdict = render_both(sliced)
    if body.language == "en":
        verdict = {"en": verdict["en"]}
    elif body.language == "ar":
        verdict = {"ar": verdict["ar"]}

    return AnalyzeResponse(
        tier=access.tier,
        access=_access_info_from(access),
        haggle=sliced,
        verdict=verdict,
        upsell=_build_upsell(full, access) if access.tier == "free" else None,
    )


class ReportRequest(BaseModel):
    compound: str
    property_type: str = "apartment"


@router.post("/report.pdf")
@limiter.limit("20/day")
async def generate_pdf_report(
    body: ReportRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Premium-only PDF report. Honors single_compound scope: a user with the
    EGP 99 SKU for compound X can download reports for X, not for Y.
    Stub until the PDF renderer ships.
    """
    access = resolve_access(user, body.compound)
    if access.tier != "premium":
        # subscription_engine builds bilingual 402 detail for us
        from app.services.subscription_engine import _payment_required_detail
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=_payment_required_detail(access, body.compound),
        )
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="PDF report generation lands in a follow-up PR.",
    )
