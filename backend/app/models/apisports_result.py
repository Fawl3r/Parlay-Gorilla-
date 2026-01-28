"""API-Sports results cache (completed games)."""

from __future__ import annotations

from sqlalchemy import Column, String, Integer, DateTime, Index
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
import uuid

from app.database.session import Base
from app.database.types import GUID


class ApisportsResult(Base):
    """Cached game result from API-Sports."""

    __tablename__ = "apisports_results"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    sport = Column(String(32), nullable=False, index=True)
    league_id = Column(Integer, nullable=True, index=True)
    fixture_id = Column(Integer, nullable=False, index=True)
    home_team_id = Column(Integer, nullable=True, index=True)
    away_team_id = Column(Integer, nullable=True, index=True)
    home_score = Column(Integer, nullable=True)
    away_score = Column(Integer, nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True, index=True)
    payload_json = Column(JSON().with_variant(JSONB(), "postgresql"), nullable=False)
    source = Column(String(32), nullable=False, default="api_sports")
    last_fetched_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_apisports_results_sport_fixture", "sport", "fixture_id", unique=True),
        Index("idx_apisports_results_sport_date", "sport", "finished_at"),
    )
