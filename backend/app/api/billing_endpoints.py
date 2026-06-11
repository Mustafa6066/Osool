"""
Billing Endpoints — Osool Pro subscription & one-time paid reports
-------------------------------------------------------------------
Wires the existing freemium gate (User.subscription_tier) to real Paymob
payments:

  GET  /api/billing/plans                  → public plan/pricing catalog (ar/en)
  POST /api/billing/subscribe              → Paymob iframe for Osool Pro
  POST /api/billing/purchase-report        → Paymob iframe for a one-time report
  GET  /api/billing/status                 → caller's tier, subscription, reports
  GET  /api/billing/reports/{id}/download  → delivered report payload/PDF link

Payment confirmation happens exclusively in the Paymob webhook
(endpoints.py /webhook/paymob), which branches on Transaction.transaction_type.
The success-page frontend polls GET /status until the webhook lands.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.config import config
from app.database import get_db
from app.models import PaidReport, Subscription, Transaction, User
from app.services.paymob_service import paymob_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/billing", tags=["billing"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ReportPurchaseRequest(BaseModel):
    report_type: str = Field(default="valuation", pattern="^(valuation)$")
    property_id: Optional[int] = None
    params: Optional[dict] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _payments_enabled_or_503() -> None:
    if not config.PAYMENTS_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="Payments are temporarily unavailable. Please try again later.",
        )


def _split_name(full_name: Optional[str]) -> tuple[str, str]:
    parts = (full_name or "Osool User").strip().split(" ", 1)
    return parts[0], (parts[1] if len(parts) > 1 else "User")


async def _initiate_paymob(user: User, amount_egp: float) -> dict:
    first, last = _split_name(getattr(user, "full_name", None))
    result = await paymob_service.initiate_payment(
        amount_egp=amount_egp,
        user_email=user.email,
        user_phone=getattr(user, "phone_number", None) or "+201000000000",
        first_name=first,
        last_name=last,
    )
    if "error" in result:
        raise HTTPException(status_code=502, detail=result["error"])
    return result


async def _active_subscription(db: AsyncSession, user_id: int) -> Optional[Subscription]:
    result = await db.execute(
        select(Subscription)
        .where(Subscription.user_id == user_id, Subscription.status == "active")
        .order_by(Subscription.current_period_end.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/plans")
async def get_plans():
    """Public pricing catalog. Bilingual copy so /pricing renders from one call."""
    return {
        "currency": "EGP",
        "payments_enabled": config.PAYMENTS_ENABLED,
        "plans": [
            {
                "id": "free",
                "price_egp": 0,
                "period": "forever",
                "name": {"en": "Free", "ar": "مجاني"},
                "features": {
                    "en": [
                        "3 Reality Checks per day",
                        "AI property matching",
                        "Market & area insights",
                        "Mortgage calculator",
                    ],
                    "ar": [
                        "٣ فحوصات حقيقية يوميًا",
                        "مطابقة عقارات بالذكاء الاصطناعي",
                        "تحليلات السوق والمناطق",
                        "حاسبة التمويل العقاري",
                    ],
                },
            },
            {
                "id": "pro_monthly",
                "price_egp": config.OSOOL_PRO_MONTHLY_EGP,
                "period": "month",
                "name": {"en": "Osool Pro", "ar": "أصول برو"},
                "features": {
                    "en": [
                        "Unlimited Reality Checks",
                        "Unmasked broker contacts & unit IDs",
                        "Unlimited AI advisor chat",
                        "Price-drop & La2ta alerts",
                        "Pro affordability analysis",
                    ],
                    "ar": [
                        "فحوصات حقيقية بلا حدود",
                        "بيانات السماسرة والوحدات كاملة",
                        "محادثة غير محدودة مع المستشار الذكي",
                        "تنبيهات انخفاض الأسعار واللقطات",
                        "تحليل القدرة الشرائية الاحترافي",
                    ],
                },
            },
            {
                "id": "valuation_report",
                "price_egp": config.VALUATION_REPORT_EGP,
                "period": "one_time",
                "name": {"en": "AI Valuation Report", "ar": "تقرير التقييم الذكي"},
                "features": {
                    "en": [
                        "Personalized bilingual PDF report",
                        "Fair-value analysis with reasoning",
                        "Top matching projects & ROI estimates",
                        "Delivered by email + dashboard",
                    ],
                    "ar": [
                        "تقرير PDF شخصي بالعربية والإنجليزية",
                        "تحليل القيمة العادلة مع الأسباب",
                        "أفضل المشاريع المطابقة وتقديرات العائد",
                        "يصل عبر البريد ولوحة التحكم",
                    ],
                },
            },
        ],
    }


@router.post("/subscribe")
async def subscribe(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start an Osool Pro purchase: Paymob order + pending Subscription."""
    _payments_enabled_or_503()

    from app.api.freemium_router import _tier_is_premium
    if _tier_is_premium(current_user):
        raise HTTPException(status_code=409, detail="You already have an active Osool Pro subscription.")
    if await _active_subscription(db, current_user.id):
        raise HTTPException(status_code=409, detail="You already have an active Osool Pro subscription.")

    amount = config.OSOOL_PRO_MONTHLY_EGP
    paymob = await _initiate_paymob(current_user, amount)
    order_id = str(paymob.get("order_id"))

    transaction = Transaction(
        user_id=current_user.id,
        property_id=None,
        amount=amount,
        currency="EGP",
        transaction_type="subscription",
        status="pending",
        paymob_order_id=order_id,
    )
    db.add(transaction)
    await db.flush()

    subscription = Subscription(
        user_id=current_user.id,
        plan="pro_monthly",
        status="pending",
        amount_egp=amount,
        paymob_order_id=order_id,
        transaction_id=transaction.id,
    )
    db.add(subscription)
    await db.commit()

    logger.info(
        "Billing: subscription order %s created for user %s (%.0f EGP)",
        order_id, current_user.id, amount,
    )
    return {
        "order_id": order_id,
        "iframe_url": paymob["iframe_url"],
        "amount_egp": amount,
        "plan": "pro_monthly",
    }


@router.post("/purchase-report")
async def purchase_report(
    req: ReportPurchaseRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start a one-time report purchase: Paymob order + pending PaidReport."""
    _payments_enabled_or_503()

    amount = config.VALUATION_REPORT_EGP
    paymob = await _initiate_paymob(current_user, amount)
    order_id = str(paymob.get("order_id"))

    transaction = Transaction(
        user_id=current_user.id,
        property_id=req.property_id,
        amount=amount,
        currency="EGP",
        transaction_type="report",
        status="pending",
        paymob_order_id=order_id,
    )
    db.add(transaction)
    await db.flush()

    report = PaidReport(
        user_id=current_user.id,
        report_type=req.report_type,
        status="pending",
        input_params_json=json.dumps(
            {"property_id": req.property_id, **(req.params or {})}, ensure_ascii=False
        ),
        amount_egp=amount,
        paymob_order_id=order_id,
        transaction_id=transaction.id,
    )
    db.add(report)
    await db.commit()

    logger.info(
        "Billing: report order %s created for user %s (%.0f EGP)",
        order_id, current_user.id, amount,
    )
    return {
        "order_id": order_id,
        "iframe_url": paymob["iframe_url"],
        "amount_egp": amount,
        "report_type": req.report_type,
    }


@router.get("/status")
async def billing_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Caller's current tier + subscription + purchased reports (success page polls this)."""
    subscription = await _active_subscription(db, current_user.id)

    reports_result = await db.execute(
        select(PaidReport)
        .where(PaidReport.user_id == current_user.id)
        .order_by(PaidReport.created_at.desc())
        .limit(20)
    )
    reports = reports_result.scalars().all()

    return {
        "tier": (getattr(current_user, "subscription_tier", "free") or "free").lower(),
        "subscription": (
            {
                "plan": subscription.plan,
                "status": subscription.status,
                "current_period_end": (
                    subscription.current_period_end.isoformat()
                    if subscription.current_period_end else None
                ),
                "amount_egp": subscription.amount_egp,
            }
            if subscription else None
        ),
        "reports": [
            {
                "id": r.id,
                "report_type": r.report_type,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "delivered_at": r.delivered_at.isoformat() if r.delivered_at else None,
                "pdf_url": r.pdf_url if r.status == "delivered" else None,
            }
            for r in reports
        ],
    }


@router.get("/reports/{report_id}/download")
async def download_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the delivered report content/PDF link (owner only)."""
    result = await db.execute(
        select(PaidReport).where(
            PaidReport.id == report_id, PaidReport.user_id == current_user.id
        )
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if report.status != "delivered":
        raise HTTPException(
            status_code=409,
            detail=f"Report is not ready yet (status: {report.status}).",
        )

    return {
        "id": report.id,
        "report_type": report.report_type,
        "pdf_url": report.pdf_url,
        "content": json.loads(report.content_json) if report.content_json else None,
        "delivered_at": report.delivered_at.isoformat() if report.delivered_at else None,
    }
