"""Cached season state per sport (computed_at_utc, counts, state)."""

from __future__ import annotations

from sqlalchemy import Column, String, DateTime, Integer
from sqlalchemy.sql import func

from app.database.session import Base


class SportSeasonState(Base):
    """Cached season state per sport with TTL (e.g. 1h)."""

    __tablename__ = "sport_season_state"

    sport = Column(String(16), primary_key=True)
    state = Column(String(32), nullable=False)
    computed_at_utc = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    recent_final_count = Column(Integer, nullable=False, default=0)
    near_scheduled_count = Column(Integer, nullable=False, default=0)
    post_scheduled_count = Column(Integer, nullable=False, default=0)
