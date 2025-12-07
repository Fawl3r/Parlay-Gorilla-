"""
Badge model for achievement/badge definitions.

Badges are earned based on user activity like parlay generation.
"""

from sqlalchemy import Column, String, Integer, Text, DateTime, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.database.session import Base
from app.database.types import GUID


class BadgeRequirementType(str, enum.Enum):
    """Types of requirements for earning badges"""
    TOTAL_PARLAYS = "TOTAL_PARLAYS"
    CONSECUTIVE_DAYS = "CONSECUTIVE_DAYS"
    SPORTS_VARIETY = "SPORTS_VARIETY"
    WINNING_STREAK = "WINNING_STREAK"
    ACCOUNT_AGE = "ACCOUNT_AGE"
    PROFILE_COMPLETE = "PROFILE_COMPLETE"
    EMAIL_VERIFIED = "EMAIL_VERIFIED"


class Badge(Base):
    """
    Badge definitions for the achievement system.
    
    Each badge has:
    - Unique slug for identification
    - Display info (name, description, icon)
    - Requirement type and threshold value
    - Display order for UI sorting
    """
    
    __tablename__ = "badges"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    
    # Badge identification
    name = Column(String(100), nullable=False)
    slug = Column(String(50), unique=True, nullable=False, index=True)
    
    # Display information
    description = Column(Text, nullable=True)
    icon = Column(String(100), nullable=True)  # Emoji or URL to icon image
    
    # Requirement for earning
    requirement_type = Column(String(50), nullable=False, index=True)
    requirement_value = Column(Integer, nullable=False, default=1)
    
    # Display ordering
    display_order = Column(Integer, default=0, nullable=False)
    
    # Status
    is_active = Column(String(1), default="1", nullable=False)  # "1" = active, "0" = inactive
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user_badges = relationship("UserBadge", back_populates="badge", lazy="dynamic")
    
    # Indexes
    __table_args__ = (
        Index("idx_badge_slug", "slug"),
        Index("idx_badge_requirement_type", "requirement_type"),
        Index("idx_badge_display_order", "display_order"),
    )
    
    def __repr__(self):
        return f"<Badge(slug={self.slug}, name={self.name}, requirement={self.requirement_type}:{self.requirement_value})>"
    
    def to_dict(self, unlocked: bool = False, unlocked_at: str = None) -> dict:
        """Convert badge to dictionary for API response"""
        return {
            "id": str(self.id),
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "icon": self.icon,
            "requirement_type": self.requirement_type,
            "requirement_value": self.requirement_value,
            "display_order": self.display_order,
            "unlocked": unlocked,
            "unlocked_at": unlocked_at,
        }


# Starter badge definitions for seeding
STARTER_BADGES = [
    {
        "slug": "rookie-gorilla",
        "name": "Rookie Gorilla",
        "description": "Generated your first parlay!",
        "icon": "🦍",
        "requirement_type": BadgeRequirementType.TOTAL_PARLAYS.value,
        "requirement_value": 1,
        "display_order": 1,
    },
    {
        "slug": "volume-shooter",
        "name": "Volume Shooter",
        "description": "10 parlays and counting",
        "icon": "🎯",
        "requirement_type": BadgeRequirementType.TOTAL_PARLAYS.value,
        "requirement_value": 10,
        "display_order": 2,
    },
    {
        "slug": "degen-apprentice",
        "name": "Degen Apprentice",
        "description": "You're learning the ways",
        "icon": "📚",
        "requirement_type": BadgeRequirementType.TOTAL_PARLAYS.value,
        "requirement_value": 25,
        "display_order": 3,
    },
    {
        "slug": "degen-veteran",
        "name": "Degen Veteran",
        "description": "A true veteran of the game",
        "icon": "🎖️",
        "requirement_type": BadgeRequirementType.TOTAL_PARLAYS.value,
        "requirement_value": 50,
        "display_order": 4,
    },
    {
        "slug": "parlay-maniac",
        "name": "Parlay Maniac",
        "description": "Unstoppable parlay machine",
        "icon": "🔥",
        "requirement_type": BadgeRequirementType.TOTAL_PARLAYS.value,
        "requirement_value": 100,
        "display_order": 5,
    },
    {
        "slug": "verified-gorilla",
        "name": "Verified Gorilla",
        "description": "Email verified and ready to roll",
        "icon": "✅",
        "requirement_type": BadgeRequirementType.EMAIL_VERIFIED.value,
        "requirement_value": 1,
        "display_order": 6,
    },
    {
        "slug": "profile-complete",
        "name": "Complete Profile",
        "description": "Set up your gorilla profile",
        "icon": "👤",
        "requirement_type": BadgeRequirementType.PROFILE_COMPLETE.value,
        "requirement_value": 1,
        "display_order": 7,
    },
]

