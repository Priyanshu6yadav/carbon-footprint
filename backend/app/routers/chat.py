"""
CarbonTrack — Chat Assistant router.
Provides the /api/chat/sustainability endpoint for green suggestions.
Rate-limited per user/IP using SlowAPI.
"""
from typing import List
from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from pydantic import BaseModel, Field

from app.config import get_settings
from app.models.user import User
from app.services.auth_service import get_current_user
from app.services.ai_service import AIService

settings = get_settings()
limiter = Limiter(key_func=get_remote_address)
router = APIRouter(tags=["chat"])
ai_service = AIService()


class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str = Field(..., max_length=2000)


class ChatRequest(BaseModel):
    message: str = Field(..., max_length=1000)
    history: List[ChatMessage] = Field(default_factory=list)


class ChatResponse(BaseModel):
    reply: str


@router.post("/sustainability", response_model=ChatResponse)
@limiter.limit(settings.RATE_LIMIT_AI)
async def chat_sustainability_assistant(
    request: Request,
    body: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Interact with the sustainability chatbot. Rate-limited to protect token quota.
    Strictly filters out non-sustainability queries and hedges statistics.
    """
    history_payload = [{"role": msg.role, "content": msg.content} for msg in body.history]
    reply = await ai_service.chat_sustainability(body.message, history_payload)
    return ChatResponse(reply=reply)
