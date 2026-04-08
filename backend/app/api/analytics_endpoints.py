"""
Analytics Endpoints — Dual-Engine Dashboard Data
---------------------------------------------------
Aggregated analytics: traffic, leads, conversions, pipeline.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from typing import Optional
from datetime import datetime, timedelta
import json
import logging

from app.auth import get_current_user
from app.database import get_db
from app.models import (
    User, LeadProfile, ChatIntent, EmailEvent, SEOProject,
    WaitlistEntry, Report, PriceHistory,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


# ═══════════════════════════════════════════════════════════════
# ADMIN GUARD
# ═══════════════════════════════════════════════════════════════

OWNER_EMAIL = "mustafa@osool.eg"
HANI_EMAIL = "hani@osool.eg"


async def require_admin(user: User = Depends(get_current_user)) -> User:
    if not user or not user.email:
        raise HTTPException(status_code=401, detail="Authentication required")
    email = user.email.strip().lower()
    role = (getattr(user, 'role', '') or '').strip().lower()
    if email in {OWNER_EMAIL, HANI_EMAIL} or role == 'admin':
        return user
    raise HTTPException(status_code=403, detail="Admin access required")


# ═══════════════════════════════════════════════════════════════
# DASHBOARD OVERVIEW
# ═══════════════════════════════════════════════════════════════

@router.get("/dashboard")
async def dashboard_overview(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Main dashboard KPIs — flat shape expected by the frontend."""
    now = datetime.utcnow()
    last_7d = now - timedelta(days=7)

    total_leads = (await db.execute(select(func.count(LeadProfile.id)))).scalar() or 0
    new_leads_7d = (await db.execute(
        select(func.count(LeadProfile.id)).where(LeadProfile.created_at >= last_7d)
    )).scalar() or 0
    hot_leads = (await db.execute(
        select(func.count(LeadProfile.id)).where(LeadProfile.score >= 70)
    )).scalar() or 0

    total_intents = (await db.execute(select(func.count(ChatIntent.id)))).scalar() or 0
    avg_confidence = (await db.execute(
        select(func.avg(ChatIntent.confidence))
    )).scalar() or 0.0

    total_emails = (await db.execute(select(func.count(EmailEvent.id)))).scalar() or 0
    emails_opened = (await db.execute(
        select(func.count(EmailEvent.id)).where(EmailEvent.status == "opened")
    )).scalar() or 0
    open_rate = (emails_opened / total_emails) if total_emails > 0 else 0.0

    return {
        "total_leads": total_leads,
        "new_leads_7d": new_leads_7d,
        "hot_leads": hot_leads,
        "total_intents": total_intents,
        "avg_confidence": avg_confidence,
        "emails_sent": total_emails,
        "emails_opened": emails_opened,
        "open_rate": open_rate,
    }


# ═══════════════════════════════════════════════════════════════
# LEAD FUNNEL
# ═══════════════════════════════════════════════════════════════

@router.get("/funnel")
async def lead_funnel(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Lead pipeline funnel breakdown — returns flat array of {stage, count}."""
    stages = (await db.execute(
        select(LeadProfile.stage, func.count(LeadProfile.id))
        .group_by(LeadProfile.stage)
    )).all()

    funnel_order = ["new", "engaged", "hot", "qualified", "converted", "lost"]
    stage_map = {s: c for s, c in stages if s}

    return [
        {"stage": s, "count": stage_map.get(s, 0)}
        for s in funnel_order
    ]


# ═══════════════════════════════════════════════════════════════
# INTENT TRENDS
# ═══════════════════════════════════════════════════════════════

@router.get("/intent-trends")
async def intent_trends(
    days: int = Query(30, ge=1, le=365),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Daily intent counts pivoted by type."""
    since = datetime.utcnow() - timedelta(days=days)
    result = await db.execute(
        select(
            func.date(ChatIntent.created_at).label("day"),
            ChatIntent.intent_type,
            func.count(ChatIntent.id),
        )
        .where(ChatIntent.created_at >= since)
        .group_by("day", ChatIntent.intent_type)
        .order_by("day")
    )
    rows = result.all()

    # Pivot into {date, SEARCH, COMPARE, PURCHASE, VALUATION, GENERAL}
    from collections import OrderedDict
    intent_types = ["SEARCH", "COMPARE", "PURCHASE", "VALUATION", "GENERAL"]
    day_map: dict = OrderedDict()
    for day, it, c in rows:
        d = str(day)
        if d not in day_map:
            day_map[d] = {"date": d, **{t: 0 for t in intent_types}}
        key = str(it).upper() if it else "GENERAL"
        if key in day_map[d]:
            day_map[d][key] = c
    return list(day_map.values())


# ═══════════════════════════════════════════════════════════════
# MARKET SNAPSHOT
# ═══════════════════════════════════════════════════════════════

@router.get("/market-snapshot")
async def market_snapshot(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Aggregated market snapshot for the dashboard."""
    from app.models import Area

    # Top searched areas (from chat intents mentioning areas, or fall back to areas by search count)
    top_areas_result = await db.execute(
        select(Area.name, Area.avg_price_per_meter)
        .order_by(Area.avg_price_per_meter.desc())
        .limit(5)
    )
    top_areas = [
        {"area": name, "count": int(price or 0)}
        for name, price in top_areas_result.all()
    ]

    # Average budget from lead profiles
    budget = await db.execute(
        select(func.avg(LeadProfile.budget_min), func.avg(LeadProfile.budget_max))
    )
    budget_row = budget.one()
    avg_budget_min = float(budget_row[0] or 0)
    avg_budget_max = float(budget_row[1] or 0)

    # Top intent type
    top_intent_result = await db.execute(
        select(ChatIntent.intent_type, func.count(ChatIntent.id).label("cnt"))
        .group_by(ChatIntent.intent_type)
        .order_by(func.count(ChatIntent.id).desc())
        .limit(1)
    )
    top_intent_row = top_intent_result.first()
    top_intent = str(top_intent_row[0]) if top_intent_row else "N/A"

    # Total interactions
    total_interactions = (await db.execute(select(func.count(ChatIntent.id)))).scalar() or 0

    return {
        "top_areas": top_areas,
        "avg_budget_min": avg_budget_min,
        "avg_budget_max": avg_budget_max,
        "top_intent": top_intent,
        "total_interactions": total_interactions,
    }


# ═══════════════════════════════════════════════════════════════
# WEB VITALS TELEMETRY (sendBeacon — no auth, CSRF-exempt)
# ═══════════════════════════════════════════════════════════════

@router.post("/web-vitals", status_code=204)
async def ingest_web_vitals(request: Request):
    """
    Accept Core Web Vitals metrics sent via navigator.sendBeacon.
    sendBeacon sends JSON as text/plain, so we read the raw body
    and parse manually. No auth required — telemetry only.
    Returns 204 No Content.
    """
    try:
        raw = await request.body()
        if not raw:
            return Response(status_code=204)
        payload = json.loads(raw)
        name = payload.get("name", "UNKNOWN")
        value = payload.get("value", 0)
        rating = payload.get("rating", "unknown")
        logger.info("[web-vitals] %s=%.2f rating=%s", name, float(value), rating)
    except Exception:
        # Never 500 on telemetry — swallow and return 204
        pass
    return Response(status_code=204)
