"""Web Push subscription model.

Stores opt-in browser PushSubscription details (endpoint + keys) so the backend
can send Web Push notifications (e.g., when new game analyses are generated).
"""

from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, Index, String, Text
from sqlalchemy.sql import func

from app.database.session import Base
from app.database.types import GUID


class PushSubscription(Base):
    """Persisted Web Push subscription (anonymous by default)."""

    __tablename__ = "push_subscriptions"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # PushSubscription.endpoint can be long; store as TEXT.
    endpoint = Column(Text, unique=True, nullable=False)

    # PushSubscription keys (base64 strings)
    p256dh = Column(String(length=255), nullable=False)
    auth = Column(String(length=255), nullable=False)

    # Optional expiration time (some browsers set this, many return null)
    expiration_time = Column(DateTime(timezone=True), nullable=True)

    # Basic context for debugging/cleanup
    user_agent = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_push_subscriptions_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<PushSubscription(id={self.id}, endpoint={self.endpoint[:32]}...)>"


