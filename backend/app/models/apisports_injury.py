"""API-Sports injuries cache (optional)."""

from __future__ import annotations

from sqlalchemy import Column, String, Integer, DateTime, Index
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
import uuid

from app.database.session import Base
from app.database.types import GUID


class ApisportsInjury(Base):
    """Cached injury data from API-Sports."""

    __tablename__ = "apisports_injuries"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    sport = Column(String(32), nullable=False, index=True)
    team_id = Column(Integer, nullable=True, index=True)
    league_id = Column(Integer, nullable=True, index=True)
    payload_json = Column(JSON().with_variant(JSONB(), "postgresql"), nullable=False)
    source = Column(String(32), nullable=False, default="api_sports")
    last_fetched_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    stale_after_seconds = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_apisports_injuries_sport_team", "sport", "team_id"),
    )
