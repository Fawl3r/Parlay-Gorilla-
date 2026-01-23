"""Parlay feed event model for marquee and win wall."""

from __future__ import annotations

import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.database.session import Base
from app.database.types import GUID


class ParlayFeedEvent(Base):
    """Feed event model for marquee and win wall display."""
    
    __tablename__ = "parlay_feed_events"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    event_type = Column(String, nullable=False)  # GAME_LIVE, GAME_FINAL, PARLAY_CREATED, LEG_WON, LEG_LOST, PARLAY_WON, PARLAY_LOST
    sport = Column(String, nullable=True)
    
    parlay_id = Column(GUID(), ForeignKey("parlays.id", ondelete="CASCADE"), nullable=True)
    saved_parlay_id = Column(GUID(), ForeignKey("saved_parlays.id", ondelete="CASCADE"), nullable=True)
    
    user_alias = Column(String, nullable=True)  # Public-safe alias for display
    summary = Column(String, nullable=False)  # Pre-rendered marquee string
    metadata = Column(JSONB, nullable=True)  # Additional event data
    
    # Indexes
    __table_args__ = (
        Index("idx_feed_events_created_at", "created_at"),
        Index("idx_feed_events_type_created", "event_type", "created_at"),
        Index("idx_feed_events_sport_created", "sport", "created_at"),
    )
    
    def __repr__(self):
        return f"<ParlayFeedEvent(id={self.id}, type={self.event_type}, created_at={self.created_at})>"
