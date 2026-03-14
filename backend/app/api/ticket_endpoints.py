"""
Osool Ticket API Endpoints (User-Facing)
------------------------------------------
Authenticated users can create, view, and reply to their own support tickets.
Users can ONLY access their own tickets (enforced by user_id filtering).
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import Optional
from pydantic import BaseModel, Field
import logging

from app.auth import get_current_user
from app.database import get_db
from app.models import User, Ticket, TicketReply

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tickets", tags=["Tickets"])


# ═══════════════════════════════════════════════════════════════
# REQUEST / RESPONSE MODELS
# ═══════════════════════════════════════════════════════════════

class CreateTicketRequest(BaseModel):
    subject: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10, max_length=5000)
    category: str = Field("general", pattern="^(general|payment|property|technical|account)$")
    priority: str = Field("medium", pattern="^(low|medium|high|urgent)$")


class CreateReplyRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)


# ═══════════════════════════════════════════════════════════════
# USER TICKET ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@router.post("")
async def create_ticket(
    req: CreateTicketRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a new support ticket."""
    ticket = Ticket(
        user_id=user.id,
        subject=req.subject,
        description=req.description,
        category=req.category,
        priority=req.priority,
        status="open",
    )
    db.add(ticket)
    await db.commit()
    await db.refresh(ticket)

    return {
        "id": ticket.id,
        "subject": ticket.subject,
        "description": ticket.description,
        "category": ticket.category,
        "priority": ticket.priority,
        "status": ticket.status,
        "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
    }


@router.get("")
async def list_my_tickets(
    status: Optional[str] = Query(None, pattern="^(open|in_progress|resolved|closed)$"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List current user's tickets with optional status filter."""
    query = select(Ticket).where(Ticket.user_id == user.id)

    if status:
        query = query.where(Ticket.status == status)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get tickets
    query = query.order_by(desc(Ticket.created_at)).limit(limit).offset(offset)
    result = await db.execute(query)
    tickets = result.scalars().all()

    # Get reply counts for each ticket
    ticket_ids = [t.id for t in tickets]
    reply_counts = {}
    if ticket_ids:
        rc_query = (
            select(TicketReply.ticket_id, func.count(TicketReply.id))
            .where(TicketReply.ticket_id.in_(ticket_ids))
            .group_by(TicketReply.ticket_id)
        )
        rc_result = await db.execute(rc_query)
        reply_counts = dict(rc_result.all())

    return {
        "total": total,
        "tickets": [
            {
                "id": t.id,
                "subject": t.subject,
                "category": t.category,
                "priority": t.priority,
                "status": t.status,
                "replies_count": reply_counts.get(t.id, 0),
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "updated_at": t.updated_at.isoformat() if t.updated_at else None,
            }
            for t in tickets
        ],
    }


@router.get("/{ticket_id}")
async def get_ticket_detail(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get a ticket's details and replies. Users can only access their own tickets."""
    result = await db.execute(
        select(Ticket).where(Ticket.id == ticket_id, Ticket.user_id == user.id)
    )
    ticket = result.scalar_one_or_none()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Load replies
    replies_result = await db.execute(
        select(TicketReply)
        .where(TicketReply.ticket_id == ticket_id)
        .order_by(TicketReply.created_at)
    )
    replies = replies_result.scalars().all()

    # Get reply user names
    reply_user_ids = list(set(r.user_id for r in replies))
    user_names = {}
    if reply_user_ids:
        users_result = await db.execute(
            select(User.id, User.full_name).where(User.id.in_(reply_user_ids))
        )
        user_names = dict(users_result.all())

    return {
        "id": ticket.id,
        "subject": ticket.subject,
        "description": ticket.description,
        "category": ticket.category,
        "priority": ticket.priority,
        "status": ticket.status,
        "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
        "updated_at": ticket.updated_at.isoformat() if ticket.updated_at else None,
        "closed_at": ticket.closed_at.isoformat() if ticket.closed_at else None,
        "replies": [
            {
                "id": r.id,
                "content": r.content,
                "user_name": user_names.get(r.user_id, "Unknown"),
                "is_admin_reply": r.is_admin_reply,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in replies
        ],
    }


@router.post("/{ticket_id}/replies")
async def add_ticket_reply(
    ticket_id: int,
    req: CreateReplyRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Add a reply to the user's own ticket."""
    # Verify ticket belongs to the user
    result = await db.execute(
        select(Ticket).where(Ticket.id == ticket_id, Ticket.user_id == user.id)
    )
    ticket = result.scalar_one_or_none()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if ticket.status == "closed":
        raise HTTPException(status_code=400, detail="Cannot reply to a closed ticket")

    reply = TicketReply(
        ticket_id=ticket_id,
        user_id=user.id,
        content=req.content,
        is_admin_reply=False,
    )
    db.add(reply)
    await db.commit()
    await db.refresh(reply)

    return {
        "id": reply.id,
        "content": reply.content,
        "user_name": user.full_name,
        "is_admin_reply": False,
        "created_at": reply.created_at.isoformat() if reply.created_at else None,
    }
