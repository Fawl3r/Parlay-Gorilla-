"""
Gorilla Bot conversation model.
"""

from sqlalchemy import Column, String, DateTime, Boolean, Index, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database.session import Base
from app.database.types import GUID


class GorillaBotConversation(Base):
    """Conversation container for Gorilla Bot chats."""

    __tablename__ = "gorilla_bot_conversations"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(120), nullable=True)
    is_archived = Column(Boolean, default=False, nullable=False)
    last_message_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    messages = relationship(
        "GorillaBotMessage",
        back_populates="conversation",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_gorilla_bot_conversation_user_updated", "user_id", "updated_at"),
        Index("idx_gorilla_bot_conversation_user_last_msg", "user_id", "last_message_at"),
    )

    def __repr__(self) -> str:
        return f"<GorillaBotConversation(id={self.id}, user_id={self.user_id})>"
