"""
App Event model for analytics tracking.

Stores generic application events like page views, clicks, and user interactions.
All events are stored in PostgreSQL for CLI-queryable analytics.
"""

from sqlalchemy import Column, String, DateTime, Index, ForeignKey, Text, JSON
from sqlalchemy.sql import func
import uuid

from app.database.session import Base
from app.database.types import GUID


class AppEvent(Base):
    """
    Generic analytics event tracking.
    
    Captures user interactions for analytics:
    - Page views (view_analysis, view_parlay_result)
    - User actions (build_parlay, click_upset_finder)
    - Session tracking via session_id
    """
    
    __tablename__ = "app_events"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    
    # User context (nullable for anonymous events)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=True, index=True)
    session_id = Column(String(64), nullable=True, index=True)
    
    # Event details
    event_type = Column(String(100), nullable=False, index=True)
    
    # Flexible metadata storage
    # e.g., {"sport": "nfl", "matchup": "bears-packers", "legs": 7, "parlay_type": "balanced"}
    # Note: Using 'metadata_' as Python attribute name because 'metadata' is reserved in SQLAlchemy
    # Using JSON instead of JSONB for SQLite compatibility
    metadata_ = Column("metadata", JSON, nullable=True, default=dict)
    
    # Request context
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    referrer = Column(Text, nullable=True)
    page_url = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Indexes for efficient analytics queries
    __table_args__ = (
        Index("idx_app_events_type_date", "event_type", "created_at"),
        Index("idx_app_events_user_date", "user_id", "created_at"),
        Index("idx_app_events_session", "session_id"),
    )
    
    def __repr__(self):
        return f"<AppEvent(type={self.event_type}, user={self.user_id}, at={self.created_at})>"

