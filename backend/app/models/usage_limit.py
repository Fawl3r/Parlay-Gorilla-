"""
Usage Limit model for tracking weekly feature usage (rolling 7-day window).

Tracks free user limits like AI parlay generations per week.
This enables the "5 free AI parlays per week" business rule.
"""

from sqlalchemy import Column, DateTime, Integer, Date, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from datetime import date as date_type, datetime, timedelta, timezone

from app.database.session import Base
from app.database.types import GUID


class UsageLimit(Base):
    """
    Weekly usage tracking for rate-limited features (rolling 7-day window).
    
    Primary use case: Enforce "5 free AI parlays per week" and "5 free custom builder parlays per week" for free users.
    
    Each row represents one user's usage for one rolling 7-day period.
    The unique constraint on (user_id, date) ensures one record per user per day (for backward compatibility).
    The `first_usage_at` timestamp tracks when the 7-day window started.
    """
    
    __tablename__ = "usage_limits"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    
    # User reference
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    
    # Date (UTC) - kept for backward compatibility and indexing
    # For weekly tracking, this represents the date when the window started
    date = Column(Date, nullable=False, index=True)
    
    # First usage timestamp - tracks when the 7-day rolling window started
    first_usage_at = Column(DateTime(timezone=True), nullable=True)
    
    # Usage counters
    free_parlays_generated = Column(Integer, default=0, nullable=False)
    custom_parlays_built = Column(Integer, default=0, nullable=False)
    upset_finder_queries = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint("user_id", "date", name="uq_usage_limits_user_date"),
        Index("idx_usage_limits_user_date", "user_id", "date"),
        Index("idx_usage_limits_user_first_usage", "user_id", "first_usage_at"),
    )
    
    def __repr__(self):
        return f"<UsageLimit(user={self.user_id}, date={self.date}, parlays={self.free_parlays_generated}, custom={self.custom_parlays_built})>"
    
    @classmethod
    def get_today(cls) -> date_type:
        """Get today's date in UTC"""
        return datetime.now(timezone.utc).date()
    
    def is_window_expired(self, days: int = 7) -> bool:
        """Check if the rolling window has expired (7 days have passed since first_usage_at)"""
        if not self.first_usage_at:
            return False
        now = datetime.now(timezone.utc)
        elapsed = now - self.first_usage_at
        return elapsed >= timedelta(days=days)
    
    def can_generate_free_parlay(self, max_allowed: int = 5) -> bool:
        """Check if user can generate another free parlay in current window"""
        if self.is_window_expired():
            return True  # Window expired, can use
        return self.free_parlays_generated < max_allowed
    
    def can_build_free_custom_parlay(self, max_allowed: int = 5) -> bool:
        """Check if user can build another free custom parlay in current window"""
        if self.is_window_expired():
            return True  # Window expired, can use
        return self.custom_parlays_built < max_allowed
    
    def increment_parlay_count(self) -> int:
        """Increment parlay count and return new value"""
        self.free_parlays_generated += 1
        return self.free_parlays_generated
    
    def increment_custom_parlay_count(self) -> int:
        """Increment custom parlay count and return new value"""
        self.custom_parlays_built += 1
        return self.custom_parlays_built
    
    def reset_window(self) -> None:
        """Reset the usage window (called when 7 days have passed)"""
        now = datetime.now(timezone.utc)
        self.first_usage_at = now
        self.date = now.date()
        self.free_parlays_generated = 0
        self.custom_parlays_built = 0
    
    @property
    def remaining_free_parlays(self) -> int:
        """Get remaining free parlays for current week"""
        from app.core.config import settings
        if self.is_window_expired():
            return settings.free_parlays_per_week
        return max(0, settings.free_parlays_per_week - self.free_parlays_generated)
    
    @property
    def remaining_free_custom_parlays(self) -> int:
        """Get remaining free custom parlays for current week"""
        from app.core.config import settings
        if self.is_window_expired():
            return settings.free_custom_parlays_per_week
        return max(0, settings.free_custom_parlays_per_week - self.custom_parlays_built)

