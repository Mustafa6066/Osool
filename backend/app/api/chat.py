from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
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
async def process_chat(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Main endpoint for the Chat Interface.
    Routes free users through the Zero-Token Local Path.
    """

    # Track session count for Depth Limit trigger
    session_count = db.query(ChatMessage).filter(
        ChatMessage.session_id == request.session_id,
        ChatMessage.role == "user"
    ).count()

    # Save user message
    user_msg = ChatMessage(
        session_id=request.session_id,
        role="user",
        content=request.message
    )
    db.add(user_msg)
    db.commit()

    try:
        if request.is_free_user:
            # Route through Zero-Token AI Engine
            response_data = local_router.process_query(
                query=request.message,
                session_count=session_count,
                db=db
            )

            # Save AI response
            ai_msg = ChatMessage(
                session_id=request.session_id,
                role="assistant",
                content=response_data["text"]
            )
            db.add(ai_msg)
            db.commit()

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
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
