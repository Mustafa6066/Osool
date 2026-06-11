"""
Paid Report Service
-------------------
Generates and delivers one-time purchased AI reports.

Fired by the Paymob webhook (asyncio.create_task) after a 'report'
transaction is confirmed. Self-contained: opens its own DB session so it
can run outside the webhook's request scope.

Pipeline:
  PaidReport(status='paid')
    → gather user prefs + market indicators + matching properties
    → generate_investment_report() (existing bilingual Claude generator)
    → store content_json, mark delivered
    → email the buyer a dashboard download link

The report renders as a print-optimized bilingual page in the web app
(/reports/[id]); pdf_url stays reserved for future server-side PDFs.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models import MarketIndicator, PaidReport, Property, User

logger = logging.getLogger(__name__)

_FRONTEND_URL = os.getenv("FRONTEND_URL", "https://osool-ten.vercel.app")


async def _gather_market_data(db) -> list[dict]:
    rows = (await db.execute(select(MarketIndicator))).scalars().all()
    return [
        {"indicator": r.key, "value": r.value, "source": r.source}
        for r in rows
    ]


async def _gather_matching_projects(db, params: dict) -> list[dict]:
    """Top properties matching the buyer's saved criteria (budget/areas/types)."""
    stmt = select(Property).where(Property.is_available.is_(True))

    budget_min = params.get("budget_min")
    budget_max = params.get("budget_max")
    if budget_min:
        stmt = stmt.where(Property.price >= float(budget_min))
    if budget_max:
        stmt = stmt.where(Property.price <= float(budget_max))

    areas = params.get("areas") or []
    if areas:
        from sqlalchemy import or_
        stmt = stmt.where(or_(*[Property.location.ilike(f"%{a}%") for a in areas]))

    property_id = params.get("property_id")
    if property_id:
        stmt = stmt.where(Property.id == int(property_id))

    stmt = stmt.order_by(Property.price_per_sqm.asc().nullslast()).limit(10)
    rows = (await db.execute(stmt)).scalars().all()
    return [
        {
            "title": p.title,
            "compound": p.compound,
            "developer": p.developer,
            "location": p.location,
            "type": p.type,
            "price_egp": p.price,
            "price_per_sqm": p.price_per_sqm,
            "size_sqm": p.size_sqm,
            "bedrooms": p.bedrooms,
            "delivery_date": p.delivery_date,
            "sale_type": p.sale_type,
        }
        for p in rows
    ]


async def generate_and_deliver_report(report_id: int) -> bool:
    """
    Generate the purchased report and mark it delivered.
    Returns True on success; on failure marks the report 'failed'.
    """
    async with AsyncSessionLocal() as db:
        report = (
            await db.execute(select(PaidReport).where(PaidReport.id == report_id))
        ).scalar_one_or_none()
        if not report:
            logger.error("[paid-report] Report %s not found", report_id)
            return False
        if report.status == "delivered":
            return True

        report.status = "generating"
        await db.commit()

        try:
            params = json.loads(report.input_params_json or "{}")
            market_data = await _gather_market_data(db)
            projects = await _gather_matching_projects(db, params)

            from app.ai_engine.report_generator import generate_investment_report

            content = await generate_investment_report(
                budget_min=int(params.get("budget_min") or 0),
                budget_max=int(params.get("budget_max") or 0),
                areas=params.get("areas") or [],
                types=params.get("types") or [],
                bedrooms=params.get("bedrooms"),
                timeline=params.get("timeline"),
                market_data=market_data,
                projects=projects,
            )

            report.content_json = json.dumps(content, ensure_ascii=False)
            report.status = "delivered"
            report.delivered_at = datetime.now(timezone.utc)
            await db.commit()

            # Notify the buyer (best-effort)
            try:
                user = (
                    await db.execute(select(User).where(User.id == report.user_id))
                ).scalar_one_or_none()
                if user:
                    from app.services.email_service import email_service
                    title = (
                        content.get("en", {}).get("title")
                        or "Your Osool Investment Report"
                    )
                    email_service.send_report_ready(
                        user.email,
                        report_title=title,
                        dashboard_url=f"{_FRONTEND_URL}/dashboard",
                    )
            except Exception as mail_err:
                logger.warning("[paid-report] Ready email failed (non-fatal): %s", mail_err)

            logger.info("[paid-report] Report %s delivered", report_id)
            return True

        except Exception as exc:
            logger.error("[paid-report] Generation failed for %s: %s", report_id, exc)
            report.status = "failed"
            await db.commit()

            # Alert operators — a customer paid and didn't get their product
            try:
                from app.ingestion.anomaly_detector import send_alert
                await send_alert(
                    title=f"Paid report {report_id} FAILED",
                    message=(
                        f"User {report.user_id} paid {report.amount_egp:.0f} EGP for "
                        f"report {report_id} but generation failed: {exc}"
                    ),
                    severity="critical",
                )
            except Exception:
                pass
            return False
