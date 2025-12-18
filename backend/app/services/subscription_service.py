"""
Subscription Service for managing user subscriptions and access levels.

Core business logic for:
- Checking if user has premium access
- Enforcing free tier limits (3 AI parlays per day)
- Managing subscription status
- Tracking feature usage
"""

from datetime import datetime, timezone, date
from typing import Optional, Dict, Any
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import uuid
import logging

from app.models.user import User, UserPlan
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.subscription_plan import SubscriptionPlan
from app.models.usage_limit import UsageLimit

logger = logging.getLogger(__name__)


@dataclass
class UserAccessLevel:
    """
    User's current access level and feature permissions.
    
    Returned by get_user_access_level() for use in access control decisions.
    """
    tier: str  # "free" or "premium"
    plan_code: Optional[str]  # e.g., "PG_PREMIUM_MONTHLY", None for free
    can_use_custom_builder: bool
    can_use_upset_finder: bool
    can_use_multi_sport: bool
    can_save_parlays: bool
    max_ai_parlays_per_day: int  # -1 for unlimited
    remaining_ai_parlays_today: int  # -1 for unlimited
    max_custom_parlays_per_day: int  # 0 for free, 15 for premium
    remaining_custom_parlays_today: int  # 0 for free, remaining for premium
    is_lifetime: bool
    subscription_end: Optional[datetime]
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            "tier": self.tier,
            "plan_code": self.plan_code,
            "can_use_custom_builder": self.can_use_custom_builder,
            "can_use_upset_finder": self.can_use_upset_finder,
            "can_use_multi_sport": self.can_use_multi_sport,
            "can_save_parlays": self.can_save_parlays,
            "max_ai_parlays_per_day": self.max_ai_parlays_per_day,
            "remaining_ai_parlays_today": self.remaining_ai_parlays_today,
            "unlimited_ai_parlays": self.max_ai_parlays_per_day == -1,
            "max_custom_parlays_per_day": self.max_custom_parlays_per_day,
            "remaining_custom_parlays_today": self.remaining_custom_parlays_today,
            "is_lifetime": self.is_lifetime,
            "subscription_end": self.subscription_end.isoformat() if self.subscription_end else None,
        }


# Default free tier access
FREE_ACCESS = UserAccessLevel(
    tier="free",
    plan_code=None,
    can_use_custom_builder=False,
    can_use_upset_finder=False,
    can_use_multi_sport=False,
    can_save_parlays=False,
    max_ai_parlays_per_day=1,
    remaining_ai_parlays_today=1,  # Will be updated based on usage
    max_custom_parlays_per_day=0,
    remaining_custom_parlays_today=0,
    is_lifetime=False,
    subscription_end=None,
)


class SubscriptionService:
    """
    Service for managing subscriptions and access control.
    
    Primary use cases:
    1. Check if user is premium: is_user_premium(user_id)
    2. Get full access level: get_user_access_level(user_id)
    3. Enforce free limit: can_use_free_parlay(user_id), increment_free_parlay_usage(user_id)
    4. Get subscription: get_user_active_subscription(user_id)
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user_active_subscription(self, user_id: str) -> Optional[Subscription]:
        """
        Get user's currently active subscription.
        
        Returns None if user has no active subscription (free tier).
        """
        try:
            user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        except ValueError:
            logger.warning(f"Invalid user_id format: {user_id}")
            return None
        
        try:
            result = await self.db.execute(
                select(Subscription).where(
                    and_(
                        Subscription.user_id == user_uuid,
                        Subscription.status.in_([
                            SubscriptionStatus.active.value,
                            SubscriptionStatus.trialing.value,
                            SubscriptionStatus.past_due.value,  # Grace period
                        ])
                    )
                ).order_by(Subscription.created_at.desc())
            )
            return result.scalar_one_or_none()
        except Exception as e:
            # Handle missing column error gracefully
            if 'is_lifetime' in str(e) or 'no such column' in str(e).lower():
                logger.warning(f"Database schema issue (missing is_lifetime column): {e}")
                # Try to add the column and retry, or return None
                return None
            raise
    
    async def is_user_premium(self, user_id: str) -> bool:
        """
        Check if user has an active premium subscription.
        
        Returns True if user has active, trialing, or past_due subscription
        that hasn't expired.
        """
        subscription = await self.get_user_active_subscription(user_id)
        
        if subscription:
            # Check if lifetime - handle missing column gracefully
            try:
                is_lifetime = getattr(subscription, 'is_lifetime', False)
                if is_lifetime:
                    return True
            except (AttributeError, KeyError):
                pass  # Column doesn't exist, treat as regular subscription
            
            # Check if subscription is expired (defensive check)
            if subscription.status == SubscriptionStatus.expired.value:
                return False
            
            # Check if within valid period
            if subscription.current_period_end:
                now = datetime.now(timezone.utc)
                if subscription.current_period_end > now:
                    return True
                else:
                    # Period has expired - mark as expired if not already
                    if subscription.status != SubscriptionStatus.expired.value:
                        subscription.status = SubscriptionStatus.expired.value
                        try:
                            await self.db.commit()
                            logger.info(f"Marked subscription {subscription.id} as expired (defensive check)")
                        except Exception as e:
                            logger.warning(f"Failed to mark subscription as expired: {e}")
                            await self.db.rollback()
                    return False
            else:
                # No period end = active (e.g., lifetime)
                return True
        
        return False
    
    async def get_user_subscription_tier(self, user_id: str) -> str:
        """
        Get user's subscription tier as a simple string.
        
        Returns:
            "free" if no active subscription
            "premium" if user has active premium subscription
        """
        is_premium = await self.is_user_premium(user_id)
        return "premium" if is_premium else "free"
    
    async def get_user_access_level(self, user_id: str) -> UserAccessLevel:
        """
        Get user's full access level including feature permissions and usage.
        
        This is the main method for determining what a user can do.
        """
        try:
            subscription = await self.get_user_active_subscription(user_id)
            
            if not subscription:
                # Free tier - check usage
                try:
                    from app.core.config import settings
                    usage = await self._get_or_create_usage_today(user_id)
                    remaining = max(0, settings.free_parlays_per_day - usage.free_parlays_generated)
                except Exception as usage_error:
                    # If we can't get usage, default to free_parlays_per_day remaining
                    from app.core.config import settings
                    logger.warning(f"Error getting usage for user {user_id}: {usage_error}, defaulting to {settings.free_parlays_per_day} remaining")
                    remaining = settings.free_parlays_per_day
                
                from app.core.config import settings
                return UserAccessLevel(
                    tier="free",
                    plan_code=None,
                    can_use_custom_builder=False,
                    can_use_upset_finder=False,
                    can_use_multi_sport=False,
                    can_save_parlays=False,
                    max_ai_parlays_per_day=settings.free_parlays_per_day,
                    remaining_ai_parlays_today=remaining,
                    max_custom_parlays_per_day=0,
                    remaining_custom_parlays_today=0,
                    is_lifetime=False,
                    subscription_end=None,
                )
            
            # Get plan details
            plan = None
            try:
                plan = await self._get_plan_by_code(subscription.plan)
            except Exception as plan_error:
                logger.warning(f"Error getting plan {subscription.plan} for user {user_id}: {plan_error}")
            
            if plan:
                # Handle missing is_lifetime column gracefully
                try:
                    is_lifetime = getattr(subscription, 'is_lifetime', False)
                    if is_lifetime is None:
                        is_lifetime = False
                except (AttributeError, KeyError):
                    is_lifetime = False
                
                # Get premium user and check/reset period
                from app.core.config import settings
                user = await self._get_user(user_id)
                if user:
                    await self._check_and_reset_premium_period(user)
                    remaining = max(0, settings.premium_ai_parlays_per_month - user.premium_ai_parlays_used)
                else:
                    remaining = settings.premium_ai_parlays_per_month
                
                # Get custom parlay remaining
                custom_remaining = await self.get_remaining_custom_parlays(user_id)
                
                return UserAccessLevel(
                    tier="premium",
                    plan_code=subscription.plan,
                    can_use_custom_builder=plan.can_use_custom_builder,
                    can_use_upset_finder=plan.can_use_upset_finder,
                    can_use_multi_sport=plan.can_use_multi_sport,
                    can_save_parlays=plan.can_save_parlays,
                    max_ai_parlays_per_day=settings.premium_ai_parlays_per_month,
                    remaining_ai_parlays_today=remaining,
                    max_custom_parlays_per_day=settings.premium_custom_parlays_per_day,
                    remaining_custom_parlays_today=custom_remaining,
                    is_lifetime=bool(is_lifetime),
                    subscription_end=subscription.current_period_end,
                )
            
            # Fallback for premium without plan details
            # Handle missing is_lifetime column gracefully
            try:
                is_lifetime = getattr(subscription, 'is_lifetime', False)
                if is_lifetime is None:
                    is_lifetime = False
            except (AttributeError, KeyError):
                is_lifetime = False
            
            # Get premium user and check/reset period
            from app.core.config import settings
            user = await self._get_user(user_id)
            if user:
                await self._check_and_reset_premium_period(user)
                remaining = max(0, settings.premium_ai_parlays_per_month - user.premium_ai_parlays_used)
            else:
                remaining = settings.premium_ai_parlays_per_month
            
            # Get custom parlay remaining
            custom_remaining = await self.get_remaining_custom_parlays(user_id)
            
            return UserAccessLevel(
                tier="premium",
                plan_code=subscription.plan,
                can_use_custom_builder=True,
                can_use_upset_finder=True,
                can_use_multi_sport=True,
                can_save_parlays=True,
                max_ai_parlays_per_day=settings.premium_ai_parlays_per_month,
                remaining_ai_parlays_today=remaining,
                max_custom_parlays_per_day=settings.premium_custom_parlays_per_day,
                remaining_custom_parlays_today=custom_remaining,
                is_lifetime=subscription.is_lifetime,
                subscription_end=subscription.current_period_end,
            )
        except Exception as e:
            logger.error(f"Error in get_user_access_level for user {user_id}: {e}")
            # Return default free tier on any error
            return FREE_ACCESS
    
    async def can_use_free_parlay(self, user_id: str) -> bool:
        """
        Check if user can generate another AI parlay.
        
        Returns True if:
        - User is premium and hasn't used 100 AI parlays this month
        - User is free and hasn't used daily limit
        """
        from app.core.config import settings
        
        if await self.is_user_premium(user_id):
            # Check premium monthly limit
            user = await self._get_user(user_id)
            if user:
                await self._check_and_reset_premium_period(user)
                return user.premium_ai_parlays_used < settings.premium_ai_parlays_per_month
            return True  # Fallback if user not found
        
        usage = await self._get_or_create_usage_today(user_id)
        return usage.free_parlays_generated < settings.free_parlays_per_day
    
    async def increment_free_parlay_usage(self, user_id: str) -> int:
        """
        Increment the free parlay counter for today.
        
        Returns the new count after incrementing.
        Call this AFTER successfully generating a parlay.
        """
        usage = await self._get_or_create_usage_today(user_id)
        usage.free_parlays_generated += 1
        await self.db.commit()
        await self.db.refresh(usage)
        return usage.free_parlays_generated
    
    async def increment_premium_ai_parlay_usage(self, user_id: str) -> int:
        """
        Increment the premium AI parlay counter for current 30-day period.
        
        Automatically resets if period has expired.
        Returns the new count after incrementing.
        Call this AFTER successfully generating a parlay.
        """
        user = await self._get_user(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # Check and reset period if needed
        await self._check_and_reset_premium_period(user)
        
        user.premium_ai_parlays_used += 1
        await self.db.commit()
        await self.db.refresh(user)
        return user.premium_ai_parlays_used
    
    async def can_use_custom_builder(self, user_id: str) -> bool:
        """
        Check if user can use custom parlay builder.
        
        Returns True if:
        - User has active premium subscription
        - User hasn't used daily custom parlay limit (15/day)
        """
        from app.core.config import settings
        
        # Must have premium subscription
        if not await self.is_user_premium(user_id):
            return False
        
        # Check daily limit
        usage = await self._get_or_create_usage_today(user_id)
        return usage.custom_parlays_built < settings.premium_custom_parlays_per_day
    
    async def get_remaining_custom_parlays(self, user_id: str) -> int:
        """
        Get remaining custom parlay count for today.
        
        Returns 0 if user is not premium.
        Returns remaining out of daily limit (15) for premium users.
        """
        from app.core.config import settings
        
        if not await self.is_user_premium(user_id):
            return 0
        
        usage = await self._get_or_create_usage_today(user_id)
        return max(0, settings.premium_custom_parlays_per_day - usage.custom_parlays_built)
    
    async def increment_custom_parlay_usage(self, user_id: str) -> int:
        """
        Increment the custom parlay counter for today.
        
        Returns the new count after incrementing.
        Call this AFTER successfully building/analyzing a custom parlay.
        """
        usage = await self._get_or_create_usage_today(user_id)
        usage.custom_parlays_built += 1
        await self.db.commit()
        await self.db.refresh(usage)
        return usage.custom_parlays_built
    
    async def get_remaining_free_parlays(self, user_id: str) -> int:
        """
        Get remaining AI parlay count.
        
        Returns:
        - For premium: remaining out of 100 monthly total (resets every 30 days)
        - For free: remaining out of daily limit
        """
        from app.core.config import settings
        
        if await self.is_user_premium(user_id):
            user = await self._get_user(user_id)
            if user:
                await self._check_and_reset_premium_period(user)
                remaining = max(0, settings.premium_ai_parlays_per_month - user.premium_ai_parlays_used)
                return remaining
            return settings.premium_ai_parlays_per_month  # Fallback
        
        usage = await self._get_or_create_usage_today(user_id)
        return max(0, settings.free_parlays_per_day - usage.free_parlays_generated)
    
    async def _get_or_create_usage_today(self, user_id: str) -> UsageLimit:
        """Get or create usage record for today."""
        try:
            user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        except ValueError:
            logger.error(f"Invalid user_id format: {user_id}")
            raise ValueError(f"Invalid user_id: {user_id}")
        
        today = date.today()
        
        try:
            # Try to get existing usage record
            result = await self.db.execute(
                select(UsageLimit).where(
                    and_(
                        UsageLimit.user_id == user_uuid,
                        UsageLimit.date == today
                    )
                )
            )
            usage = result.scalar_one_or_none()
            
            if not usage:
                # Create new usage record
                usage = UsageLimit(
                    id=uuid.uuid4(),
                    user_id=user_uuid,
                    date=today,
                    free_parlays_generated=0,
                )
                self.db.add(usage)
                try:
                    await self.db.commit()
                    await self.db.refresh(usage)
                except Exception as commit_error:
                    await self.db.rollback()
                    # Check if it's a unique constraint violation (race condition)
                    error_str = str(commit_error).lower()
                    if "unique" in error_str or "duplicate" in error_str:
                        # Another request created it, try to fetch again
                        logger.info(f"Usage record created by another request, fetching again")
                        result = await self.db.execute(
                            select(UsageLimit).where(
                                and_(
                                    UsageLimit.user_id == user_uuid,
                                    UsageLimit.date == today
                                )
                            )
                        )
                        usage = result.scalar_one_or_none()
                        if usage:
                            return usage
                    logger.error(f"Error creating usage record: {commit_error}")
                    raise
            
            return usage
        except Exception as e:
            logger.error(f"Database error in _get_or_create_usage_today for user {user_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    async def _get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        try:
            user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        except ValueError:
            return None
        
        result = await self.db.execute(
            select(User).where(User.id == user_uuid)
        )
        return result.scalar_one_or_none()
    
    async def _check_and_reset_premium_period(self, user: User) -> None:
        """
        Check if premium user's 30-day period has expired and reset if needed.
        
        This should be called before checking/updating premium AI parlay usage.
        """
        from app.core.config import settings
        from datetime import timedelta
        
        now = datetime.now(timezone.utc)
        
        # If no period start date, start a new period
        if not user.premium_ai_parlays_period_start:
            user.premium_ai_parlays_period_start = now
            user.premium_ai_parlays_used = 0
            await self.db.commit()
            await self.db.refresh(user)
            return
        
        # Check if 30 days have passed
        period_end = user.premium_ai_parlays_period_start + timedelta(days=settings.premium_ai_parlays_period_days)
        
        if now >= period_end:
            # Reset period
            user.premium_ai_parlays_period_start = now
            user.premium_ai_parlays_used = 0
            await self.db.commit()
            await self.db.refresh(user)
            logger.info(f"Reset premium AI parlay period for user {user.id}")
    
    async def _get_plan_by_code(self, plan_code: str) -> Optional[SubscriptionPlan]:
        """Get subscription plan by code."""
        result = await self.db.execute(
            select(SubscriptionPlan).where(
                and_(
                    SubscriptionPlan.code == plan_code,
                    SubscriptionPlan.is_active == True
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_active_plans(self) -> list:
        """Get all active subscription plans for pricing page."""
        result = await self.db.execute(
            select(SubscriptionPlan).where(
                SubscriptionPlan.is_active == True
            ).order_by(SubscriptionPlan.display_order)
        )
        plans = result.scalars().all()
        return [p.to_dict() for p in plans]


# Helper function for dependency injection
async def get_subscription_service(db: AsyncSession) -> SubscriptionService:
    """Get subscription service instance."""
    return SubscriptionService(db)

