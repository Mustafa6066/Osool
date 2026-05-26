from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from app.auth import get_current_user_optional, is_forced_free_test_user_email
from app.ai_engine.company_brain import CompanyBrainKernel
from app.ai_engine.free_tier_gate import build_best_price_free_payload
from app.ai_engine.wolf_orchestrator import wolf_brain
from app.database import get_db
from app.middleware.rate_limiting import limiter, CHAT_RATE_LIMIT
from app.models import ChatMessage, User

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    session_id: str
    language: str = "auto"
    is_authenticated: bool = False

class ChatResponse(BaseModel):
    type: str
    text: str
    properties: List[Dict[str, Any]]
    show_upsell: bool
    ui_actions: List[Dict[str, Any]] = []
    ui_primitive_descriptor: Optional[str] = None
    primitive_data: Optional[Dict[str, Any]] = None


def _viewer_kind(user: Optional[User]) -> str:
    if user is None:
        return "anonymous"
    if is_forced_free_test_user_email(getattr(user, "email", None)):
        return "free"
    tier = (getattr(user, "subscription_tier", "free") or "free").lower()
    if getattr(user, "role", "").lower() == "admin" or tier in {"premium", "admin"}:
        return "premium"
    return "free"

@router.post("/chat", response_model=ChatResponse)
@limiter.limit(CHAT_RATE_LIMIT)
async def process_chat(
    chat_request: ChatRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Main endpoint for the Chat Interface.
    Routes free users through the Zero-Token Local Path.

    Rate limit: CHAT_RATE_LIMIT (30/minute) keyed by user_id when authed,
    by IP otherwise — see middleware/rate_limiting.py.
    """

    # Track session count for gate logic.
    session_count_stmt = select(func.count()).where(
        ChatMessage.session_id == chat_request.session_id,
        ChatMessage.role == "user"
    )
    if user:
        session_count_stmt = session_count_stmt.where(ChatMessage.user_id == user.id)
    else:
        session_count_stmt = session_count_stmt.where(ChatMessage.user_id.is_(None))
    session_count = (await db.execute(session_count_stmt)).scalar_one()

    # Load prior user messages (newest first) so the local router can merge
    # entities like area/compound/budget from earlier turns. Without this the
    # chat becomes effectively stateless and loops on clarification prompts.
    history_stmt = (
        select(ChatMessage.content)
        .where(
            ChatMessage.session_id == chat_request.session_id,
            ChatMessage.role == "user",
        )
        .order_by(ChatMessage.created_at.desc())
        .limit(6)
    )
    if user:
        history_stmt = history_stmt.where(ChatMessage.user_id == user.id)
    else:
        history_stmt = history_stmt.where(ChatMessage.user_id.is_(None))
    previous_user_messages = [row[0] for row in (await db.execute(history_stmt)).all()]

    # Save user message
    user_msg = ChatMessage(
        session_id=chat_request.session_id,
        user_id=user.id if user else None,
        role="user",
        content=chat_request.message
    )
    db.add(user_msg)
    await db.commit()

    try:
        kind = _viewer_kind(user)

        if kind in {"anonymous", "free"}:
            payload = await build_best_price_free_payload(db, chat_request.message, chat_request.language)
            response_text = payload.get("response", "")
            properties = payload.get("properties", [])
            ui_actions = payload.get("ui_actions", [])
            show_upsell = bool(payload.get("show_upsell", False))
            ui_primitive_descriptor = payload.get("ui_primitive_descriptor")
            primitive_data = payload.get("primitive_data")

            ai_msg = ChatMessage(
                session_id=chat_request.session_id,
                user_id=user.id if user else None,
                role="assistant",
                content=response_text,
            )
            db.add(ai_msg)
            await db.commit()

            return ChatResponse(
                type="success",
                text=response_text,
                properties=properties,
                show_upsell=show_upsell,
                ui_actions=ui_actions,
                ui_primitive_descriptor=ui_primitive_descriptor,
                primitive_data=primitive_data,
            )

        history = [{"role": "user", "content": text} for text in reversed(previous_user_messages)]
        history.append({"role": "user", "content": chat_request.message})
        system_truth = await CompanyBrainKernel.synthesize_definitive_truth(db)
        history = [{"role": "system", "content": system_truth}] + history

        result = await wolf_brain.process_turn(
            query=chat_request.message,
            history=history,
            profile={
                "id": user.id if user else None,
                "email": getattr(user, "email", None) if user else None,
            },
            language=chat_request.language,
            session_id=chat_request.session_id,
        )

        response_text = result.get("response", "")
        properties = result.get("properties", [])
        ui_actions = result.get("ui_actions") or result.get("charts", [])

        ai_msg = ChatMessage(
            session_id=chat_request.session_id,
            user_id=user.id if user else None,
            role="assistant",
            content=response_text,
        )
        db.add(ai_msg)
        await db.commit()

        return ChatResponse(
            type="success",
            text=response_text,
            properties=properties,
            show_upsell=False,
            ui_actions=ui_actions,
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
