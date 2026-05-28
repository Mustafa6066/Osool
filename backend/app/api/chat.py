import asyncio
import logging
import re

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from app.auth import get_current_user_optional, is_forced_free_test_user_email

logger = logging.getLogger(__name__)

# Hard ceiling for the Free-tier "best price" path. The frontend axios
# timeout is 30s; we leave ourselves 10s of slack so a graceful in-language
# fallback always lands before the browser gives up and shows the generic
# "Could not reach Osool" error.
_FREE_PATH_TIMEOUT_S = 20.0
_ARABIC_RANGE = re.compile(r"[؀-ۿ]")


def _detect_language(message: str) -> str:
    """Return 'ar' if the message contains any Arabic codepoint, else 'en'.
    Matches the heuristic the Wolf orchestrator already uses."""
    return "ar" if _ARABIC_RANGE.search(message or "") else "en"


def _free_path_timeout_payload(message: str) -> Dict[str, Any]:
    """
    Build a graceful "couldn't find the best price in time" response in the
    user's language. Free-tier policy: ONE best price, no extra features.
    When the search runs over budget (slow correlated subqueries on a niche
    criterion that has no matches), we still send a useful answer — not a
    generic timeout error.
    """
    lang = _detect_language(message)
    if lang == "ar":
        text = (
            "ما لقيتش وحدة بأقل سعر تطابق طلبك في الوقت المحدد. "
            "جرب تكبّر الميزانية شوية، أو غيّر المنطقة، أو نوع الوحدة، وابعتلي تاني."
        )
    else:
        text = (
            "Couldn't find a best-price match for your request in time. "
            "Try raising the budget a little, or change the area or unit type, and send again."
        )
    return {
        "response": text,
        "properties": [],
        "ui_actions": [],
        "show_upsell": False,
        "ui_primitive_descriptor": "free_best_price_timeout",
        "primitive_data": {"reason": "search_timeout", "language": lang},
        "detected_language": lang,
    }
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
    # DB id of the just-saved assistant ChatMessage row, so the frontend
    # can offer a "flag this answer" affordance. None for the error/auth
    # branches that never reach the persistence step.
    message_id: Optional[int] = None
    # Verifier disclosure — when the Wolf path's claim verifier flagged
    # an issue and auto-rewrote the response, surface that so the user
    # knows there was a correction. Empty dict for the free path (which
    # doesn't run the verifier).
    #   { "auto_corrected": bool, "fix_count": int }
    verification: Optional[Dict[str, Any]] = None


# Admin email allowlist — mirrors the frontend's check in app/chat/page.tsx
# so an admin who hasn't been flagged role='admin' in the DB can still
# trigger the simulate_tier override.
_ADMIN_EMAILS = {
    "mustafa@osool.com",
    "mustafa@osool.eg",
    "hani@osool.com",
    "hani@osool.eg",
}


def _is_admin_user(user: Optional[User]) -> bool:
    """True iff `user` has admin role OR is in the hard-coded admin allowlist."""
    if user is None:
        return False
    if (getattr(user, "role", "") or "").lower() == "admin":
        return True
    email = (getattr(user, "email", "") or "").lower().strip()
    return email in _ADMIN_EMAILS


def _viewer_kind(user: Optional[User], simulate_tier: Optional[str] = None) -> str:
    """
    Resolve the caller's effective tier for routing.

    Admin-only override: passing simulate_tier="free" forces the
    "free" routing path even for admins (whose subscription would
    normally land them on the premium Wolf path). This is the
    backend half of the /chat "Demo" toggle — letting Osool staff
    demo the zero-LLM free experience end-to-end without burning
    Anthropic credits. Non-admin callers can't escalate themselves;
    the param is silently ignored when present without admin privs.
    """
    if simulate_tier == "free" and _is_admin_user(user):
        return "free"

    if user is None:
        return "anonymous"
    if is_forced_free_test_user_email(getattr(user, "email", None)):
        return "free"
    tier = (getattr(user, "subscription_tier", "free") or "free").lower()
    if (getattr(user, "role", "") or "").lower() == "admin" or tier in {"premium", "admin"}:
        return "premium"
    return "free"

@router.post("/chat")
@limiter.limit(CHAT_RATE_LIMIT)
async def process_chat(
    chat_request: ChatRequest,
    request: Request,
    simulate_tier: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional),
) -> JSONResponse:
    """
    Main endpoint for the Chat Interface — authentication required.

    Anonymous callers get a 401 with `requires_auth=true` so the
    frontend can redirect them to /signup. The landing-page composer
    persists the user's prompt in localStorage before redirecting; the
    chat page re-submits it after sign-in.

    Query params:
        simulate_tier: "free" → admin-only override forcing the free
            routing path. Useful for end-to-end demos without burning
            Anthropic credits. Ignored when caller is not admin.

    Rate limit: CHAT_RATE_LIMIT (30/minute) keyed by user_id when authed.

    Returns JSONResponse explicitly (not a Pydantic model via
    response_model) because the slowapi limiter has headers_enabled=True
    and only accepts a starlette.Response instance.
    """
    # Auth gate — anonymous chat is not available. Customers must sign
    # in / sign up first; the frontend persists their prompt and replays
    # it after auth.
    if user is None:
        return JSONResponse(
            status_code=401,
            content={
                "type": "error",
                "error": "authentication_required",
                "detail": "Sign in to chat with Osool.",
                "requires_auth": True,
                "next": "/chat",
            },
        )

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

    # A6 — lead scoring runs INLINE (cheap, deterministic, swallows its
    # own exceptions). Doing it inline keeps the DB session simple — the
    # alternative (asyncio.create_task) would race with the chat path's
    # later commits on the same session. Cost: ~1-3ms per turn.
    if user is not None:
        try:
            from app.services.lead_scoring import update_lead_score_for_turn
            await update_lead_score_for_turn(db, user, chat_request.message)
        except Exception:
            logger.exception("Lead scoring threw; chat path continues unaffected")

    try:
        kind = _viewer_kind(user, simulate_tier=simulate_tier)

        if kind in {"anonymous", "free"}:
            # Free-tier policy: ONE best price in the user's language. If the
            # underlying scoped SQL (correlated devloper-avg subqueries) blows
            # past 20s on a niche criterion with no matches, abort and return
            # a graceful in-language fallback so the user gets a real answer
            # instead of the browser-side "Could not reach Osool" timeout.
            try:
                payload = await asyncio.wait_for(
                    build_best_price_free_payload(
                        db, chat_request.message, chat_request.language
                    ),
                    timeout=_FREE_PATH_TIMEOUT_S,
                )
            except asyncio.TimeoutError:
                logger.warning(
                    "Free-tier best-price search exceeded %ss for session=%s msg=%r — returning fallback",
                    _FREE_PATH_TIMEOUT_S,
                    chat_request.session_id,
                    (chat_request.message or "")[:80],
                )
                # Roll back any partial state from the cancelled query so the
                # remaining commits in this handler (the assistant message) succeed.
                try:
                    await db.rollback()
                except Exception:
                    pass
                payload = _free_path_timeout_payload(chat_request.message)
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
            await db.refresh(ai_msg)

            return JSONResponse(
                content=ChatResponse(
                    type="success",
                    text=response_text,
                    properties=properties,
                    show_upsell=show_upsell,
                    ui_actions=ui_actions,
                    ui_primitive_descriptor=ui_primitive_descriptor,
                    primitive_data=primitive_data,
                    message_id=ai_msg.id,
                ).model_dump()
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

        # Surface verifier disclosure to the frontend so the user can see
        # when the AI's first draft was auto-corrected. Slim payload: never
        # leak the original (hallucinated) text, just the fact that we
        # caught something. Full audit lives in HallucinationFlag.
        verif_raw = result.get("verification") or {}
        verification_out: Optional[Dict[str, Any]] = None
        if verif_raw:
            corrections = verif_raw.get("corrections") or []
            if verif_raw.get("rewritten") or corrections:
                verification_out = {
                    "auto_corrected": bool(verif_raw.get("rewritten")),
                    "fix_count": len(corrections),
                }

        ai_msg = ChatMessage(
            session_id=chat_request.session_id,
            user_id=user.id if user else None,
            role="assistant",
            content=response_text,
        )
        db.add(ai_msg)
        await db.commit()
        await db.refresh(ai_msg)

        return JSONResponse(
            content=ChatResponse(
                type="success",
                text=response_text,
                properties=properties,
                show_upsell=False,
                ui_actions=ui_actions,
                message_id=ai_msg.id,
                verification=verification_out,
            ).model_dump()
        )

    except Exception as e:
        await db.rollback()
        logger.exception(
            "process_chat failed for session=%s viewer=%s tier=%s: %s",
            chat_request.session_id,
            getattr(user, "email", "anon"),
            simulate_tier,
            e,
        )
        raise HTTPException(status_code=500, detail=str(e))
