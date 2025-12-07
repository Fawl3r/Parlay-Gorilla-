"""
Badge Service for managing user achievements.

Provides:
- Badge checking and awarding
- Badge retrieval
- Race condition handling with unique constraints
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.exc import IntegrityError
import uuid
import logging

from app.models.user import User
from app.models.parlay import Parlay
from app.models.badge import Badge, BadgeRequirementType
from app.models.user_badge import UserBadge

logger = logging.getLogger(__name__)


class BadgeService:
    """
    Service for badge/achievement operations.
    
    Handles:
    - Checking badge requirements
    - Awarding badges
    - Handling race conditions
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def check_and_award_badges(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Check all badge requirements and award any newly earned badges.
        
        Returns list of newly unlocked badges (for frontend toast/modal).
        Handles race conditions gracefully by catching unique constraint violations.
        """
        try:
            user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        except ValueError:
            logger.warning(f"Invalid user_id format: {user_id}")
            return []
        
        # Get user
        result = await self.db.execute(
            select(User).where(User.id == user_uuid)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return []
        
        # Get user's current stats for badge checking
        stats = await self._get_user_stats(user_uuid)
        
        # Get all active badges
        badges_result = await self.db.execute(
            select(Badge).where(Badge.is_active == "1")
        )
        all_badges = badges_result.scalars().all()
        
        # Get user's already earned badges
        earned_result = await self.db.execute(
            select(UserBadge.badge_id).where(UserBadge.user_id == user_uuid)
        )
        earned_badge_ids = {str(row[0]) for row in earned_result.all()}
        
        newly_unlocked = []
        
        for badge in all_badges:
            badge_id_str = str(badge.id)
            
            # Skip if already earned
            if badge_id_str in earned_badge_ids:
                continue
            
            # Check if requirement is met
            if self._check_requirement(badge, stats, user):
                # Try to award badge
                awarded = await self._award_badge(user_uuid, badge.id)
                if awarded:
                    newly_unlocked.append(badge.to_dict(unlocked=True))
                    logger.info(f"User {user_id} earned badge: {badge.name}")
        
        return newly_unlocked
    
    async def get_user_badges(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all badges with unlock status for a user.
        
        Returns list of all badges with unlocked: boolean and unlocked_at.
        """
        try:
            user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        except ValueError:
            return []
        
        # Get all active badges
        badges_result = await self.db.execute(
            select(Badge)
            .where(Badge.is_active == "1")
            .order_by(Badge.display_order)
        )
        all_badges = badges_result.scalars().all()
        
        # Get user's unlocked badges
        user_badges_result = await self.db.execute(
            select(UserBadge)
            .where(UserBadge.user_id == user_uuid)
        )
        user_badges = {
            str(ub.badge_id): ub.unlocked_at 
            for ub in user_badges_result.scalars().all()
        }
        
        # Combine into response
        badges_with_status = []
        for badge in all_badges:
            badge_id_str = str(badge.id)
            unlocked = badge_id_str in user_badges
            unlocked_at = user_badges.get(badge_id_str)
            
            badges_with_status.append(
                badge.to_dict(
                    unlocked=unlocked,
                    unlocked_at=unlocked_at.isoformat() if unlocked_at else None
                )
            )
        
        return badges_with_status
    
    async def _get_user_stats(self, user_uuid: uuid.UUID) -> Dict[str, Any]:
        """Get user stats for badge requirement checking."""
        # Total parlays
        total_result = await self.db.execute(
            select(func.count(Parlay.id)).where(Parlay.user_id == user_uuid)
        )
        total_parlays = total_result.scalar() or 0
        
        return {
            "total_parlays": total_parlays,
        }
    
    def _check_requirement(
        self, 
        badge: Badge, 
        stats: Dict[str, Any],
        user: User
    ) -> bool:
        """Check if a badge requirement is met."""
        req_type = badge.requirement_type
        req_value = badge.requirement_value
        
        if req_type == BadgeRequirementType.TOTAL_PARLAYS.value:
            return stats.get("total_parlays", 0) >= req_value
        
        elif req_type == BadgeRequirementType.EMAIL_VERIFIED.value:
            return user.email_verified
        
        elif req_type == BadgeRequirementType.PROFILE_COMPLETE.value:
            return user.profile_completed
        
        # Add more requirement types as needed
        # elif req_type == BadgeRequirementType.CONSECUTIVE_DAYS.value:
        #     return stats.get("consecutive_days", 0) >= req_value
        
        return False
    
    async def _award_badge(self, user_uuid: uuid.UUID, badge_id: uuid.UUID) -> bool:
        """
        Award a badge to a user.
        
        Returns True if badge was awarded, False if already exists (race condition).
        """
        try:
            user_badge = UserBadge(
                id=uuid.uuid4(),
                user_id=user_uuid,
                badge_id=badge_id,
            )
            self.db.add(user_badge)
            await self.db.commit()
            return True
        
        except IntegrityError:
            # Unique constraint violation - badge already awarded (race condition)
            await self.db.rollback()
            logger.debug(f"Badge {badge_id} already awarded to user {user_uuid} (race condition handled)")
            return False
        
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error awarding badge: {e}")
            return False
    
    async def award_badge_by_slug(self, user_id: str, badge_slug: str) -> Optional[Dict[str, Any]]:
        """
        Manually award a specific badge by slug.
        
        Useful for special badges like "Verified Gorilla" or "Complete Profile".
        """
        try:
            user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        except ValueError:
            return None
        
        # Get badge by slug
        badge_result = await self.db.execute(
            select(Badge).where(Badge.slug == badge_slug)
        )
        badge = badge_result.scalar_one_or_none()
        
        if not badge:
            logger.warning(f"Badge not found: {badge_slug}")
            return None
        
        # Check if already awarded
        existing_result = await self.db.execute(
            select(UserBadge).where(
                and_(
                    UserBadge.user_id == user_uuid,
                    UserBadge.badge_id == badge.id
                )
            )
        )
        if existing_result.scalar_one_or_none():
            return None  # Already awarded
        
        # Award badge
        awarded = await self._award_badge(user_uuid, badge.id)
        if awarded:
            return badge.to_dict(unlocked=True)
        
        return None


# Helper function for dependency injection
async def get_badge_service(db: AsyncSession) -> BadgeService:
    """Get badge service instance."""
    return BadgeService(db)

