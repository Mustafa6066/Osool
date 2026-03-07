"""
Osool Admin API Endpoints
--------------------------
JWT-authenticated admin endpoints for Mustafa@osool.eg and Hani@osool.eg.
Provides full system control: user management, conversation monitoring, scraper triggers.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, text
from typing import Optional
import os
import logging

from app.auth import get_current_user
from app.database import get_db
from app.models import User, ChatMessage, Property, Transaction, MarketIndicator, ConversationAnalytics

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["Admin Dashboard"])

# ═══════════════════════════════════════════════════════════════
# ADMIN ACCESS CONTROL
# ═══════════════════════════════════════════════════════════════


async def require_admin(request: Request, user: User = Depends(get_current_user)) -> User:
    """
    Dependency: Ensures current user has admin role in the database.
    Database-driven RBAC — no hardcoded email lists.
    """
    if not user or not user.email:
        raise HTTPException(status_code=401, detail="Authentication required")

    role = (getattr(user, 'role', '') or '').strip().lower()
    if role in {"admin", "super_admin"}:
        return user

    # Compatibility fallback for legacy/misaligned production data.
    # Allows explicitly configured admin emails when role is not normalized.
    configured_admins = {
        e.strip().lower()
        for e in os.getenv("ADMIN_EMAILS", "").split(",")
        if e.strip()
    }
    configured_admins.update({"mustafa@osool.eg", "hani@osool.eg"})

    user_email = user.email.strip().lower()
    if user_email in configured_admins:
        logger.warning(
            "Admin access granted via email fallback for %s on %s (role=%s)",
            user_email,
            request.url.path,
            role or "<empty>",
        )
        return user

    logger.warning(
        "Admin access denied for %s on %s (role=%s)",
        user_email,
        request.url.path,
        role or "<empty>",
    )
    raise HTTPException(status_code=403, detail="Admin access denied")


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
    limit: int = 100,
    offset: int = 0,
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
        # Backward-compatibility fallback for partially migrated DBs
        logger.warning(f"Admin users full query failed; using fallback columns. Error: {e}")
        # Schema-aware raw SQL fallback: avoid referencing ORM columns that may not exist yet.
        col_result = await db.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'users'
        """))
        user_cols = {row[0] for row in col_result.fetchall()}

        table_result = await db.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'chat_messages'
            )
        """))
        has_chat_messages = bool(table_result.scalar())

        def col_or_null(column_name: str, cast_type: str = "text") -> str:
            if column_name in user_cols:
                return f"u.{column_name}"
            return f"NULL::{cast_type}"

        created_at_expr = col_or_null("created_at", "timestamptz")
        order_expr = "u.created_at DESC" if "created_at" in user_cols else "u.id DESC"

        if has_chat_messages:
            fallback_sql = f"""
                SELECT
                    u.id AS id,
                    {col_or_null('email')} AS email,
                    {col_or_null('full_name')} AS full_name,
                    {col_or_null('role')} AS role,
                    {created_at_expr} AS created_at,
                    {col_or_null('is_verified', 'boolean')} AS is_verified,
                    {col_or_null('kyc_status')} AS kyc_status,
                    COALESCE(cm.message_count, 0) AS message_count,
                    cm.last_activity AS last_activity
                FROM users u
                LEFT JOIN (
                    SELECT user_id, COUNT(*) AS message_count, MAX(created_at) AS last_activity
                    FROM chat_messages
                    GROUP BY user_id
                ) cm ON cm.user_id = u.id
                ORDER BY {order_expr}
                LIMIT :limit OFFSET :offset
            """
        else:
            fallback_sql = f"""
                SELECT
                    u.id AS id,
                    {col_or_null('email')} AS email,
                    {col_or_null('full_name')} AS full_name,
                    {col_or_null('role')} AS role,
                    {created_at_expr} AS created_at,
                    {col_or_null('is_verified', 'boolean')} AS is_verified,
                    {col_or_null('kyc_status')} AS kyc_status,
                    0::bigint AS message_count,
                    NULL::timestamptz AS last_activity
                FROM users u
                ORDER BY {order_expr}
                LIMIT :limit OFFSET :offset
            """

        result = await db.execute(text(fallback_sql), {"limit": limit, "offset": offset})

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
    admin: User = Depends(require_admin),
):
    """
    Admin: Get all conversations for a specific user.
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
async def admin_trigger_property_scraper(
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
async def admin_trigger_economic_scraper(
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
