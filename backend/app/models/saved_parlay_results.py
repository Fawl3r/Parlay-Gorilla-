"""Saved parlay results model for tracking outcomes of user-saved parlays.

This is separate from `parlay_results`:
- `parlay_results` tracks AI-generated parlay generation history (`parlays` table).
- `saved_parlay_results` tracks outcomes for `saved_parlays` (custom + AI-saved).
"""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, JSON, String
from sqlalchemy.sql import func

from app.database.session import Base
from app.database.types import GUID


class SavedParlayResult(Base):
    """Outcome tracking for a SavedParlay."""

    __tablename__ = "saved_parlay_results"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    saved_parlay_id = Column(GUID(), ForeignKey("saved_parlays.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    parlay_type = Column(String(20), nullable=False, index=True)  # custom | ai_generated
    num_legs = Column(Integer, nullable=False)

    # Overall outcome
    hit = Column(Boolean, nullable=True)  # True if won, False if lost, None if pending/push-only

    # Counts (push legs are excluded from these counts)
    legs_hit = Column(Integer, default=0)
    legs_missed = Column(Integer, default=0)

    # Per-leg outcomes
    leg_results = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_saved_parlay_results_saved", "saved_parlay_id"),
        Index("idx_saved_parlay_results_user_created", "user_id", "created_at"),
        Index("idx_saved_parlay_results_hit", "hit"),
        Index("idx_saved_parlay_results_type", "parlay_type"),
    )

    def __repr__(self) -> str:  # pragma: no cover
        status = "pending" if self.hit is None else ("hit" if self.hit else "missed")
        return f"<SavedParlayResult(id={self.id}, saved_parlay_id={self.saved_parlay_id}, {status})>"


