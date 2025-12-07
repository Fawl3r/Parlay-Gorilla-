"""
Subscription Service for managing user subscriptions and access levels.

Core business logic for:
- Checking if user has premium access
- Enforcing free tier limits (1 AI parlay per day)
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
        
        Returns True if user has active, trialing, or past_due subscription.
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
            
            # Check if within valid period
            if subscription.current_period_end:
                if subscription.current_period_end > datetime.now(timezone.utc):
                    return True
            else:
                # No period end = active (e.g., lifetime)
                return True
        
        return False
    
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
                    usage = await self._get_or_create_usage_today(user_id)
                    remaining = max(0, 1 - usage.free_parlays_generated)
                except Exception as usage_error:
                    # If we can't get usage, default to 1 remaining
                    logger.warning(f"Error getting usage for user {user_id}: {usage_error}, defaulting to 1 remaining")
                    remaining = 1
                
                return UserAccessLevel(
                    tier="free",
                    plan_code=None,
                    can_use_custom_builder=False,
                    can_use_upset_finder=False,
                    can_use_multi_sport=False,
                    can_save_parlays=False,
                    max_ai_parlays_per_day=1,
                    remaining_ai_parlays_today=remaining,
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
                
                return UserAccessLevel(
                    tier="premium",
                    plan_code=subscription.plan,
                    can_use_custom_builder=plan.can_use_custom_builder,
                    can_use_upset_finder=plan.can_use_upset_finder,
                    can_use_multi_sport=plan.can_use_multi_sport,
                    can_save_parlays=plan.can_save_parlays,
                    max_ai_parlays_per_day=plan.max_ai_parlays_per_day,
                    remaining_ai_parlays_today=-1,  # Unlimited for premium
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
            
            return UserAccessLevel(
                tier="premium",
                plan_code=subscription.plan,
                can_use_custom_builder=True,
                can_use_upset_finder=True,
                can_use_multi_sport=True,
                can_save_parlays=True,
                max_ai_parlays_per_day=-1,
                remaining_ai_parlays_today=-1,
                is_lifetime=subscription.is_lifetime,
                subscription_end=subscription.current_period_end,
            )
        except Exception as e:
            logger.error(f"Error in get_user_access_level for user {user_id}: {e}")
            # Return default free tier on any error
            return FREE_ACCESS
    
    async def can_use_free_parlay(self, user_id: str) -> bool:
        """
        Check if free user can generate another AI parlay today.
        
        Returns True if:
        - User is premium (unlimited)
        - User is free and hasn't used daily limit
        """
        if await self.is_user_premium(user_id):
            return True
        
        usage = await self._get_or_create_usage_today(user_id)
        return usage.free_parlays_generated < 1
    
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
    
    async def get_remaining_free_parlays(self, user_id: str) -> int:
        """
        Get remaining free parlay count for today.
        
        Returns -1 for premium users (unlimited).
        Returns 0 or 1 for free users.
        """
        if await self.is_user_premium(user_id):
            return -1
        
        usage = await self._get_or_create_usage_today(user_id)
        return max(0, 1 - usage.free_parlays_generated)
    
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

