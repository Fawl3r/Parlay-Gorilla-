"""Derived features computed from API-Sports + internal data (form, rest days, etc.)."""

from __future__ import annotations

from sqlalchemy import Column, String, Integer, Float, DateTime, Index
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
import uuid

from app.database.session import Base
from app.database.types import GUID


class ApisportsFeature(Base):
    """Computed features for modeling (rolling stats, form, rest days, opponent strength)."""

    __tablename__ = "apisports_features"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    sport = Column(String(32), nullable=False, index=True)
    team_id = Column(Integer, nullable=True, index=True)
    league_id = Column(Integer, nullable=True, index=True)
    season = Column(String(16), nullable=True, index=True)
    features_json = Column(JSON().with_variant(JSONB(), "postgresql"), nullable=False)
    last_n_form_wins = Column(Integer, nullable=True)
    last_n_form_losses = Column(Integer, nullable=True)
    rest_days = Column(Integer, nullable=True)
    home_away_split_json = Column(JSON().with_variant(JSONB(), "postgresql"), nullable=True)
    opponent_strength_proxy = Column(Float, nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_apisports_features_sport_team", "sport", "team_id"),
        Index("idx_apisports_features_sport_league", "sport", "league_id"),
    )
