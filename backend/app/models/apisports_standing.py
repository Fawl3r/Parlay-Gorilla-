"""API-Sports standings cache (per league/season)."""

from __future__ import annotations

from sqlalchemy import Column, String, Integer, DateTime, Index
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
import uuid

from app.database.session import Base
from app.database.types import GUID


class ApisportsStanding(Base):
    """Cached standings from API-Sports."""

    __tablename__ = "apisports_standings"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    sport = Column(String(32), nullable=False, index=True)
    league_id = Column(Integer, nullable=False, index=True)
    season = Column(String(16), nullable=True, index=True)
    payload_json = Column(JSON().with_variant(JSONB(), "postgresql"), nullable=False)
    source = Column(String(32), nullable=False, default="api_sports")
    last_fetched_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    stale_after_seconds = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_apisports_standings_sport_league", "sport", "league_id"),
    )
