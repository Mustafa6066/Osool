"""
Lead Management Endpoints — Admin-facing
-------------------------------------------
CRUD for lead profiles, lead scoring, pipeline stages.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import Optional, List
from pydantic import BaseModel, Field
import logging

from app.auth import get_current_user
from app.database import get_db
from app.models import User, LeadProfile

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/leads", tags=["Lead Management"])


# ═══════════════════════════════════════════════════════════════
# SCHEMAS
# ═══════════════════════════════════════════════════════════════

class LeadOut(BaseModel):
    id: int
    user_id: Optional[int] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    preferred_areas: Optional[str] = None
    preferred_types: Optional[str] = None
    timeline: Optional[str] = None
    score: Optional[float] = None
    stage: Optional[str] = None
    segment: Optional[str] = None
    interaction_count: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class LeadUpdate(BaseModel):
    stage: Optional[str] = Field(None, pattern="^(new|engaged|hot|qualified|converted|lost)$")
    score: Optional[float] = Field(None, ge=0, le=100)
    notes: Optional[str] = Field(None, max_length=2000)


# ═══════════════════════════════════════════════════════════════
# ADMIN GUARD (reuse from admin_endpoints pattern)
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
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@router.get("", response_model=List[LeadOut])
async def list_leads(
    stage: Optional[str] = None,
    min_score: Optional[int] = None,
    sort: str = Query("score", pattern="^(score|created_at|updated_at)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all leads (admin only)."""
    from sqlalchemy.orm import selectinload
    q = select(LeadProfile).options(selectinload(LeadProfile.user))
    if stage:
        q = q.where(LeadProfile.stage == stage)
    if min_score is not None:
        q = q.where(LeadProfile.score >= min_score)

    col = getattr(LeadProfile, sort, LeadProfile.score)
    order_col = col.desc() if order == "desc" else col.asc()
    result = await db.execute(q.order_by(order_col).limit(limit).offset(offset))
    leads = result.scalars().all()
    return [
        {
            "id": lp.id,
            "user_id": lp.user_id,
            "email": lp.user.email if lp.user else None,
            "phone": lp.user.phone if lp.user and hasattr(lp.user, 'phone') else None,
            "stage": lp.stage,
            "score": lp.score,
            "segment": lp.segment,
            "budget_min": lp.budget_min,
            "budget_max": lp.budget_max,
            "preferred_areas": lp.preferred_areas,
            "preferred_types": lp.preferred_types,
            "timeline": lp.timeline,
            "interaction_count": lp.interaction_count,
            "created_at": str(lp.created_at) if lp.created_at else None,
            "updated_at": str(lp.updated_at) if lp.updated_at else None,
        }
        for lp in leads
    ]


@router.get("/stats")
async def lead_stats(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Pipeline statistics."""
    total = (await db.execute(select(func.count(LeadProfile.id)))).scalar()
    hot = (await db.execute(
        select(func.count(LeadProfile.id)).where(LeadProfile.score >= 70)
    )).scalar()
    stages = (await db.execute(
        select(LeadProfile.stage, func.count(LeadProfile.id))
        .group_by(LeadProfile.stage)
    )).all()
    return {
        "total_leads": total,
        "hot_leads": hot,
        "by_stage": {s: c for s, c in stages if s},
    }


@router.get("/{lead_id}", response_model=LeadOut)
async def get_lead(
    lead_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get a single lead."""
    result = await db.execute(select(LeadProfile).where(LeadProfile.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.patch("/{lead_id}", response_model=LeadOut)
async def update_lead(
    lead_id: int,
    body: LeadUpdate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update lead stage or score."""
    result = await db.execute(select(LeadProfile).where(LeadProfile.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    if body.stage is not None:
        lead.stage = body.stage
    if body.score is not None:
        lead.score = body.score

    await db.commit()
    await db.refresh(lead)
    return lead
