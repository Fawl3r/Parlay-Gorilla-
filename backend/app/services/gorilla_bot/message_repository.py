"""
Message repository for Gorilla Bot.
"""

from __future__ import annotations

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.gorilla_bot_message import GorillaBotMessage


class GorillaBotMessageRepository:
    """Persistence helpers for Gorilla Bot messages."""

    def __init__(self, db: AsyncSession):
        self._db = db

    async def add_message(
        self,
        conversation_id,
        role: str,
        content: str,
        citations: Optional[list] = None,
        token_count: Optional[int] = None,
    ) -> GorillaBotMessage:
        message = GorillaBotMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
            citations=citations,
            token_count=token_count,
        )
        self._db.add(message)
        await self._db.flush()
        return message

    async def list_messages(self, conversation_id, limit: int = 50) -> List[GorillaBotMessage]:
        result = await self._db.execute(
            select(GorillaBotMessage)
            .where(GorillaBotMessage.conversation_id == conversation_id)
            .order_by(GorillaBotMessage.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())
