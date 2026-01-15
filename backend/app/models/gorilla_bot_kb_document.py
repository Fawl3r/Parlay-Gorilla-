"""
Gorilla Bot knowledgebase document model.
"""

from sqlalchemy import Column, String, DateTime, Boolean, Index
from sqlalchemy.sql import func
import uuid

from app.database.session import Base
from app.database.types import GUID


class GorillaBotKnowledgeDocument(Base):
    """Source document tracked for Gorilla Bot knowledgebase indexing."""

    __tablename__ = "gorilla_bot_kb_documents"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    source_path = Column(String(255), nullable=False, unique=True, index=True)
    title = Column(String(255), nullable=False)
    source_url = Column(String(500), nullable=True)
    checksum = Column(String(64), nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    last_indexed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_gorilla_bot_kb_doc_active", "is_active"),
        Index("idx_gorilla_bot_kb_doc_checksum", "checksum"),
    )

    def __repr__(self) -> str:
        return f"<GorillaBotKnowledgeDocument(path={self.source_path})>"
