"""
Email Automation Endpoints
-----------------------------
Manages email drip campaigns, event tracking, and user
subscription preferences via Resend API.
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
from app.models import User, EmailEvent, EmailStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/email", tags=["Email Automation"])


# ═══════════════════════════════════════════════════════════════
# SCHEMAS
# ═══════════════════════════════════════════════════════════════

class EmailEventOut(BaseModel):
    id: int
    user_id: Optional[int] = None
    email_type: Optional[str] = None
    subject: Optional[str] = None
    status: Optional[str] = None
    sent_at: Optional[str] = None
    opened_at: Optional[str] = None
    clicked_at: Optional[str] = None

    class Config:
        from_attributes = True


class SendEmailRequest(BaseModel):
    user_id: int
    email_type: str = Field(..., pattern="^(welcome|drip_1|drip_2|drip_3|price_alert|report|custom)$")
    subject: str = Field(..., min_length=1, max_length=200)
    body_html: str = Field(..., min_length=1, max_length=50000)


class WebhookPayload(BaseModel):
    """Resend webhook payload (simplified)."""
    type: str
    data: dict


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
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@router.post("/send")
async def send_email(
    body: SendEmailRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Send an email via Resend and log the event."""
    import os
    resend_key = os.getenv("RESEND_API_KEY")
    if not resend_key:
        raise HTTPException(status_code=503, detail="Email service not configured")

    # Get recipient
    user_q = await db.execute(select(User).where(User.id == body.user_id))
    target_user = user_q.scalar_one_or_none()
    if not target_user or not target_user.email:
        raise HTTPException(status_code=404, detail="User not found or no email")

    # Send via Resend
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {resend_key}"},
                json={
                    "from": os.getenv("EMAIL_FROM", "Osool <noreply@osool.eg>"),
                    "to": [target_user.email],
                    "subject": body.subject,
                    "html": body.body_html,
                },
                timeout=15.0,
            )
            resp.raise_for_status()
            resend_data = resp.json()
    except Exception as e:
        logger.error("Resend API error: %s", e)
        raise HTTPException(status_code=502, detail="Email delivery failed")

    # Log
    event = EmailEvent(
        user_id=body.user_id,
        template_id=body.email_type,
        email_type=body.email_type,
        subject=body.subject,
        status=EmailStatus.SENT,
        resend_id=resend_data.get("id"),
        sent_at=datetime.utcnow(),
    )
    db.add(event)
    await db.commit()

    return {"status": "sent", "resend_id": resend_data.get("id")}


@router.post("/webhook")
async def resend_webhook(payload: WebhookPayload, db: AsyncSession = Depends(get_db)):
    """
    Resend webhook handler for delivery/open/click tracking.
    Configure at: https://resend.com/webhooks
    """
    event_type = payload.type
    data = payload.data
    resend_id = data.get("email_id")

    if not resend_id:
        return {"status": "ignored"}

    result = await db.execute(
        select(EmailEvent).where(EmailEvent.resend_id == resend_id)
    )
    event = result.scalar_one_or_none()
    if not event:
        return {"status": "not_found"}

    now = datetime.utcnow()

    if event_type == "email.delivered":
        event.status = EmailStatus.DELIVERED
    elif event_type == "email.opened":
        event.status = EmailStatus.OPENED
        event.opened_at = now
    elif event_type == "email.clicked":
        event.status = EmailStatus.CLICKED
        event.clicked_at = now
    elif event_type == "email.bounced":
        event.status = EmailStatus.BOUNCED

    await db.commit()
    return {"status": "processed"}


@router.get("/events", response_model=List[EmailEventOut])
async def list_email_events(
    user_id: Optional[int] = None,
    email_type: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List email events (admin only)."""
    q = select(EmailEvent)
    if user_id:
        q = q.where(EmailEvent.user_id == user_id)
    if email_type:
        q = q.where(EmailEvent.email_type == email_type)
    result = await db.execute(q.order_by(EmailEvent.sent_at.desc()).limit(limit))
    return result.scalars().all()


@router.get("/stats")
async def email_stats(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Email performance stats."""
    total = (await db.execute(select(func.count(EmailEvent.id)))).scalar()
    by_status = (await db.execute(
        select(EmailEvent.status, func.count(EmailEvent.id))
        .group_by(EmailEvent.status)
    )).all()
    return {
        "total_sent": total,
        "by_status": {str(s): c for s, c in by_status if s},
    }
