"""Historical odds snapshots (The Odds API).

Stores a compact snapshot per event for a given reference window (e.g. lookback_24h).
This lets the app compute line movement without re-calling the external API on every
analysis/parlay request.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Column, Date, DateTime, Index, JSON, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.database.session import Base
from app.database.types import GUID


class OddsHistorySnapshot(Base):
    __tablename__ = "odds_history_snapshots"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # The Odds API event id (matches Game.external_game_id for odds-sourced games)
    external_game_id = Column(String, nullable=False, index=True)

    # Odds API sport key, e.g. "basketball_nba"
    sport_key = Column(String, nullable=False, index=True)

    # Snapshot category, e.g. "lookback_24h"
    snapshot_kind = Column(String, nullable=False, index=True)

    # Date bucket for the snapshot run (UTC).
    snapshot_date = Column(Date, nullable=False, index=True)

    # Requested timestamp and the actual snapshot timestamp returned by the API.
    requested_at = Column(DateTime(timezone=True), nullable=False)
    snapshot_time = Column(DateTime(timezone=True), nullable=True)

    # Compact extracted line data (JSON for cross-db; JSONB on Postgres).
    data = Column(JSON().with_variant(JSONB(), "postgresql"), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index(
            "uq_odds_history_snapshots_game_kind_date",
            "external_game_id",
            "snapshot_kind",
            "snapshot_date",
            unique=True,
        ),
    )




