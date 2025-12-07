"""
Parlay Event model for detailed parlay analytics.

Stores parlay-specific events with structured fields for efficient querying.
Complements app_events with specialized parlay metrics.
"""

from sqlalchemy import Column, String, DateTime, Index, ForeignKey, Integer, Float, Boolean, JSON
from sqlalchemy.sql import func
import uuid

from app.database.session import Base
from app.database.types import GUID


class ParlayEvent(Base):
    """
    Parlay-specific analytics tracking.
    
    Captures detailed parlay generation metrics:
    - Parlay type (safe/balanced/degen/custom)
    - Sports involved
    - Leg count and composition
    - Expected value calculations
    """
    
    __tablename__ = "parlay_events"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    
    # User context
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=True, index=True)
    session_id = Column(String(64), nullable=True, index=True)
    
    # Parlay reference
    parlay_id = Column(GUID(), nullable=True, index=True)  # Links to parlays table if saved
    
    # Parlay configuration
    parlay_type = Column(String(20), nullable=False, index=True)  # safe, balanced, degen, custom
    sport_filters = Column(JSON, nullable=True)  # ["nfl", "nba"] or null for all
    
    # Parlay metrics
    legs_count = Column(Integer, nullable=False)
    expected_value = Column(Float, nullable=True)
    combined_odds = Column(Float, nullable=True)
    hit_probability = Column(Float, nullable=True)
    
    # Leg composition details
    legs_breakdown = Column(JSON, nullable=True)
    # e.g., {"moneyline": 3, "spread": 2, "total": 2, "upsets": 1}
    
    # User interaction
    was_saved = Column(Boolean, default=False)
    was_shared = Column(Boolean, default=False)
    build_method = Column(String(50), nullable=True)  # "auto_generated", "user_built", "ai_assisted"
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Indexes for analytics
    __table_args__ = (
        Index("idx_parlay_events_type_date", "parlay_type", "created_at"),
        Index("idx_parlay_events_user", "user_id", "created_at"),
        Index("idx_parlay_events_legs", "legs_count"),
    )
    
    def __repr__(self):
        return f"<ParlayEvent(type={self.parlay_type}, legs={self.legs_count}, ev={self.expected_value})>"

