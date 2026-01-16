"""
Database repository for Gorilla Bot knowledgebase.
"""

from __future__ import annotations

from typing import Iterable, Optional, Sequence
from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.gorilla_bot_kb_document import GorillaBotKnowledgeDocument
from app.models.gorilla_bot_kb_chunk import GorillaBotKnowledgeChunk


class GorillaBotKnowledgeRepository:
    """Persistence layer for Gorilla Bot knowledgebase documents and chunks."""

    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_document_by_path(self, source_path: str) -> Optional[GorillaBotKnowledgeDocument]:
        result = await self._db.execute(
            select(GorillaBotKnowledgeDocument).where(GorillaBotKnowledgeDocument.source_path == source_path)
        )
        return result.scalar_one_or_none()

    async def upsert_document(
        self,
        source_path: str,
        title: str,
        checksum: str,
        source_url: Optional[str],
        is_active: bool = True,
    ) -> GorillaBotKnowledgeDocument:
        existing = await self.get_document_by_path(source_path)
        if existing:
            existing.title = title
            existing.checksum = checksum
            existing.source_url = source_url
            existing.is_active = is_active
            return existing

        document = GorillaBotKnowledgeDocument(
            source_path=source_path,
            title=title,
            checksum=checksum,
            source_url=source_url,
            is_active=is_active,
        )
        self._db.add(document)
        # Ensure the UUID primary key is populated before callers create related rows.
        # SQLAlchemy won't assign `default=uuid.uuid4` until flush/insert time.
        try:
            await self._db.flush()
        except IntegrityError:
            # If another process inserted the same source_path concurrently, fall back to fetching it.
            await self._db.rollback()
            existing = await self.get_document_by_path(source_path)
            if existing:
                existing.title = title
                existing.checksum = checksum
                existing.source_url = source_url
                existing.is_active = is_active
                return existing
            raise
        return document

    async def replace_chunks(
        self,
        document_id,
        chunks: Sequence[GorillaBotKnowledgeChunk],
    ) -> None:
        await self._db.execute(
            delete(GorillaBotKnowledgeChunk).where(GorillaBotKnowledgeChunk.document_id == document_id)
        )
        self._db.add_all(list(chunks))

    async def get_chunks_by_document(self, document_id) -> Iterable[GorillaBotKnowledgeChunk]:
        result = await self._db.execute(
            select(GorillaBotKnowledgeChunk)
            .where(GorillaBotKnowledgeChunk.document_id == document_id)
            .order_by(GorillaBotKnowledgeChunk.chunk_index.asc())
        )
        return result.scalars().all()
