"""Arcade points totals model - per-user aggregate for fast leaderboard queries."""

from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, UniqueConstraint
from sqlalchemy.sql import func

from app.database.session import Base
from app.database.types import GUID


class ArcadePointsTotals(Base):
    """Per-user aggregate of arcade points (denormalized for fast leaderboard queries)."""

    __tablename__ = "arcade_points_totals"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    total_points = Column(Integer, nullable=False, default=0)
    total_qualifying_wins = Column(Integer, nullable=False, default=0)
    last_win_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", name="unique_arcade_points_totals_user"),
        Index("idx_arcade_points_totals_points", "total_points"),
        Index("idx_arcade_points_totals_last_win", "last_win_at"),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ArcadePointsTotals(user_id={self.user_id}, points={self.total_points}, wins={self.total_qualifying_wins})>"

