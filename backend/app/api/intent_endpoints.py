"""
Intent Endpoints — Chat Intent Extraction & Lead Capture
-----------------------------------------------------------
Processes chat messages to extract user intent and auto-create
lead profiles from conversation signals.
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field
from typing import Optional
import logging

from app.auth import get_current_user
from app.database import get_db
from app.models import User, ChatIntent, LeadProfile

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/intent", tags=["Intent & Lead"])


# ═══════════════════════════════════════════════════════════════
# REQUEST / RESPONSE SCHEMAS
# ═══════════════════════════════════════════════════════════════

class IntentInput(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    session_id: Optional[str] = None


class IntentResult(BaseModel):
    intent_type: str
    confidence: float
    extracted: dict
    lead_updated: bool


class LeadProfileOut(BaseModel):
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

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════
# INTENT EXTRACTION
# ═══════════════════════════════════════════════════════════════

@router.post("/extract", response_model=IntentResult)
async def extract_intent(
    body: IntentInput,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Extract purchase intent from a chat message.
    Updates the user's lead profile automatically.
    """
    # Lazy import to avoid circular deps
    from app.ai_engine.intent_extractor import extract_intent as _extract

    result = await _extract(body.message)

    # Persist intent record
    import json as _json
    intent = ChatIntent(
        user_id=user.id,
        session_id=body.session_id or str(user.id),
        raw_query=body.message,
        intent_type=result.get("intent_type", "GENERAL"),
        confidence=result.get("confidence", 0.0),
        entities=_json.dumps(result.get("extracted", {})),
    )
    db.add(intent)

    # Upsert lead profile
    lead_updated = False
    if result["confidence"] >= 0.6:
        lead_q = await db.execute(
            select(LeadProfile).where(LeadProfile.user_id == user.id)
        )
        lead = lead_q.scalar_one_or_none()
        if not lead:
            lead = LeadProfile(user_id=user.id, stage="new")
            db.add(lead)

        extracted = result["extracted"]
        if extracted.get("budget_min"):
            lead.budget_min = extracted["budget_min"]
        if extracted.get("budget_max"):
            lead.budget_max = extracted["budget_max"]
        if extracted.get("areas"):
            lead.preferred_areas = _json.dumps(extracted["areas"])
        if extracted.get("property_types"):
            lead.preferred_types = _json.dumps(extracted["property_types"])
        if extracted.get("timeline"):
            lead.timeline = extracted["timeline"]

        # Bump score
        lead.score = min(100, (lead.score or 0) + int(result["confidence"] * 20))
        lead.interaction_count = (lead.interaction_count or 0) + 1
        lead_updated = True

    await db.commit()

    return IntentResult(
        intent_type=result["intent_type"],
        confidence=result["confidence"],
        extracted=result["extracted"],
        lead_updated=lead_updated,
    )


# ═══════════════════════════════════════════════════════════════
# LEAD PROFILE
# ═══════════════════════════════════════════════════════════════

@router.get("/lead/me", response_model=LeadProfileOut)
async def get_my_lead_profile(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the current user's lead profile."""
    result = await db.execute(
        select(LeadProfile).where(LeadProfile.user_id == user.id)
    )
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="No lead profile yet — start chatting!")
    return lead


@router.get("/intents/me")
async def get_my_intents(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 20,
):
    """Get recent intents extracted from user's messages."""
    result = await db.execute(
        select(ChatIntent)
        .where(ChatIntent.user_id == user.id)
        .order_by(ChatIntent.created_at.desc())
        .limit(limit)
    )
    intents = result.scalars().all()
    return [
        {
            "id": i.id,
            "intent_type": i.intent_type,
            "confidence": i.confidence,
            "entities": i.entities,
            "created_at": str(i.created_at),
        }
        for i in intents
    ]
