"""Saved parlay model for user-saved custom and AI parlays.

This table is distinct from `parlays` (AI generation history used for analytics).
`saved_parlays` is the durable "user clicked Save" store that powers the dashboard's
Saved Parlays section and (for custom parlays only) Solana inscription anchoring.
"""

from __future__ import annotations

import enum
import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.session import Base
from app.database.types import GUID


class SavedParlayType(str, enum.Enum):
    """Saved parlay type: user-built custom vs AI-generated."""

    custom = "custom"
    ai_generated = "ai_generated"


class InscriptionStatus(str, enum.Enum):
    """Solana inscription lifecycle status."""

    none = "none"
    queued = "queued"
    confirmed = "confirmed"
    failed = "failed"


class SavedParlay(Base):
    """User-saved parlay (custom or AI-generated)."""

    __tablename__ = "saved_parlays"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)

    # Required classification.
    parlay_type = Column(String(20), nullable=False, index=True)

    title = Column(String(200), nullable=False)
    legs = Column(JSON, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    version = Column(Integer, nullable=False, default=1)

    # Deterministic canonical content hash (sha256 hex).
    content_hash = Column(String(64), nullable=False)

    # Inscription fields (hash-only proof payload; user-selected).
    inscription_status = Column(String(20), nullable=False, default=InscriptionStatus.none.value)
    inscription_hash = Column(String(64), nullable=True)
    inscription_tx = Column(String(128), nullable=True)
    inscription_error = Column(Text, nullable=True)
    inscribed_at = Column(DateTime(timezone=True), nullable=True)
    # Tracks whether the user's inscription quota was consumed for this saved parlay.
    # This prevents retries from consuming quota multiple times.
    inscription_quota_consumed = Column(Boolean, nullable=False, default=False)
    # Tracks whether the user spent credits for this inscription (premium overage).
    # This prevents retries from charging credits multiple times.
    inscription_credits_consumed = Column(Boolean, nullable=False, default=False)

    # Settlement fields (added via migration 039)
    status = Column(String, nullable=False, server_default="PENDING")
    settled_at = Column(DateTime(timezone=True), nullable=True)
    public_alias = Column(String, nullable=True)
    is_public = Column(Boolean, nullable=False, server_default="false")

    user = relationship("User", backref="saved_parlays")

    __table_args__ = (
        Index("idx_saved_parlays_user_created", "user_id", "created_at"),
        Index("idx_saved_parlays_user_type", "user_id", "parlay_type"),
        Index("idx_saved_parlays_inscription_status", "inscription_status"),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<SavedParlay(id={self.id}, type={self.parlay_type}, v={self.version})>"



