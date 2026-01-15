"""
Gorilla Bot knowledgebase chunk model.
"""

from sqlalchemy import Column, DateTime, Text, Integer, Index, ForeignKey, JSON
from sqlalchemy.sql import func
import uuid

from pgvector.sqlalchemy import Vector

from app.database.session import Base
from app.database.types import GUID

GORILLA_BOT_EMBEDDING_DIM = 1536


class GorillaBotKnowledgeChunk(Base):
    """Chunked knowledgebase entry with embedding for semantic retrieval."""

    __tablename__ = "gorilla_bot_kb_chunks"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    document_id = Column(GUID(), ForeignKey("gorilla_bot_kb_documents.id"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    token_count = Column(Integer, nullable=True)
    embedding = Column(Vector(GORILLA_BOT_EMBEDDING_DIM), nullable=True)
    embedding_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_gorilla_bot_kb_chunk_doc_index", "document_id", "chunk_index"),
    )

    def __repr__(self) -> str:
        return f"<GorillaBotKnowledgeChunk(doc_id={self.document_id}, idx={self.chunk_index})>"
