"""API-Sports fixtures cache (DB-first; never call API from user-facing endpoints)."""

from __future__ import annotations

from sqlalchemy import Column, String, Integer, DateTime, Index, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
import uuid

from app.database.session import Base
from app.database.types import GUID


class ApisportsFixture(Base):
    """Cached fixture list from API-Sports. Refreshed by background job only."""

    __tablename__ = "apisports_fixtures"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    sport = Column(String(32), nullable=False, index=True)
    league_id = Column(Integer, nullable=True, index=True)
    fixture_id = Column(Integer, nullable=True, index=True)
    date = Column(DateTime(timezone=True), nullable=True, index=True)
    home_team_id = Column(Integer, nullable=True, index=True)
    away_team_id = Column(Integer, nullable=True, index=True)
    payload_json = Column(JSON().with_variant(JSONB(), "postgresql"), nullable=False)
    source = Column(String(32), nullable=False, default="api_sports")
    last_fetched_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    stale_after_seconds = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_apisports_fixtures_sport_date", "sport", "date"),
        Index("idx_apisports_fixtures_sport_fixture_id", "sport", "fixture_id"),
        Index("idx_apisports_fixtures_sport_league", "sport", "league_id"),
    )
