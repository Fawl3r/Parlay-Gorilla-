"""
Usage Limit model for tracking daily feature usage.

Tracks free user limits like AI parlay generations per day.
This enables the "3 free AI parlays per day" business rule.
"""

from sqlalchemy import Column, DateTime, Integer, Date, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from datetime import date as date_type

from app.database.session import Base
from app.database.types import GUID


class UsageLimit(Base):
    """
    Daily usage tracking for rate-limited features.
    
    Primary use case: Enforce "3 free AI parlays per day" for free users.
    
    Each row represents one user's usage for one day (UTC).
    The unique constraint on (user_id, date) ensures one record per user per day.
    """
    
    __tablename__ = "usage_limits"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    
    # User reference
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    
    # Date (UTC) - one record per user per day
    date = Column(Date, nullable=False, index=True)
    
    # Usage counters
    free_parlays_generated = Column(Integer, default=0, nullable=False)
    custom_parlays_built = Column(Integer, default=0, nullable=False)  # For future tracking
    upset_finder_queries = Column(Integer, default=0, nullable=False)  # For future tracking
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint("user_id", "date", name="uq_usage_limits_user_date"),
        Index("idx_usage_limits_user_date", "user_id", "date"),
    )
    
    def __repr__(self):
        return f"<UsageLimit(user={self.user_id}, date={self.date}, parlays={self.free_parlays_generated})>"
    
    @classmethod
    def get_today(cls) -> date_type:
        """Get today's date in UTC"""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).date()
    
    def can_generate_free_parlay(self, max_allowed: int = 3) -> bool:
        """Check if user can generate another free parlay today"""
        return self.free_parlays_generated < max_allowed
    
    def increment_parlay_count(self) -> int:
        """Increment parlay count and return new value"""
        self.free_parlays_generated += 1
        return self.free_parlays_generated
    
    @property
    def remaining_free_parlays(self) -> int:
        """Get remaining free parlays for today (assuming max of 3)"""
        from app.core.config import settings
        return max(0, settings.free_parlays_per_day - self.free_parlays_generated)

