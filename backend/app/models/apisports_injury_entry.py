"""Per-player injury rows from API-Sports for analysis UI (player names + status)."""

from __future__ import annotations

import uuid
from sqlalchemy import Column, String, Integer, DateTime, Text, Index, JSON
from sqlalchemy.dialects.postgresql import JSONB
from app.database.session import Base
from app.database.types import GUID


class ApisportsInjuryEntry(Base):
    """One row per player injury for queryability and display (name, status, type, etc.)."""

    __tablename__ = "apisports_injury_entries"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    sport = Column(String(32), nullable=False, index=True)
    league_id = Column(Integer, nullable=True, index=True)
    apisports_team_id = Column(Integer, nullable=False, index=True)
    apisports_player_id = Column(Integer, nullable=True, index=True)
    player_name = Column(String(256), nullable=False, index=True)
    status = Column(String(64), nullable=False)  # out, questionable, doubtful, probable, day-to-day
    injury_type = Column(String(128), nullable=True)
    description = Column(Text, nullable=True)
    reported_at = Column(DateTime(timezone=True), nullable=True)
    fetched_at = Column(DateTime(timezone=True), nullable=False)
    source = Column(String(32), nullable=False, default="apisports")
    raw_payload = Column(JSON().with_variant(JSONB(), "postgresql"), nullable=True)

    __table_args__ = (
        Index("idx_injury_entries_sport_team_fetched", "sport", "apisports_team_id", "fetched_at"),
    )
