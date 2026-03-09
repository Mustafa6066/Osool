"""
Campaign & Waitlist Endpoints
---------------------------------
Ad campaign tracking, retargeting rules, and waitlist signups.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
import logging

from app.auth import get_current_user
from app.database import get_db
from app.models import User, AdCampaign, RetargetingRule, WaitlistEntry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/campaigns", tags=["Campaigns & Waitlist"])


# ═══════════════════════════════════════════════════════════════
# SCHEMAS
# ═══════════════════════════════════════════════════════════════

class CampaignOut(BaseModel):
    id: int
    name: str
    platform: Optional[str] = None
    campaign_id: Optional[str] = None
    status: Optional[str] = None
    budget: Optional[float] = None
    spend: Optional[float] = None
    impressions: Optional[int] = None
    clicks: Optional[int] = None
    conversions: Optional[int] = None
    roas: Optional[float] = None
    target_segment: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class CampaignCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    platform: str = Field(..., pattern="^(meta|google|tiktok|snapchat)$")
    budget: float = Field(..., ge=100)
    target_segment: Optional[str] = None


class RetargetingRuleOut(BaseModel):
    id: int
    name: str
    trigger_type: Optional[str] = None
    trigger_config: Optional[str] = None
    ad_template: Optional[str] = None
    audience: Optional[str] = None
    is_active: bool = True

    class Config:
        from_attributes = True


class RetargetingRuleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    trigger_type: str = Field(..., max_length=100)
    trigger_config: Optional[str] = None
    ad_template: str = Field(..., max_length=200)


class WaitlistSignup(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    email: str = Field(..., max_length=320)
    phone: Optional[str] = Field(None, max_length=20)
    segment: Optional[str] = Field(None, max_length=100)
    source: Optional[str] = Field(None, max_length=100)


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
# AD CAMPAIGNS
# ═══════════════════════════════════════════════════════════════

@router.get("/", response_model=List[CampaignOut])
async def list_campaigns(
    platform: Optional[str] = None,
    status: Optional[str] = None,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all ad campaigns."""
    q = select(AdCampaign)
    if platform:
        q = q.where(AdCampaign.platform == platform)
    if status:
        q = q.where(AdCampaign.status == status)
    result = await db.execute(q.order_by(AdCampaign.created_at.desc()))
    return result.scalars().all()


@router.post("/", response_model=CampaignOut)
async def create_campaign(
    body: CampaignCreate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new ad campaign."""
    campaign = AdCampaign(
        name=body.name,
        platform=body.platform,
        campaign_id=f"osool-{body.platform}-{int(datetime.utcnow().timestamp())}",
        status="draft",
        budget=body.budget,
        target_segment=body.target_segment,
    )
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)
    return campaign


@router.get("/stats")
async def campaign_stats(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Aggregated campaign performance."""
    result = await db.execute(
        select(
            AdCampaign.platform,
            func.sum(AdCampaign.spend).label("total_spend"),
            func.sum(AdCampaign.impressions).label("total_impressions"),
            func.sum(AdCampaign.clicks).label("total_clicks"),
            func.sum(AdCampaign.conversions).label("total_conversions"),
        ).group_by(AdCampaign.platform)
    )
    rows = result.all()
    return [
        {
            "platform": r.platform,
            "total_spend": r.total_spend or 0,
            "total_impressions": r.total_impressions or 0,
            "total_clicks": r.total_clicks or 0,
            "total_conversions": r.total_conversions or 0,
        }
        for r in rows
    ]


# ═══════════════════════════════════════════════════════════════
# RETARGETING RULES
# ═══════════════════════════════════════════════════════════════

@router.get("/retargeting", response_model=List[RetargetingRuleOut])
async def list_retargeting_rules(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all retargeting rules."""
    result = await db.execute(select(RetargetingRule).order_by(RetargetingRule.created_at.desc()))
    return result.scalars().all()


@router.post("/retargeting", response_model=RetargetingRuleOut)
async def create_retargeting_rule(
    body: RetargetingRuleCreate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a retargeting rule."""
    rule = RetargetingRule(
        name=body.name,
        trigger_type=body.trigger_type,
        trigger_config=body.trigger_config,
        ad_template=body.ad_template,
        is_active=True,
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return rule


# ═══════════════════════════════════════════════════════════════
# WAITLIST (PUBLIC — no auth required)
# ═══════════════════════════════════════════════════════════════

@router.post("/waitlist")
async def join_waitlist(body: WaitlistSignup, db: AsyncSession = Depends(get_db)):
    """Public endpoint: join the Osool waitlist."""
    # Check duplicate
    existing = await db.execute(
        select(WaitlistEntry).where(WaitlistEntry.email == body.email)
    )
    if existing.scalar_one_or_none():
        return {"status": "already_registered"}

    entry = WaitlistEntry(
        name=body.name,
        email=body.email,
        phone=body.phone,
        segment=body.segment,
        source=body.source,
    )
    db.add(entry)
    await db.commit()
    return {"status": "registered"}


@router.get("/waitlist")
async def list_waitlist(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(100, ge=1, le=1000),
):
    """List waitlist entries (admin)."""
    result = await db.execute(
        select(WaitlistEntry).order_by(WaitlistEntry.created_at.desc()).limit(limit)
    )
    entries = result.scalars().all()
    return [
        {
            "id": e.id, "name": e.name, "email": e.email,
            "phone": e.phone, "segment": e.segment,
            "source": e.source, "created_at": str(e.created_at),
        }
        for e in entries
    ]
