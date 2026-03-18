"""
Orchestrator Integration Endpoints
-----------------------------------
Bridges the Osool Platform (FastAPI) with the Osool Orchestrator (Fastify).

Provides:
1. GET /api/orchestrator/context — Fetch enriched user context from orchestrator
2. POST /api/orchestrator/sync-session — Push chat session data to orchestrator
3. GET /api/orchestrator/notifications — Fetch user notifications from orchestrator

All calls are server-to-server with API key auth.
"""

import os
import logging
import secrets
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from app.auth import get_current_user
from app.models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/orchestrator", tags=["Orchestrator Integration"])

ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "").rstrip("/")
ORCHESTRATOR_API_KEY = os.getenv("ORCHESTRATOR_API_KEY", "")

_http_client: Optional[httpx.AsyncClient] = None


def _get_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(10.0, connect=5.0),
            headers={
                "Content-Type": "application/json",
                "X-API-Key": ORCHESTRATOR_API_KEY,
            },
        )
    return _http_client


async def _fetch_from_orchestrator(path: str) -> dict:
    """Fetch data from orchestrator data API. Returns empty dict on failure."""
    if not ORCHESTRATOR_URL:
        return {}
    client = _get_client()
    try:
        resp = await client.get(f"{ORCHESTRATOR_URL}/data{path}")
        if resp.status_code == 200:
            return resp.json()
        logger.warning(f"Orchestrator returned {resp.status_code} for {path}")
        return {}
    except httpx.RequestError as e:
        logger.error(f"Orchestrator unreachable for {path}: {e}")
        return {}


# ── Response Models ────────────────────────────────────────────────────────────

class OrchestratorContext(BaseModel):
    lead_score: int = 0
    tier: str = "cold"
    icp_segment: str = "first_time_buyer"
    preferred_developers: list[str] = []
    preferred_areas: list[str] = []
    intent_types: list[str] = []
    signal_count: int = 0
    suggested_topics: list[str] = []


class Notification(BaseModel):
    id: str
    type: str
    title: str
    title_ar: str = ""
    body: str
    body_ar: str = ""
    read: bool = False
    created_at: str = ""


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get("/context")
async def get_user_context(user: User = Depends(get_current_user)):
    """
    Fetch enriched user context from the Orchestrator.
    Includes lead score, ICP segment, preferred developers/areas,
    recent intents, and suggested chat topics.

    This data is injected into the AI chat system prompt so the
    CoInvestor advisor remembers the user across the entire journey.
    """
    data = await _fetch_from_orchestrator(f"/user-context/{user.id}")
    if not data:
        return OrchestratorContext().model_dump()

    return OrchestratorContext(
        lead_score=data.get("leadScore", 0),
        tier=data.get("tier", "cold"),
        icp_segment=data.get("icpSegment", "first_time_buyer"),
        preferred_developers=data.get("preferredDevelopers", []),
        preferred_areas=data.get("preferredAreas", []),
        intent_types=data.get("intentTypes", []),
        signal_count=data.get("signalCount", 0),
        suggested_topics=data.get("suggestedTopics", []),
    ).model_dump()


@router.get("/notifications")
async def get_notifications(
    limit: int = 20,
    user: User = Depends(get_current_user),
):
    """
    Fetch unread notifications for the current user from the Orchestrator.
    Includes market pulse alerts, trending developers, and investment insights.
    """
    data = await _fetch_from_orchestrator(f"/notifications/{user.id}?limit={limit}")
    notifications_raw = data.get("notifications", [])

    return {
        "notifications": [
            Notification(
                id=n.get("id", ""),
                type=n.get("type", ""),
                title=n.get("title", ""),
                title_ar=n.get("titleAr", ""),
                body=n.get("body", ""),
                body_ar=n.get("bodyAr", ""),
                read=n.get("read", False),
                created_at=n.get("createdAt", ""),
            ).model_dump()
            for n in notifications_raw
        ],
        "unread_count": sum(1 for n in notifications_raw if not n.get("read", False)),
    }


@router.get("/trending")
async def get_trending(user: User = Depends(get_current_user)):
    """
    Fetch trending market data from the Orchestrator.
    Includes trending developers, locations, and search queries.
    HIGH-8 fix: Requires auth — trending data is proprietary business intelligence.
    """
    data = await _fetch_from_orchestrator("/trending")
    return data or {
        "trendingDevelopers": [],
        "trendingLocations": [],
        "trendingQueries": [],
        "period": "7d",
    }


@router.get("/chat-context/{session_id}")
async def get_chat_context(
    session_id: str,
    user: User = Depends(get_current_user),
):
    """
    Fetch enriched chat context from the Orchestrator for a specific session.
    Includes intent signals, lead score, and personalization hints.
    Used to resume conversations with full context.
    """
    data = await _fetch_from_orchestrator(f"/chat-context/{session_id}")
    return data or {
        "leadScore": 0,
        "segment": "first_time_buyer",
        "previousIntents": [],
        "suggestedTopics": [],
        "personalizationHints": {},
    }


# ── SMS Fallback for Orchestrator Notifications ──────────────────────────────

INTERNAL_API_KEY = os.getenv("ORCHESTRATOR_API_KEY", "")


def _verify_api_key(request: Request):
    """Verify X-API-Key header for server-to-server calls from the Orchestrator."""
    key = request.headers.get("X-API-Key", "")
    # HIGH-1 fix: Use constant-time comparison to prevent timing-based key oracle attacks
    if not key or not INTERNAL_API_KEY or not secrets.compare_digest(key.encode(), INTERNAL_API_KEY.encode()):
        raise HTTPException(status_code=401, detail="Invalid API key")


class SendSMSRequest(BaseModel):
    phone: str
    message: str


@router.post("/send-sms")
async def send_sms_fallback(body: SendSMSRequest, request: Request):
    """
    SMS fallback endpoint called by the Orchestrator's notification-push job
    when WhatsApp delivery fails (user doesn't have WhatsApp or API error).
    Uses the Platform's existing Twilio SMS service.
    Auth: X-API-Key (server-to-server only).
    """
    _verify_api_key(request)

    try:
        from app.services.sms_service import send_message
        await send_message(body.phone, body.message)
        return {"status": "sent"}
    except Exception as e:
        logger.error(f"SMS fallback failed for {body.phone[:6]}***: {e}")
        raise HTTPException(status_code=502, detail="SMS delivery failed")


# ── User Notification Preferences ────────────────────────────────────────────

class NotificationPrefsUpdate(BaseModel):
    in_app: bool = True
    whatsapp: bool = False
    email_digest: bool = False
    frequency: str = "realtime"
    whatsapp_number: Optional[str] = None


# Use prefix-less router for /api/user/* endpoints
user_prefs_router = APIRouter(prefix="/api/user", tags=["User Preferences"])


@user_prefs_router.get("/notification-preferences")
async def get_notification_preferences(user: User = Depends(get_current_user)):
    """Get the current user's notification preferences."""
    from sqlalchemy import select
    from app.database import async_session
    from app.models import UserMemory

    async with async_session() as session:
        result = await session.execute(
            select(UserMemory).where(UserMemory.user_id == user.id)
        )
        memory = result.scalar_one_or_none()

    if not memory or not memory.memory_json:
        return NotificationPrefsUpdate().model_dump()

    prefs = memory.memory_json.get("notification_preferences", {})
    return NotificationPrefsUpdate(
        in_app=prefs.get("in_app", True),
        whatsapp=prefs.get("whatsapp", False),
        email_digest=prefs.get("email_digest", False),
        frequency=prefs.get("frequency", "realtime"),
        whatsapp_number=prefs.get("whatsapp_number"),
    ).model_dump()


@user_prefs_router.patch("/notification-preferences")
async def update_notification_preferences(
    body: NotificationPrefsUpdate,
    user: User = Depends(get_current_user),
):
    """Update the current user's notification preferences."""
    from sqlalchemy import select
    from app.database import async_session
    from app.models import UserMemory

    async with async_session() as session:
        result = await session.execute(
            select(UserMemory).where(UserMemory.user_id == user.id)
        )
        memory = result.scalar_one_or_none()

        if not memory:
            memory = UserMemory(user_id=user.id, memory_json={})
            session.add(memory)

        if not memory.memory_json:
            memory.memory_json = {}

        memory.memory_json["notification_preferences"] = body.model_dump()
        await session.commit()

    return {"status": "updated"}
