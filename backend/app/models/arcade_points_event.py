"""Arcade points event model - one row per awarded win."""

from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, UniqueConstraint
from sqlalchemy.sql import func

from app.database.session import Base
from app.database.types import GUID


class ArcadePointsEvent(Base):
    """One-time event recording when points were awarded for a verified win."""

    __tablename__ = "arcade_points_events"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    saved_parlay_id = Column(GUID(), ForeignKey("saved_parlays.id", ondelete="CASCADE"), nullable=False, index=True)
    saved_parlay_result_id = Column(
        GUID(), ForeignKey("saved_parlay_results.id", ondelete="CASCADE"), nullable=False, index=True
    )

    num_legs = Column(Integer, nullable=False)
    points_awarded = Column(Integer, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("saved_parlay_result_id", name="unique_arcade_points_event_result"),
        Index("idx_arcade_points_events_user_created", "user_id", "created_at"),
        Index("idx_arcade_points_events_created", "created_at"),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ArcadePointsEvent(id={self.id}, user_id={self.user_id}, points={self.points_awarded})>"

