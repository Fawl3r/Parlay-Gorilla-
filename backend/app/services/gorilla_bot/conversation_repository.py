"""
Conversation repository for Gorilla Bot.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.gorilla_bot_conversation import GorillaBotConversation


class GorillaBotConversationRepository:
    """Persistence helpers for Gorilla Bot conversations."""

    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_by_id(self, conversation_id, user_id) -> Optional[GorillaBotConversation]:
        result = await self._db.execute(
            select(GorillaBotConversation)
            .where(GorillaBotConversation.id == conversation_id)
            .where(GorillaBotConversation.user_id == user_id)
            .where(GorillaBotConversation.is_archived == False)  # noqa: E712
        )
        return result.scalar_one_or_none()

    async def list_for_user(self, user_id, limit: int = 20) -> List[GorillaBotConversation]:
        result = await self._db.execute(
            select(GorillaBotConversation)
            .where(GorillaBotConversation.user_id == user_id)
            .where(GorillaBotConversation.is_archived == False)  # noqa: E712
            .order_by(func.coalesce(GorillaBotConversation.last_message_at, GorillaBotConversation.created_at).desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create(self, user_id, title: Optional[str] = None) -> GorillaBotConversation:
        conversation = GorillaBotConversation(user_id=user_id, title=title)
        self._db.add(conversation)
        await self._db.flush()
        return conversation

    async def mark_last_message(self, conversation_id, timestamp: datetime) -> None:
        await self._db.execute(
            update(GorillaBotConversation)
            .where(GorillaBotConversation.id == conversation_id)
            .values(last_message_at=timestamp)
        )

    async def archive(self, conversation_id, user_id) -> bool:
        result = await self._db.execute(
            update(GorillaBotConversation)
            .where(GorillaBotConversation.id == conversation_id)
            .where(GorillaBotConversation.user_id == user_id)
            .values(is_archived=True)
        )
        return result.rowcount > 0
