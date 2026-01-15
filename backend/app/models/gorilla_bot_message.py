"""
Gorilla Bot message model.
"""

from sqlalchemy import Column, String, DateTime, Text, JSON, Index, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database.session import Base
from app.database.types import GUID


class GorillaBotMessage(Base):
    """Individual message within a Gorilla Bot conversation."""

    __tablename__ = "gorilla_bot_messages"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(GUID(), ForeignKey("gorilla_bot_conversations.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # user | assistant | system
    content = Column(Text, nullable=False)
    citations = Column(JSON, nullable=True)  # list of {title, url, source_path}
    token_count = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    conversation = relationship("GorillaBotConversation", back_populates="messages")

    __table_args__ = (
        Index("idx_gorilla_bot_message_conversation_role", "conversation_id", "role"),
        Index("idx_gorilla_bot_message_conversation_created", "conversation_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<GorillaBotMessage(id={self.id}, role={self.role})>"
