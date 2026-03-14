"""
Analytics Endpoints — Dual-Engine Dashboard Data
---------------------------------------------------
Aggregated analytics: traffic, leads, conversions, pipeline.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from typing import Optional
from datetime import datetime, timedelta
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
    """Main dashboard KPIs."""
    now = datetime.utcnow()
    last_30d = now - timedelta(days=30)
    last_7d = now - timedelta(days=7)

    total_users = (await db.execute(select(func.count(User.id)))).scalar()
    new_users_30d = (await db.execute(
        select(func.count(User.id)).where(User.created_at >= last_30d)
    )).scalar()

    total_leads = (await db.execute(select(func.count(LeadProfile.id)))).scalar()
    hot_leads = (await db.execute(
        select(func.count(LeadProfile.id)).where(LeadProfile.score >= 70)
    )).scalar()

    total_intents_7d = (await db.execute(
        select(func.count(ChatIntent.id)).where(ChatIntent.created_at >= last_7d)
    )).scalar()

    total_emails = (await db.execute(select(func.count(EmailEvent.id)))).scalar()

    total_projects = (await db.execute(select(func.count(SEOProject.id)))).scalar()

    waitlist = (await db.execute(select(func.count(WaitlistEntry.id)))).scalar()

    return {
        "users": {"total": total_users, "new_30d": new_users_30d},
        "leads": {"total": total_leads, "hot": hot_leads},
        "intents_7d": total_intents_7d,
        "emails_sent": total_emails,
        "projects_listed": total_projects,
        "waitlist_entries": waitlist,
    }


# ═══════════════════════════════════════════════════════════════
# LEAD FUNNEL
# ═══════════════════════════════════════════════════════════════

@router.get("/funnel")
async def lead_funnel(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Lead pipeline funnel breakdown."""
    stages = (await db.execute(
        select(LeadProfile.stage, func.count(LeadProfile.id))
        .group_by(LeadProfile.stage)
    )).all()

    funnel_order = ["new", "engaged", "hot", "qualified", "converted", "lost"]
    stage_map = {s: c for s, c in stages if s}

    return {
        "funnel": [
            {"stage": s, "count": stage_map.get(s, 0)}
            for s in funnel_order
        ],
        "total": sum(stage_map.values()),
    }


# ═══════════════════════════════════════════════════════════════
# INTENT TRENDS
# ═══════════════════════════════════════════════════════════════

@router.get("/intent-trends")
async def intent_trends(
    days: int = Query(30, ge=1, le=365),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Daily intent counts over past N days."""
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
    return [
        {"date": str(day), "intent_type": str(it), "count": c}
        for day, it, c in rows
    ]


# ═══════════════════════════════════════════════════════════════
# MARKET SNAPSHOT
# ═══════════════════════════════════════════════════════════════

@router.get("/market-snapshot")
async def market_snapshot(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Latest price data per area."""
    from app.models import Area

    areas = (await db.execute(select(Area).order_by(Area.name))).scalars().all()
    snapshot = []
    for area in areas:
        latest = await db.execute(
            select(PriceHistory)
            .where(PriceHistory.area_id == area.id)
            .order_by(PriceHistory.date.desc())
            .limit(1)
        )
        ph = latest.scalar_one_or_none()
        snapshot.append({
            "area": area.name,
            "slug": area.slug,
            "avg_price_per_meter": ph.price_per_m2 if ph else area.avg_price_per_meter,
            "price_growth_ytd": area.price_growth_ytd,
            "rental_yield": area.rental_yield,
        })
    return snapshot
