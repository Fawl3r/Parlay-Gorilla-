"""API-Sports team catalog cache (per sport/league/season)."""

from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, Index, Integer, String
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.database.session import Base
from app.database.types import GUID


class ApisportsTeam(Base):
    """Cached team catalog from API-Sports (teams per sport/league/season)."""

    __tablename__ = "apisports_teams"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    sport = Column(String(32), nullable=False, index=True)
    league_id = Column(Integer, nullable=True, index=True)
    team_id = Column(Integer, nullable=False, index=True)
    season = Column(String(16), nullable=True, index=True)
    name = Column(String(256), nullable=True)
    normalized_name = Column(String(256), nullable=True, index=True)
    payload_json = Column(JSON().with_variant(JSONB(), "postgresql"), nullable=False)
    source = Column(String(32), nullable=False, default="api_sports")
    last_fetched_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    stale_after_seconds = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_apisports_teams_sport_team", "sport", "team_id"),
        Index("idx_apisports_teams_sport_league_season", "sport", "league_id", "season"),
        Index("idx_apisports_teams_sport_team_season", "sport", "team_id", "season", unique=True),
    )
