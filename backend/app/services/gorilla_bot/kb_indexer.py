"""
Knowledgebase indexing for Gorilla Bot.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
import hashlib
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.gorilla_bot_kb_chunk import GorillaBotKnowledgeChunk, GORILLA_BOT_EMBEDDING_DIM
from app.services.gorilla_bot.kb_chunker import GorillaBotChunker
from app.services.gorilla_bot.kb_repository import GorillaBotKnowledgeRepository
from app.services.gorilla_bot.openai_client import GorillaBotOpenAIClient

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GorillaBotSourceDocument:
    source_path: str
    title: str
    content: str
    checksum: str
    source_url: Optional[str]


@dataclass(frozen=True)
class GorillaBotIndexSummary:
    total_documents: int
    indexed_documents: int
    skipped_documents: int
    total_chunks: int


class GorillaBotPathResolver:
    def resolve_repo_root(self) -> Path:
        current = Path(__file__).resolve()
        for parent in current.parents:
            if parent.name == "backend":
                return parent.parent
        return Path.cwd()

    def resolve_kb_path(self, kb_path: str) -> Path:
        root = Path(kb_path)
        if root.is_absolute():
            return root
        return self.resolve_repo_root() / root


class GorillaBotChecksumService:
    def build_checksum(self, content: str) -> str:
        digest = hashlib.sha256()
        digest.update((content or "").encode("utf-8"))
        return digest.hexdigest()


class GorillaBotDocumentLoader:
    def __init__(self, checksum_service: GorillaBotChecksumService):
        self._checksum_service = checksum_service

    def load_documents(self, root_path: Path, repo_root: Path) -> List[GorillaBotSourceDocument]:
        if not root_path.exists():
            raise FileNotFoundError(f"Gorilla Bot KB path not found: {root_path}")

        documents: List[GorillaBotSourceDocument] = []
        for path in sorted(root_path.rglob("*.md")):
            content = path.read_text(encoding="utf-8").strip()
            if not content:
                continue
            title = self._extract_title(content, path)
            checksum = self._checksum_service.build_checksum(content)
            source_path = self._relative_path(path, repo_root)
            documents.append(
                GorillaBotSourceDocument(
                    source_path=source_path,
                    title=title,
                    content=content,
                    checksum=checksum,
                    source_url=None,
                )
            )
        return documents

    def _extract_title(self, content: str, path: Path) -> str:
        for line in content.splitlines():
            if line.strip().startswith("# "):
                return line.strip()[2:].strip()
        return path.stem.replace("_", " ").replace("-", " ").title()

    def _relative_path(self, path: Path, repo_root: Path) -> str:
        try:
            return str(path.relative_to(repo_root))
        except ValueError:
            return str(path)


class GorillaBotKnowledgeBaseIndexer:
    """Index Markdown documents into Postgres + pgvector."""

    def __init__(
        self,
        db: AsyncSession,
        openai_client: GorillaBotOpenAIClient,
        chunker: GorillaBotChunker,
        repository: GorillaBotKnowledgeRepository,
    ):
        self._db = db
        self._openai_client = openai_client
        self._chunker = chunker
        self._repository = repository
        self._path_resolver = GorillaBotPathResolver()
        self._document_loader = GorillaBotDocumentLoader(GorillaBotChecksumService())
        self._batch_size = int(settings.gorilla_bot_embedding_batch_size)

    async def index_from_settings(self, force: bool = False) -> GorillaBotIndexSummary:
        root_path = self._path_resolver.resolve_kb_path(settings.gorilla_bot_kb_path)
        repo_root = self._path_resolver.resolve_repo_root()
        documents = self._document_loader.load_documents(root_path, repo_root)

        total_chunks = 0
        indexed = 0
        skipped = 0

        for document in documents:
            was_indexed, chunk_count = await self._index_document(document, force=force)
            total_chunks += chunk_count
            if was_indexed:
                indexed += 1
            else:
                skipped += 1

        return GorillaBotIndexSummary(
            total_documents=len(documents),
            indexed_documents=indexed,
            skipped_documents=skipped,
            total_chunks=total_chunks,
        )

    async def _index_document(self, document: GorillaBotSourceDocument, force: bool) -> tuple[bool, int]:
        existing = await self._repository.get_document_by_path(document.source_path)
        if existing and existing.checksum == document.checksum and not force:
            return False, 0

        chunks = self._chunker.chunk(document.content)
        if not chunks:
            return False, 0

        embeddings = await self._embed_chunks([chunk.content for chunk in chunks])
        if len(embeddings) != len(chunks):
            raise RuntimeError("Embedding response size mismatch for Gorilla Bot KB.")

        db_document = await self._repository.upsert_document(
            source_path=document.source_path,
            title=document.title,
            checksum=document.checksum,
            source_url=document.source_url,
            is_active=True,
        )
        db_document.last_indexed_at = datetime.now(timezone.utc)

        db_chunks = [
            GorillaBotKnowledgeChunk(
                document_id=db_document.id,
                chunk_index=chunk.index,
                content=chunk.content,
                token_count=chunk.token_estimate,
                embedding=embedding,
                embedding_json=embedding,
            )
            for chunk, embedding in zip(chunks, embeddings)
        ]

        await self._repository.replace_chunks(db_document.id, db_chunks)
        await self._db.commit()
        return True, len(db_chunks)

    async def _embed_chunks(self, texts: List[str]) -> List[List[float]]:
        if not self._openai_client.enabled:
            raise RuntimeError("OpenAI is disabled. Cannot embed Gorilla Bot KB.")

        embeddings: List[List[float]] = []
        for batch in self._split_batches(texts, self._batch_size):
            response = await self._openai_client.embed_texts(batch)
            for embedding in response:
                self._validate_embedding(embedding)
            embeddings.extend(response)
        return embeddings

    def _split_batches(self, items: List[str], batch_size: int) -> List[List[str]]:
        size = max(1, batch_size)
        return [items[i : i + size] for i in range(0, len(items), size)]

    def _validate_embedding(self, embedding: List[float]) -> None:
        if len(embedding) != GORILLA_BOT_EMBEDDING_DIM:
            raise ValueError(
                f"Embedding dimension mismatch: expected {GORILLA_BOT_EMBEDDING_DIM}, got {len(embedding)}"
            )
