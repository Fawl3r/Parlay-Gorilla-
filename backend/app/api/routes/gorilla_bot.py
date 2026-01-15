"""
Gorilla Bot API routes.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_current_user, get_db
from app.middleware.rate_limiter import rate_limit
from app.models.user import User
from app.services.gorilla_bot.conversation_repository import GorillaBotConversationRepository
from app.services.gorilla_bot.message_repository import GorillaBotMessageRepository
from app.services.gorilla_bot.gorilla_bot_manager import GorillaBotManager

router = APIRouter()


class GorillaBotChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1200)
    conversation_id: Optional[str] = None


class GorillaBotCitationResponse(BaseModel):
    title: str
    source_path: str
    source_url: Optional[str] = None


class GorillaBotChatResponse(BaseModel):
    conversation_id: str
    message_id: str
    reply: str
    citations: List[GorillaBotCitationResponse]


class GorillaBotConversationSummaryResponse(BaseModel):
    id: str
    title: Optional[str]
    last_message_at: Optional[str]
    created_at: str

    model_config = {"from_attributes": True}


class GorillaBotMessageResponse(BaseModel):
    id: str
    role: str
    content: str
    citations: Optional[list]
    created_at: str

    model_config = {"from_attributes": True}


class GorillaBotConversationDetailResponse(BaseModel):
    conversation: GorillaBotConversationSummaryResponse
    messages: List[GorillaBotMessageResponse]


class GorillaBotDeleteResponse(BaseModel):
    message: str


class GorillaBotRequestParser:
    def parse_conversation_id(self, conversation_id: Optional[str]) -> Optional[uuid.UUID]:
        if not conversation_id:
            return None
        try:
            return uuid.UUID(str(conversation_id))
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid conversation_id format",
            ) from exc


@router.post("/gorilla-bot/chat", response_model=GorillaBotChatResponse)
@rate_limit("60/hour")
async def chat_gorilla_bot(
    request: Request,
    payload: GorillaBotChatRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _ = request
    if not settings.gorilla_bot_enabled:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Gorilla Bot is disabled.")

    parser = GorillaBotRequestParser()
    conversation_id = parser.parse_conversation_id(payload.conversation_id)
    manager = GorillaBotManager(db)

    try:
        result = await manager.chat(user, payload.message, conversation_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    return GorillaBotChatResponse(
        conversation_id=result.conversation_id,
        message_id=result.message_id,
        reply=result.reply,
        citations=[
            GorillaBotCitationResponse(
                title=citation.title,
                source_path=citation.source_path,
                source_url=citation.source_url,
            )
            for citation in result.citations
        ],
    )


@router.get("/gorilla-bot/conversations", response_model=List[GorillaBotConversationSummaryResponse])
@rate_limit("120/hour")
async def list_gorilla_bot_conversations(
    request: Request,
    limit: int = 20,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _ = request
    repository = GorillaBotConversationRepository(db)
    conversations = await repository.list_for_user(user.id, limit=min(50, max(1, limit)))
    return [
        GorillaBotConversationSummaryResponse(
            id=str(conversation.id),
            title=conversation.title,
            last_message_at=conversation.last_message_at.isoformat() if conversation.last_message_at else None,
            created_at=conversation.created_at.isoformat() if conversation.created_at else datetime.now().isoformat(),
        )
        for conversation in conversations
    ]


@router.get(
    "/gorilla-bot/conversations/{conversation_id}",
    response_model=GorillaBotConversationDetailResponse,
)
@rate_limit("120/hour")
async def get_gorilla_bot_conversation(
    request: Request,
    conversation_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _ = request
    parser = GorillaBotRequestParser()
    conversation_uuid = parser.parse_conversation_id(conversation_id)
    repository = GorillaBotConversationRepository(db)
    message_repo = GorillaBotMessageRepository(db)

    conversation = await repository.get_by_id(conversation_uuid, user.id)
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")

    messages = await message_repo.list_messages(conversation.id, limit=200)
    return GorillaBotConversationDetailResponse(
        conversation=GorillaBotConversationSummaryResponse(
            id=str(conversation.id),
            title=conversation.title,
            last_message_at=conversation.last_message_at.isoformat() if conversation.last_message_at else None,
            created_at=conversation.created_at.isoformat() if conversation.created_at else datetime.now().isoformat(),
        ),
        messages=[
            GorillaBotMessageResponse(
                id=str(message.id),
                role=message.role,
                content=message.content,
                citations=message.citations,
                created_at=message.created_at.isoformat() if message.created_at else datetime.now().isoformat(),
            )
            for message in messages
        ],
    )


@router.delete("/gorilla-bot/conversations/{conversation_id}", response_model=GorillaBotDeleteResponse)
@rate_limit("60/hour")
async def delete_gorilla_bot_conversation(
    request: Request,
    conversation_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _ = request
    parser = GorillaBotRequestParser()
    conversation_uuid = parser.parse_conversation_id(conversation_id)
    repository = GorillaBotConversationRepository(db)

    archived = await repository.archive(conversation_uuid, user.id)
    if not archived:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")

    await db.commit()
    return GorillaBotDeleteResponse(message="Conversation removed.")
