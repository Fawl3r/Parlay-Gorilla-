"""
Profile Service for managing user profiles, stats, and badges.

Provides:
- Profile retrieval with parlay stats and badges
- Profile updates
- Profile setup completion
- Parlay statistics calculation
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
import uuid
import logging

from app.models.user import User
from app.models.parlay import Parlay
from app.models.badge import Badge
from app.models.user_badge import UserBadge

logger = logging.getLogger(__name__)


class ProfileService:
    """
    Service for profile operations.
    
    Handles:
    - Profile retrieval with stats and badges
    - Profile updates
    - Profile setup completion
    - Parlay statistics
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get complete user profile with stats and badges.
        
        Returns:
            {
                "user": { profile fields },
                "stats": { parlay statistics },
                "badges": [ all badges with unlock status ]
            }
        """
        try:
            user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        except ValueError:
            logger.warning(f"Invalid user_id format: {user_id}")
            return None
        
        # Get user
        result = await self.db.execute(
            select(User).where(User.id == user_uuid)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        # Get stats
        stats = await self.get_parlay_stats(user_id)
        
        # Get badges
        badges = await self.get_all_badges_with_status(user_id)
        
        return {
            "user": self._user_to_dict(user),
            "stats": stats,
            "badges": badges,
        }
    
    async def update_profile(self, user_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update user profile fields.
        
        Allowed fields: display_name, avatar_url, bio, timezone,
                       default_risk_profile, favorite_teams, favorite_sports
        """
        try:
            user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        except ValueError:
            logger.warning(f"Invalid user_id format: {user_id}")
            return None
        
        # Get user
        result = await self.db.execute(
            select(User).where(User.id == user_uuid)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        # Allowed fields for update
        allowed_fields = {
            "display_name", "avatar_url", "bio", "timezone",
            "default_risk_profile", "favorite_teams", "favorite_sports"
        }
        
        # Update allowed fields
        for field, value in data.items():
            if field in allowed_fields:
                setattr(user, field, value)
        
        await self.db.commit()
        await self.db.refresh(user)
        
        return self._user_to_dict(user)
    
    async def complete_profile_setup(
        self, 
        user_id: str, 
        data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Complete initial profile setup.
        
        Sets profile_completed = True after updating profile fields.
        
        Required fields in data:
        - display_name (required)
        
        Optional fields:
        - avatar_url
        - bio
        - timezone
        - default_risk_profile
        - favorite_teams
        - favorite_sports
        """
        try:
            user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        except ValueError:
            logger.warning(f"Invalid user_id format: {user_id}")
            return None
        
        # Validate required fields
        if not data.get("display_name"):
            raise ValueError("display_name is required for profile setup")
        
        # Get user
        result = await self.db.execute(
            select(User).where(User.id == user_uuid)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        # Allowed fields for setup
        allowed_fields = {
            "display_name", "avatar_url", "bio", "timezone",
            "default_risk_profile", "favorite_teams", "favorite_sports"
        }
        
        # Update allowed fields
        for field, value in data.items():
            if field in allowed_fields:
                setattr(user, field, value)
        
        # Mark profile as completed
        user.profile_completed = True
        
        await self.db.commit()
        await self.db.refresh(user)
        
        logger.info(f"Profile setup completed for user {user_id}")
        
        return self._user_to_dict(user)
    
    async def get_parlay_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get parlay statistics for a user.
        
        Returns:
            {
                "total_parlays": int,
                "by_sport": { "NFL": count, "NBA": count, ... },
                "by_risk_profile": { "safe": count, "balanced": count, "degen": count }
            }
        """
        try:
            user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        except ValueError:
            return {"total_parlays": 0, "by_sport": {}, "by_risk_profile": {}}
        
        # Get total parlays
        total_result = await self.db.execute(
            select(func.count(Parlay.id)).where(Parlay.user_id == user_uuid)
        )
        total_parlays = total_result.scalar() or 0
        
        # Get breakdown by risk profile
        risk_result = await self.db.execute(
            select(Parlay.risk_profile, func.count(Parlay.id))
            .where(Parlay.user_id == user_uuid)
            .group_by(Parlay.risk_profile)
        )
        by_risk_profile = {row[0]: row[1] for row in risk_result.all()}
        
        # Get breakdown by sport (from legs JSON)
        # This is a simplified version - in production you might want to
        # aggregate this in a more efficient way
        parlays_result = await self.db.execute(
            select(Parlay.legs).where(Parlay.user_id == user_uuid)
        )
        
        by_sport = {}
        for row in parlays_result.all():
            legs = row[0] or []
            for leg in legs:
                sport = leg.get("sport", "Unknown")
                by_sport[sport] = by_sport.get(sport, 0) + 1
        
        return {
            "total_parlays": total_parlays,
            "by_sport": by_sport,
            "by_risk_profile": by_risk_profile,
        }
    
    async def get_all_badges_with_status(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all badges with unlock status for a user.
        
        Returns list of all badges, each with:
        - Badge info (name, description, icon, etc.)
        - unlocked: boolean
        - unlocked_at: timestamp if unlocked
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
    
    def _user_to_dict(self, user: User) -> Dict[str, Any]:
        """Convert user to dictionary for API response."""
        return {
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
            "display_name": user.display_name,
            "avatar_url": user.avatar_url,
            "bio": user.bio,
            "timezone": user.timezone,
            "email_verified": user.email_verified,
            "profile_completed": user.profile_completed,
            "default_risk_profile": user.default_risk_profile,
            "favorite_teams": user.favorite_teams or [],
            "favorite_sports": user.favorite_sports or [],
            "role": user.role,
            "plan": user.plan,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None,
        }


# Helper function for dependency injection
async def get_profile_service(db: AsyncSession) -> ProfileService:
    """Get profile service instance."""
    return ProfileService(db)

