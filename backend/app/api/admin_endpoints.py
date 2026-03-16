"""
Osool Admin API Endpoints
--------------------------
JWT-authenticated admin endpoints for Mustafa@osool.eg and Hani@osool.eg.
Provides full system control: user management, conversation monitoring, scraper triggers.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, text
from typing import Optional
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address
import logging

limiter = Limiter(key_func=get_remote_address)

from app.auth import get_current_user
from app.database import get_db, AsyncSessionLocal
from app.models import (User, ChatMessage, Property, Transaction, 
                        MarketIndicator, ConversationAnalytics, 
                        Ticket, TicketReply, GeopoliticalEvent, MarketingMaterial)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["Admin Dashboard"])


# ═══════════════════════════════════════════════════════════════
# REQUEST MODELS (SECURITY FIX V3: Validated inputs)
# ═══════════════════════════════════════════════════════════════

class UpdateRoleRequest(BaseModel):
    """SECURITY: Strict validation for role updates."""
    role: str = Field(..., pattern="^(investor|agent|analyst|admin|blocked)$")


class BlockUserRequest(BaseModel):
    """SECURITY: Validated block/unblock request."""
    action: str = Field(..., pattern="^(block|unblock)$")


class UpdateTicketStatusRequest(BaseModel):
    """Validated ticket status update."""
    status: str = Field(..., pattern="^(open|in_progress|resolved|closed)$")


class AssignTicketRequest(BaseModel):
    """Assign ticket to an admin user."""
    admin_id: Optional[int] = None


# ═══════════════════════════════════════════════════════════════
# ADMIN ACCESS CONTROL
# ═══════════════════════════════════════════════════════════════


OWNER_EMAIL = "mustafa@osool.eg"
HANI_EMAIL = "hani@osool.eg"


async def require_admin(request: Request, user: User = Depends(get_current_user)) -> User:
    """
    Grants access to: Mustafa, Hani, and any user whose DB role == 'admin'.
    """
    if not user or not user.email:
        raise HTTPException(status_code=401, detail="Authentication required")

    user_email = user.email.strip().lower()
    role = (getattr(user, 'role', '') or '').strip().lower()

    if user_email in {OWNER_EMAIL, HANI_EMAIL} or role == 'admin':
        return user

    logger.warning("Admin access denied for %s on %s", user_email, request.url.path)
    raise HTTPException(status_code=403, detail="Admin access denied")


async def require_super_admin(request: Request, user: User = Depends(get_current_user)) -> User:
    """
    Grants access to Mustafa only. Used for destructive management actions.
    """
    if not user or not user.email:
        raise HTTPException(status_code=401, detail="Authentication required")

    if user.email.strip().lower() != OWNER_EMAIL:
        logger.warning("Super-admin action blocked for %s on %s", user.email, request.url.path)
        raise HTTPException(status_code=403, detail="Owner-only action")

    return user


# ═══════════════════════════════════════════════════════════════
# ADMIN DASHBOARD OVERVIEW
# ═══════════════════════════════════════════════════════════════

@router.get("/dashboard")
async def admin_dashboard(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Admin Dashboard: System overview with key metrics.
    """
    # Total users
    user_count = await db.execute(select(func.count(User.id)))
    total_users = user_count.scalar() or 0

    # Total messages
    msg_count = await db.execute(select(func.count(ChatMessage.id)))
    total_messages = msg_count.scalar() or 0

    # Total properties
    prop_count = await db.execute(select(func.count(Property.id)))
    total_properties = prop_count.scalar() or 0

    # Active properties
    active_prop_count = await db.execute(
        select(func.count(Property.id)).where(Property.is_available == True)
    )
    active_properties = active_prop_count.scalar() or 0

    # Total transactions
    txn_count = await db.execute(select(func.count(Transaction.id)))
    total_transactions = txn_count.scalar() or 0

    # Unique chat sessions
    session_count = await db.execute(
        select(func.count(func.distinct(ChatMessage.session_id)))
    )
    total_sessions = session_count.scalar() or 0

    # Recent user signups (last 7 days)
    from datetime import datetime, timedelta
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_signups = await db.execute(
        select(func.count(User.id)).where(User.created_at >= week_ago)
    )
    new_users_7d = recent_signups.scalar() or 0

    # Recent messages (last 24h)
    day_ago = datetime.utcnow() - timedelta(hours=24)
    recent_msgs = await db.execute(
        select(func.count(ChatMessage.id)).where(ChatMessage.created_at >= day_ago)
    )
    messages_24h = recent_msgs.scalar() or 0

    return {
        "overview": {
            "total_users": total_users,
            "total_messages": total_messages,
            "total_properties": total_properties,
            "active_properties": active_properties,
            "total_transactions": total_transactions,
            "total_sessions": total_sessions,
        },
        "recent_activity": {
            "new_users_7d": new_users_7d,
            "messages_24h": messages_24h,
        },
        "admin": {
            "email": admin.email,
            "name": admin.full_name,
        },
    }


# ═══════════════════════════════════════════════════════════════
# USER MANAGEMENT
# ═══════════════════════════════════════════════════════════════

@router.get("/users")
async def admin_list_users(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
    limit: int = Query(default=100, ge=1, le=1000, description="Max 1000 results per page"),
    offset: int = Query(default=0, ge=0, le=1000000, description="Max offset 1M to prevent abuse"),
):
    """
    Admin: Get all registered users with chat statistics.
    """
    # Get total count first
    count_result = await db.execute(select(func.count(User.id)))
    total_count = count_result.scalar() or 0

    try:
        result = await db.execute(
            select(
                User.id,
                User.email,
                User.full_name,
                User.role,
                User.created_at,
                User.is_verified,
                User.kyc_status,
                func.count(ChatMessage.id).label("message_count"),
                func.max(ChatMessage.created_at).label("last_activity"),
            )
            .outerjoin(ChatMessage, User.id == ChatMessage.user_id)
            .group_by(
                User.id, User.email, User.full_name, User.role,
                User.created_at, User.is_verified, User.kyc_status,
            )
            .order_by(User.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
    except Exception as e:
        # SECURITY FIX V1: Removed dynamic SQL to prevent SQL injection
        # If query fails, return minimal safe data instead of using raw SQL
        logger.error(f"Admin users query failed - database schema may be incomplete: {e}")
        
        # Safe fallback: Return minimal user list without joins
        # Uses ORM exclusively - no string interpolation
        try:
            minimal_result = await db.execute(
                select(User.id, User.email)
                .order_by(User.id.desc())
                .limit(limit)
                .offset(offset)
            )
            users = [
                {
                    "id": row.id,
                    "email": row.email,
                    "full_name": None,
                    "role": None,
                    "created_at": None,
                    "is_verified": None,
                    "kyc_status": None,
                    "message_count": 0,
                    "last_activity": None,
                }
                for row in minimal_result.all()
            ]
            return {
                "total": total_count,
                "users": users,
                "limit": limit,
                "offset": offset,
                "warning": "Schema incomplete - showing minimal data"
            }
        except Exception as fallback_error:
            logger.critical(f"Even minimal query failed: {fallback_error}")
            raise HTTPException(
                status_code=500,
                detail="Database schema error - contact system administrator"
            )

    users = []
    for row in result.all():
        users.append({
            "id": row.id,
            "email": row.email,
            "full_name": row.full_name,
            "role": getattr(row, "role", "investor") or "investor",
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "is_verified": bool(getattr(row, "is_verified", False)),
            "kyc_status": getattr(row, "kyc_status", "unknown") or "unknown",
            "message_count": row.message_count or 0,
            "last_activity": row.last_activity.isoformat() if row.last_activity else None,
        })

    return {"total": total_count, "users": users}


# ═══════════════════════════════════════════════════════════════
# USER ROLE MANAGEMENT
# ═══════════════════════════════════════════════════════════════

@router.patch("/users/{user_id}/role")
async def admin_update_user_role(
    user_id: int,
    body: dict,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_super_admin),
):
    """
    Mustafa only: Change a user's role (investor / agent / analyst / admin).
    """
    VALID_ROLES = {"investor", "agent", "analyst", "admin"}
    new_role = (body.get("role") or "").strip().lower()
    if new_role not in VALID_ROLES:
        raise HTTPException(status_code=422, detail=f"Role must be one of: {', '.join(sorted(VALID_ROLES))}")

    result = await db.execute(select(User).where(User.id == user_id))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if target.email.strip().lower() in {OWNER_EMAIL, HANI_EMAIL}:
        raise HTTPException(status_code=422, detail="Cannot change role of owner accounts")

    target.role = new_role
    await db.commit()
    logger.info("%s changed role of %s (id=%s) to %s", admin.email, target.email, user_id, new_role)
    return {"id": target.id, "email": target.email, "role": target.role}


@router.patch("/users/{user_id}/block")
async def admin_block_user(
    user_id: int,
    body: BlockUserRequest,  # SECURITY FIX V3: Validated input
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_super_admin),
):
    """
    Mustafa only: Block or unblock a user account.
    SECURITY: Now uses validated Pydantic model.
    """
    blocked: bool = (body.action == "block")

    result = await db.execute(select(User).where(User.id == user_id))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if target.email.strip().lower() in {OWNER_EMAIL, HANI_EMAIL}:
        raise HTTPException(status_code=422, detail="Cannot block owner accounts")

    target.role = "blocked" if blocked else "investor"
    await db.commit()
    action = "blocked" if blocked else "unblocked"
    logger.info("%s %s user %s (id=%s)", admin.email, action, target.email, user_id)
    return {"id": target.id, "email": target.email, "blocked": blocked}


# ═══════════════════════════════════════════════════════════════
# CONVERSATION MONITORING (CoInvestor AI Chats)
# ═══════════════════════════════════════════════════════════════

@router.get("/conversations")
async def admin_list_conversations(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
    limit: int = 50,
    offset: int = 0,
):
    """
    Admin: List all conversation sessions with user info and previews.
    Shows all historical and ongoing CoInvestor conversations.
    """
    # Get distinct sessions with user info
    result = await db.execute(
        select(
            ChatMessage.session_id,
            ChatMessage.user_id,
            User.email,
            User.full_name,
            func.count(ChatMessage.id).label("message_count"),
            func.min(ChatMessage.created_at).label("started_at"),
            func.max(ChatMessage.created_at).label("last_message_at"),
        )
        .outerjoin(User, ChatMessage.user_id == User.id)
        .group_by(ChatMessage.session_id, ChatMessage.user_id, User.email, User.full_name)
        .order_by(func.max(ChatMessage.created_at).desc())
        .limit(limit)
        .offset(offset)
    )

    sessions = []
    for row in result.all():
        # Get first user message as preview
        preview_result = await db.execute(
            select(ChatMessage.content)
            .where(
                ChatMessage.session_id == row.session_id,
                ChatMessage.role == "user",
            )
            .order_by(ChatMessage.created_at.asc())
            .limit(1)
        )
        preview = preview_result.scalar_one_or_none()

        sessions.append({
            "session_id": row.session_id,
            "user_id": row.user_id,
            "user_email": row.email,
            "user_name": row.full_name,
            "message_count": row.message_count,
            "started_at": row.started_at.isoformat() if row.started_at else None,
            "last_message_at": row.last_message_at.isoformat() if row.last_message_at else None,
            "preview": (preview[:150] + "...") if preview and len(preview) > 150 else preview,
        })

    return {"total": len(sessions), "sessions": sessions}


@router.get("/conversations/{session_id}")
async def admin_get_conversation(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Admin: Get full conversation thread for a specific session.
    Returns all messages in chronological order.
    """
    import json

    # Get session messages
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
    )
    messages = result.scalars().all()

    if not messages:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Get user info
    user_id = messages[0].user_id
    user_info = None
    if user_id:
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if user:
            user_info = {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
            }

    return {
        "session_id": session_id,
        "user": user_info,
        "message_count": len(messages),
        "messages": [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at.isoformat() if msg.created_at else None,
                "properties": json.loads(msg.properties_json) if msg.properties_json else None,
            }
            for msg in messages
        ],
    }


@router.get("/conversations/user/{user_id}")
async def admin_get_user_conversations(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_super_admin),  # SECURITY FIX V2: Only Mustafa can access arbitrary user chats
):
    """
    SECURITY: Restricted to super-admin only to prevent IDOR attacks.
    View all chat sessions for a specific user.
    """
    # Verify user exists
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get all sessions for this user
    result = await db.execute(
        select(
            ChatMessage.session_id,
            func.count(ChatMessage.id).label("message_count"),
            func.min(ChatMessage.created_at).label("started_at"),
            func.max(ChatMessage.created_at).label("last_message_at"),
        )
        .where(ChatMessage.user_id == user_id)
        .group_by(ChatMessage.session_id)
        .order_by(func.max(ChatMessage.created_at).desc())
    )

    sessions = []
    for row in result.all():
        sessions.append({
            "session_id": row.session_id,
            "message_count": row.message_count,
            "started_at": row.started_at.isoformat() if row.started_at else None,
            "last_message_at": row.last_message_at.isoformat() if row.last_message_at else None,
        })

    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
        },
        "total_sessions": len(sessions),
        "sessions": sessions,
    }


# ═══════════════════════════════════════════════════════════════
# SCRAPER MANAGEMENT
# ═══════════════════════════════════════════════════════════════

@router.post("/scraper/properties")
@limiter.limit("2/minute")  # SECURITY: Prevents repeated triggering of expensive scrape jobs
async def admin_trigger_property_scraper(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Admin: Manually trigger the Nawy property scraper.
    Runs in background.
    """
    from app.services.nawy_scraper import ingest_nawy_data_async
    background_tasks.add_task(ingest_nawy_data_async)
    return {"status": "Property scraper triggered", "triggered_by": admin.email}


@router.post("/scraper/economic")
@limiter.limit("2/minute")  # SECURITY: Each call executes external scraping + DB writes
async def admin_trigger_economic_scraper(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Admin: Manually trigger the economic indicators scraper.
    """
    from app.services.economic_scraper import update_market_indicators
    result = await update_market_indicators(db)
    return {"status": "Economic data updated", "triggered_by": admin.email, **result}


# ═══════════════════════════════════════════════════════════════
# MARKET INDICATORS (Admin View)
# ═══════════════════════════════════════════════════════════════

@router.get("/market-indicators")
async def admin_get_market_indicators(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Admin: Get all market indicator values.
    """
    result = await db.execute(
        select(MarketIndicator).order_by(MarketIndicator.key)
    )
    indicators = result.scalars().all()

    return {
        "total": len(indicators),
        "indicators": [
            {
                "key": ind.key,
                "value": ind.value,
                "source": ind.source,
                "last_updated": ind.last_updated.isoformat() if ind.last_updated else None,
            }
            for ind in indicators
        ],
    }


class UpdateMarketIndicatorRequest(BaseModel):
    """Validated market indicator update (e.g. parallel rate manual override)."""
    value: float = Field(..., ge=0, le=1_000_000)
    source: Optional[str] = Field(None, max_length=200)


@router.patch("/market-indicators/{key}")
@limiter.limit("10/minute")
async def admin_update_market_indicator(
    key: str,
    body: UpdateMarketIndicatorRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Admin: Manually update a single market indicator (e.g. usd_egp_parallel).
    Useful for values that can't be scraped (parallel market rate, etc.).
    """
    if not key.replace("_", "").isalnum() or len(key) > 100:
        raise HTTPException(status_code=400, detail="Invalid indicator key")

    result = await db.execute(
        select(MarketIndicator).where(MarketIndicator.key == key)
    )
    indicator = result.scalar_one_or_none()

    source = body.source or f"Admin Override ({admin.email})"

    if indicator:
        indicator.value = body.value
        indicator.source = source
    else:
        indicator = MarketIndicator(key=key, value=body.value, source=source)
        db.add(indicator)

    await db.commit()
    logger.info(f"Admin {admin.email} updated market indicator {key} = {body.value}")

    return {
        "key": key,
        "value": body.value,
        "source": source,
        "updated_by": admin.email,
    }


# ═══════════════════════════════════════════════════════════════
# ADMIN AUTH CHECK
# ═══════════════════════════════════════════════════════════════

@router.get("/check")
async def admin_check(admin: User = Depends(require_admin)):
    """
    Quick check: Is current user an admin?
    Used by frontend to conditionally show admin tab.
    """
    return {
        "is_admin": True,
        "email": admin.email,
        "name": admin.full_name,
    }


@router.get("/scheduler/status")
async def admin_scheduler_status(admin: User = Depends(require_admin)):
    """
    Admin: Get current scheduler job statuses and next run times.
    """
    try:
        from app.services.scheduler import scheduler
        jobs = []
        for job in scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            })
        return {"running": scheduler.running, "jobs": jobs}
    except Exception as e:
        return {"running": False, "error": str(e)}


# ═══════════════════════════════════════════════════════════════
# ADMIN TICKET MANAGEMENT
# ═══════════════════════════════════════════════════════════════

@router.get("/tickets/stats")
async def admin_ticket_stats(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Get ticket statistics by status."""
    result = await db.execute(
        select(Ticket.status, func.count(Ticket.id)).group_by(Ticket.status)
    )
    counts = dict(result.all())
    return {
        "open": counts.get("open", 0),
        "in_progress": counts.get("in_progress", 0),
        "resolved": counts.get("resolved", 0),
        "closed": counts.get("closed", 0),
        "total": sum(counts.values()),
    }


@router.get("/tickets")
async def admin_list_tickets(
    status: Optional[str] = Query(None, pattern="^(open|in_progress|resolved|closed)$"),
    priority: Optional[str] = Query(None, pattern="^(low|medium|high|urgent)$"),
    category: Optional[str] = Query(None, pattern="^(general|payment|property|technical|account)$"),
    search: Optional[str] = Query(None, max_length=200),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """List all tickets with optional filters. Admin only."""
    query = select(Ticket)

    if status:
        query = query.where(Ticket.status == status)
    if priority:
        query = query.where(Ticket.priority == priority)
    if category:
        query = query.where(Ticket.category == category)
    if search:
        search_pattern = f"%{search}%"
        query = query.where(Ticket.subject.ilike(search_pattern))

    # Total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get tickets with user info via join
    query = query.order_by(desc(Ticket.created_at)).limit(limit).offset(offset)
    result = await db.execute(query)
    tickets = result.scalars().all()

    # Fetch user names and assigned admin names
    user_ids = list(set([t.user_id for t in tickets] + [t.assigned_to for t in tickets if t.assigned_to]))
    user_names = {}
    if user_ids:
        users_result = await db.execute(
            select(User.id, User.full_name, User.email).where(User.id.in_(user_ids))
        )
        for uid, name, email in users_result.all():
            user_names[uid] = {"name": name, "email": email}

    # Reply counts
    ticket_ids = [t.id for t in tickets]
    reply_counts = {}
    if ticket_ids:
        rc_result = await db.execute(
            select(TicketReply.ticket_id, func.count(TicketReply.id))
            .where(TicketReply.ticket_id.in_(ticket_ids))
            .group_by(TicketReply.ticket_id)
        )
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
                "user_name": user_names.get(t.user_id, {}).get("name", "Unknown"),
                "user_email": user_names.get(t.user_id, {}).get("email", ""),
                "assigned_to_name": user_names.get(t.assigned_to, {}).get("name") if t.assigned_to else None,
                "replies_count": reply_counts.get(t.id, 0),
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "updated_at": t.updated_at.isoformat() if t.updated_at else None,
            }
            for t in tickets
        ],
    }


@router.get("/tickets/{ticket_id}")
async def admin_get_ticket(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Get full ticket details with all replies. Admin only."""
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Get ticket creator info
    user_result = await db.execute(
        select(User.full_name, User.email).where(User.id == ticket.user_id)
    )
    ticket_user = user_result.one_or_none()

    # Assigned admin info
    assigned_name = None
    if ticket.assigned_to:
        assigned_result = await db.execute(
            select(User.full_name).where(User.id == ticket.assigned_to)
        )
        assigned_name = assigned_result.scalar_one_or_none()

    # Load replies
    replies_result = await db.execute(
        select(TicketReply)
        .where(TicketReply.ticket_id == ticket_id)
        .order_by(TicketReply.created_at)
    )
    replies = replies_result.scalars().all()

    # Get reply user names
    reply_user_ids = list(set(r.user_id for r in replies))
    reply_user_names = {}
    if reply_user_ids:
        ru_result = await db.execute(
            select(User.id, User.full_name).where(User.id.in_(reply_user_ids))
        )
        reply_user_names = dict(ru_result.all())

    return {
        "id": ticket.id,
        "subject": ticket.subject,
        "description": ticket.description,
        "category": ticket.category,
        "priority": ticket.priority,
        "status": ticket.status,
        "user": {
            "name": ticket_user[0] if ticket_user else "Unknown",
            "email": ticket_user[1] if ticket_user else "",
        },
        "assigned_to_name": assigned_name,
        "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
        "updated_at": ticket.updated_at.isoformat() if ticket.updated_at else None,
        "closed_at": ticket.closed_at.isoformat() if ticket.closed_at else None,
        "replies": [
            {
                "id": r.id,
                "content": r.content,
                "user_name": reply_user_names.get(r.user_id, "Unknown"),
                "is_admin_reply": r.is_admin_reply,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in replies
        ],
    }


@router.patch("/tickets/{ticket_id}/status")
async def admin_update_ticket_status(
    ticket_id: int,
    req: UpdateTicketStatusRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Update a ticket's status. Admin only."""
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket.status = req.status
    if req.status == "closed":
        ticket.closed_at = func.now()
    elif req.status == "open":
        ticket.closed_at = None

    await db.commit()
    await db.refresh(ticket)

    return {
        "id": ticket.id,
        "status": ticket.status,
        "updated_at": ticket.updated_at.isoformat() if ticket.updated_at else None,
    }


@router.patch("/tickets/{ticket_id}/assign")
async def admin_assign_ticket(
    ticket_id: int,
    req: AssignTicketRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Assign a ticket to an admin user. Admin only."""
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if req.admin_id:
        # Verify the target user exists and is an admin
        admin_result = await db.execute(select(User).where(User.id == req.admin_id))
        target_admin = admin_result.scalar_one_or_none()
        if not target_admin:
            raise HTTPException(status_code=404, detail="Admin user not found")
        target_email = (target_admin.email or "").strip().lower()
        target_role = (getattr(target_admin, 'role', '') or '').strip().lower()
        if target_email not in {OWNER_EMAIL, HANI_EMAIL} and target_role != 'admin':
            raise HTTPException(status_code=400, detail="Target user is not an admin")

    ticket.assigned_to = req.admin_id
    await db.commit()
    await db.refresh(ticket)

    return {
        "id": ticket.id,
        "assigned_to": ticket.assigned_to,
        "updated_at": ticket.updated_at.isoformat() if ticket.updated_at else None,
    }


@router.post("/tickets/{ticket_id}/replies")
async def admin_add_ticket_reply(
    ticket_id: int,
    req: dict,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Add an admin reply to any ticket. Admin only."""
    content = (req.get("content") or "").strip()
    if not content or len(content) > 5000:
        raise HTTPException(status_code=422, detail="Reply content is required (max 5000 chars)")

    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    reply = TicketReply(
        ticket_id=ticket_id,
        user_id=admin.id,
        content=content,
        is_admin_reply=True,
    )
    db.add(reply)

    # Auto-set status to in_progress if it was open
    if ticket.status == "open":
        ticket.status = "in_progress"

    await db.commit()
    await db.refresh(reply)

    return {
        "id": reply.id,
        "content": reply.content,
        "user_name": admin.full_name,
        "is_admin_reply": True,
        "created_at": reply.created_at.isoformat() if reply.created_at else None,
    }


# ═══════════════════════════════════════════════════════════════
# GEOPOLITICAL EVENTS
# ═══════════════════════════════════════════════════════════════

@router.post("/scraper/geopolitical")
@limiter.limit("2/minute")  # SECURITY: Each run calls GPT-4o-mini per article — cost abuse risk
async def admin_trigger_geopolitical_scraper(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Admin: Manually trigger the geopolitical & macro events scraper.
    Runs inline (typically < 30s).
    """
    from app.services.geopolitical_scraper import scrape_geopolitical_events
    result = await scrape_geopolitical_events(db, use_llm=True)
    return {"status": "Geopolitical scraper completed", "triggered_by": admin.email, **result}


@router.get("/geopolitical-events")
async def admin_get_geopolitical_events(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
    category: Optional[str] = Query(None, pattern="^(conflict|monetary_policy|currency|oil_energy|inflation|construction_costs|foreign_investment|fiscal_policy|regulation)$"),
    impact_level: Optional[str] = Query(None, pattern="^(high|medium|low)$"),
    limit: int = Query(20, ge=1, le=100),
):
    """
    Admin: View recent geopolitical events with optional filters.
    """
    query = select(GeopoliticalEvent).where(GeopoliticalEvent.is_active == True)

    if category:
        query = query.where(GeopoliticalEvent.category == category)
    if impact_level:
        query = query.where(GeopoliticalEvent.impact_level == impact_level)

    query = query.order_by(desc(GeopoliticalEvent.event_date)).limit(limit)
    result = await db.execute(query)
    events = result.scalars().all()

    return {
        "total": len(events),
        "events": [
            {
                "id": e.id,
                "title": e.title,
                "summary": e.summary,
                "source": e.source,
                "source_url": e.source_url,
                "event_date": e.event_date.isoformat() if e.event_date else None,
                "category": e.category,
                "region": e.region,
                "impact_level": e.impact_level,
                "impact_tags": e.impact_tags,
                "real_estate_impact": e.real_estate_impact,
                "created_at": e.created_at.isoformat() if e.created_at else None,
                "expires_at": e.expires_at.isoformat() if e.expires_at else None,
            }
            for e in events
        ],
    }

@router.get("/marketing-materials")
async def get_marketing_materials(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)
):
    from app.services.marketing_generator import ensure_seeded_questions

    await ensure_seeded_questions(db)

    query = select(MarketingMaterial).order_by(MarketingMaterial.category, MarketingMaterial.id)
    result = await db.execute(query)
    materials = result.scalars().all()
    
    return {
        "total": len(materials),
        "materials": [
            {
                "id": m.id,
                "category": m.category,
                "question_en": m.question_en,
                "question_ar": m.question_ar,
                "answer_en": m.answer_en,
                "answer_ar": m.answer_ar,
                "last_updated": m.last_updated.isoformat() if m.last_updated else None,
                "last_run_status": m.last_run_status
            }
            for m in materials
        ]
    }

@router.post("/marketing-materials/generate")
async def generate_marketing_materials_endpoint(
    background_tasks: BackgroundTasks,
    admin: User = Depends(require_admin)
):
    from app.services.marketing_generator import generate_marketing_answers
    
    async def run_generation():
        try:
            async with AsyncSessionLocal() as db_session:
                count = await generate_marketing_answers(db_session)
                logger.info("Marketing generation background task completed: %d answers", count)
        except Exception as e:
            logger.error("Marketing generation background task failed: %s", e)
    
    background_tasks.add_task(run_generation)
    
    return {"message": "Marketing materials generation started in background. Answers will appear as they are generated — refresh in a few minutes."}
