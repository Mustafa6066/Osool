from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from app.database import get_db
from app.ai_engine.local_router import local_router
from app.models import ChatMessage

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    session_id: str
    is_free_user: bool = True

class ChatResponse(BaseModel):
    type: str
    text: str
    properties: List[Dict[str, Any]]
    show_upsell: bool

@router.post("/chat", response_model=ChatResponse)
async def process_chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """
    Main endpoint for the Chat Interface.
    Routes free users through the Zero-Token Local Path.
    """

    # Track session count for Depth Limit trigger
    session_count_stmt = select(func.count()).where(
        ChatMessage.session_id == request.session_id,
        ChatMessage.role == "user"
    )
    session_count = (await db.execute(session_count_stmt)).scalar_one()

    # Load prior user messages (newest first) so the local router can merge
    # entities like area/compound/budget from earlier turns. Without this the
    # chat becomes effectively stateless and loops on clarification prompts.
    history_stmt = (
        select(ChatMessage.content)
        .where(
            ChatMessage.session_id == request.session_id,
            ChatMessage.role == "user",
        )
        .order_by(ChatMessage.created_at.desc())
        .limit(6)
    )
    previous_user_messages = [row[0] for row in (await db.execute(history_stmt)).all()]

    # Save user message
    user_msg = ChatMessage(
        session_id=request.session_id,
        role="user",
        content=request.message
    )
    db.add(user_msg)
    await db.commit()

    try:
        if request.is_free_user:
            # Route through Zero-Token AI Engine
            response_data = await local_router.process_query_async(
                query=request.message,
                session_count=session_count,
                db=db,
                previous_queries=previous_user_messages,
            )

            # Save AI response
            ai_msg = ChatMessage(
                session_id=request.session_id,
                role="assistant",
                content=response_data["text"]
            )
            db.add(ai_msg)
            await db.commit()

            return ChatResponse(**response_data)
        else:
            # Paid User Path: Call Premium LLM Engine (Claude/OpenAI)
            # This is outside the scope of the Zero-Token Free Path implementation
            return ChatResponse(
                type="success",
                text="Premium AI Engine Response (Not implemented in this step)",
                properties=[],
                show_upsell=False
            )

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
