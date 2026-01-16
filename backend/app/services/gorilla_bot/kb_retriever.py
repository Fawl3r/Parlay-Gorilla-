"""
Knowledgebase retriever for Gorilla Bot.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List
import math

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database.session import AsyncSessionLocal
from app.models.gorilla_bot_kb_chunk import GorillaBotKnowledgeChunk
from app.models.gorilla_bot_kb_document import GorillaBotKnowledgeDocument
from app.services.gorilla_bot.openai_client import GorillaBotOpenAIClient
from app.services.gorilla_bot.prompt_builder import GorillaBotContextSnippet


@dataclass(frozen=True)
class GorillaBotRetrievalResult:
    snippet: GorillaBotContextSnippet
    score: float


class GorillaBotSimilarityCalculator:
    def cosine_similarity(self, a: List[float], b: List[float]) -> float:
        if not a or not b or len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)


class GorillaBotKnowledgeRetriever:
    """Retrieve knowledgebase snippets using vector similarity."""

    def __init__(
        self,
        openai_client: GorillaBotOpenAIClient,
        *,
        session_factory: Callable[[], AsyncSession] = AsyncSessionLocal,
    ):
        self._openai_client = openai_client
        self._session_factory = session_factory
        self._similarity = GorillaBotSimilarityCalculator()

    async def retrieve(self, query: str) -> List[GorillaBotContextSnippet]:
        if not self._openai_client.enabled:
            return []
        embedding = await self._openai_client.embed_texts([query])
        if not embedding:
            return []
        vector = embedding[0]

        # IMPORTANT: Use a separate session for retrieval.
        #
        # A failed SELECT in Postgres aborts the current transaction. If we did this
        # on the request's primary session (which is also writing conversation/messages),
        # we'd need to rollback and would lose those writes + expire ORM objects,
        # causing MissingGreenlet errors in async contexts.
        async with self._session_factory() as db:
            if db.bind and db.bind.dialect.name == "postgresql":
                return await self._retrieve_postgres(db, vector)
            return await self._retrieve_fallback(db, vector)

    async def _retrieve_postgres(self, db: AsyncSession, vector: List[float]) -> List[GorillaBotContextSnippet]:
        """Retrieve using PostgreSQL vector search, fallback to JSON if pgvector unavailable."""
        try:
            # Try vector search first (requires pgvector extension)
            distance = GorillaBotKnowledgeChunk.embedding.cosine_distance(vector)
            stmt = (
                select(GorillaBotKnowledgeChunk, GorillaBotKnowledgeDocument, (1 - distance).label("score"))
                .join(GorillaBotKnowledgeDocument, GorillaBotKnowledgeChunk.document_id == GorillaBotKnowledgeDocument.id)
                .where(GorillaBotKnowledgeDocument.is_active == True)  # noqa: E712
                .order_by(distance.asc())
                .limit(int(settings.gorilla_bot_max_context_chunks))
            )
            result = await db.execute(stmt)
            rows = result.all()
            return [self._row_to_snippet(row) for row in rows]
        except Exception:
            # Rollback the failed transaction before fallback (local session only)
            await db.rollback()
            # Fallback to JSON-based similarity if pgvector is not available
            return await self._retrieve_fallback(db, vector)

    async def _retrieve_fallback(self, db: AsyncSession, vector: List[float]) -> List[GorillaBotContextSnippet]:
        # Select only columns that exist (avoid embedding column if pgvector not available)
        stmt = (
            select(
                GorillaBotKnowledgeChunk.id,
                GorillaBotKnowledgeChunk.document_id,
                GorillaBotKnowledgeChunk.chunk_index,
                GorillaBotKnowledgeChunk.content,
                GorillaBotKnowledgeChunk.token_count,
                GorillaBotKnowledgeChunk.embedding_json,
                GorillaBotKnowledgeDocument.id.label("doc_id"),
                GorillaBotKnowledgeDocument.title,
                GorillaBotKnowledgeDocument.source_path,
                GorillaBotKnowledgeDocument.source_url,
            )
            .join(GorillaBotKnowledgeDocument, GorillaBotKnowledgeChunk.document_id == GorillaBotKnowledgeDocument.id)
            .where(GorillaBotKnowledgeDocument.is_active == True)  # noqa: E712
        )
        result = await db.execute(stmt)
        rows = result.all()

        scored: List[GorillaBotContextSnippet] = []
        for row in rows:
            # Handle both tuple (from explicit select) and object (from model select) results
            if hasattr(row, 'content'):
                # Object result
                embedding = getattr(row, 'embedding_json', None) or []
                content = row.content
                doc_title = row.title if hasattr(row, 'title') else ""
                doc_source_path = row.source_path if hasattr(row, 'source_path') else ""
                doc_source_url = row.source_url if hasattr(row, 'source_url') else None
            else:
                # Tuple result from explicit select
                _, _, _, content, _, embedding_json, _, title, source_path, source_url = row
                embedding = embedding_json or []
                doc_title = title
                doc_source_path = source_path
                doc_source_url = source_url
            
            score = self._similarity.cosine_similarity(vector, list(embedding)) if embedding else 0.0
            scored.append(
                GorillaBotContextSnippet(
                    title=doc_title,
                    content=content,
                    source_path=doc_source_path,
                    source_url=doc_source_url,
                    score=score,
                )
            )

        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[: int(settings.gorilla_bot_max_context_chunks)]

    def _row_to_snippet(self, row) -> GorillaBotContextSnippet:
        chunk, doc, score = row
        return GorillaBotContextSnippet(
            title=doc.title,
            content=chunk.content,
            source_path=doc.source_path,
            source_url=doc.source_url,
            score=float(score or 0.0),
        )
