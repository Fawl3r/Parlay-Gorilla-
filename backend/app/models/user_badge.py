"""
UserBadge model for tracking user's earned badges.

Junction table between User and Badge with unlock timestamp.
"""

from sqlalchemy import Column, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database.session import Base
from app.database.types import GUID


class UserBadge(Base):
    """
    Tracks which badges a user has unlocked.
    
    Features:
    - Unique constraint on (user_id, badge_id) prevents duplicate badges
    - Unlock timestamp for showing when badge was earned
    - Relationship to both User and Badge for easy queries
    """
    
    __tablename__ = "user_badges"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    
    # User reference
    user_id = Column(
        GUID(), 
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    
    # Badge reference
    badge_id = Column(
        GUID(), 
        ForeignKey("badges.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    
    # When the badge was unlocked
    unlocked_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="badges")
    badge = relationship("Badge", back_populates="user_badges")
    
    # Constraints and indexes
    __table_args__ = (
        # UNIQUE CONSTRAINT to prevent race condition duplicates
        UniqueConstraint('user_id', 'badge_id', name='uq_user_badge'),
        Index("idx_user_badge_user", "user_id"),
        Index("idx_user_badge_badge", "badge_id"),
        Index("idx_user_badge_unlocked", "unlocked_at"),
    )
    
    def __repr__(self):
        return f"<UserBadge(user_id={self.user_id}, badge_id={self.badge_id}, unlocked={self.unlocked_at})>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API response"""
        badge_dict = self.badge.to_dict(
            unlocked=True,
            unlocked_at=self.unlocked_at.isoformat() if self.unlocked_at else None
        )
        return badge_dict

