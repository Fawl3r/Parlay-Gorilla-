"""
Subscription Service for managing user subscriptions and access levels.

Core business logic for:
- Checking if user has premium access
- Enforcing free tier limits (3 AI parlays per day)
- Managing subscription status
- Tracking feature usage
"""

from datetime import datetime, timezone, date
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import uuid
import logging

from app.models.user import User, UserPlan
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.subscription_plan import SubscriptionPlan
from app.services.subscription_access_level import FREE_ACCESS, UserAccessLevel
from app.services.premium_usage_service import PremiumUsageService
from app.services.usage_limit_repository import UsageLimitRepository
from app.utils.datetime_utils import coerce_utc, now_utc

logger = logging.getLogger(__name__)


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
        self.usage_repo = UsageLimitRepository(db)
        self.premium_usage = PremiumUsageService(db)
    
    async def get_user_active_subscription(self, user_id: str) -> Optional[Subscription]:
        """
        Get the user's current subscription that should grant access right now.
        
        Includes "cancelled" subscriptions that are in their grace period
        (i.e., cancelled but still valid until `current_period_end`).
        
        Returns None if user has no valid subscription (free tier).
        """
        try:
            user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        except ValueError:
            logger.warning(f"Invalid user_id format: {user_id}")
            return None
        
        now = now_utc()
        candidate_statuses = [
            SubscriptionStatus.active.value,
            SubscriptionStatus.trialing.value,
            SubscriptionStatus.past_due.value,  # Grace period
            SubscriptionStatus.cancelled.value,  # Cancellation grace period
        ]

        try:
            result = await self.db.execute(
                select(Subscription)
                .where(
                    and_(
                        Subscription.user_id == user_uuid,
                        Subscription.status.in_(candidate_statuses),
                    )
                )
                .order_by(Subscription.created_at.desc())
            )
            subscriptions = list(result.scalars().all())

            for subscription in subscriptions:
                # Cancellation semantics:
                # - If provider marks status=cancelled, the subscription can still be valid
                #   until current_period_end (grace period). We model this using
                #   cancel_at_period_end=True.
                if (
                    subscription.status == SubscriptionStatus.cancelled.value
                    and not bool(subscription.cancel_at_period_end)
                ):
                    continue

                # Lifetime access always grants premium.
                try:
                    if bool(getattr(subscription, "is_lifetime", False) or False):
                        return subscription
                except Exception:
                    # Missing column / schema drift; treat as non-lifetime.
                    pass

                # If we have a period end, enforce it.
                if subscription.current_period_end:
                    period_end = coerce_utc(subscription.current_period_end)
                    if period_end > now:
                        return subscription

                    # Period has expired; mark as expired (best-effort) and keep searching.
                    if subscription.status != SubscriptionStatus.expired.value:
                        subscription.status = SubscriptionStatus.expired.value
                        try:
                            await self.db.commit()
                        except Exception as commit_error:
                            logger.warning(
                                "Failed to mark subscription %s as expired: %s",
                                getattr(subscription, "id", "unknown"),
                                commit_error,
                            )
                            await self.db.rollback()
                    continue

                # No period end:
                # - treat as active for non-cancelled subscriptions (e.g., schema gaps / lifetime-like)
                if subscription.status != SubscriptionStatus.cancelled.value:
                    return subscription

            return None
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
                now = now_utc()
                period_end = coerce_utc(subscription.current_period_end)
                if period_end > now:
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
                    usage = await self.usage_repo.get_or_create_today(user_id)
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
                    ai_snapshot = await self.premium_usage.get_premium_ai_snapshot(user)
                    remaining = ai_snapshot.remaining
                else:
                    remaining = settings.premium_ai_parlays_per_month
                
                # Get custom parlay remaining
                custom_remaining = 0
                if bool(getattr(plan, "can_use_custom_builder", False)) and user:
                    custom_remaining = (await self.premium_usage.get_custom_builder_snapshot(user)).remaining
                
                return UserAccessLevel(
                    tier="premium",
                    plan_code=subscription.plan,
                    can_use_custom_builder=plan.can_use_custom_builder,
                    can_use_upset_finder=plan.can_use_upset_finder,
                    can_use_multi_sport=plan.can_use_multi_sport,
                    can_save_parlays=plan.can_save_parlays,
                    max_ai_parlays_per_day=settings.premium_ai_parlays_per_month,
                    remaining_ai_parlays_today=remaining,
                    max_custom_parlays_per_day=settings.premium_custom_builder_per_month,
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
                ai_snapshot = await self.premium_usage.get_premium_ai_snapshot(user)
                remaining = ai_snapshot.remaining
            else:
                remaining = settings.premium_ai_parlays_per_month
            
            # Get custom parlay remaining
            custom_remaining = 0
            if user:
                custom_remaining = (await self.premium_usage.get_custom_builder_snapshot(user)).remaining
            
            return UserAccessLevel(
                tier="premium",
                plan_code=subscription.plan,
                can_use_custom_builder=True,
                can_use_upset_finder=True,
                can_use_multi_sport=True,
                can_save_parlays=True,
                max_ai_parlays_per_day=settings.premium_ai_parlays_per_month,
                remaining_ai_parlays_today=remaining,
                max_custom_parlays_per_day=settings.premium_custom_builder_per_month,
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
        - User is premium and within their rolling AI period limit
        - User is free and hasn't used weekly limit (5 per rolling 7-day window)
        """
        from app.core.config import settings
        
        if await self.is_user_premium(user_id):
            # Check premium monthly limit
            user = await self._get_user(user_id)
            if user:
                snap = await self.premium_usage.get_premium_ai_snapshot(user)
                return snap.remaining > 0
            return True  # Fallback if user not found
        
        usage = await self.usage_repo.get_or_create_weekly(user_id)
        return usage.can_generate_free_parlay(max_allowed=settings.free_parlays_per_week)
    
    async def increment_free_parlay_usage(self, user_id: str, count: int = 1) -> int:
        """
        Increment the free parlay counter for current rolling 7-day window.
        
        Returns the new count after incrementing.
        Call this AFTER successfully generating a parlay.
        """
        usage = await self.usage_repo.get_or_create_weekly(user_id)
        # Reset window if expired before incrementing
        if usage.is_window_expired(days=7):
            usage.reset_window()
        usage.free_parlays_generated += max(1, int(count or 1))
        await self.db.commit()
        await self.db.refresh(usage)
        return usage.free_parlays_generated
    
    async def increment_premium_ai_parlay_usage(self, user_id: str, count: int = 1) -> int:
        """
        Increment the premium AI parlay counter for current 30-day period.
        
        Automatically resets if period has expired.
        Returns the new count after incrementing.
        Call this AFTER successfully generating a parlay.
        """
        user = await self._get_user(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
        return await self.premium_usage.increment_premium_ai_used(user, count=count)
    
    async def can_use_custom_builder(self, user_id: str) -> bool:
        """
        Check if user can use custom parlay builder.
        
        Returns True if the user has an active premium subscription AND
        still has included custom builder actions remaining in the current rolling period.
        """
        # Must have premium subscription
        if not await self.is_user_premium(user_id):
            return False
        user = await self._get_user(user_id)
        if not user:
            return False
        return (await self.premium_usage.get_custom_builder_snapshot(user)).remaining > 0
    
    async def get_remaining_custom_parlays(self, user_id: str) -> int:
        """
        Get remaining included custom builder actions for the current rolling period.

        Returns 0 if user is not premium.
        """
        if not await self.is_user_premium(user_id):
            return 0
        user = await self._get_user(user_id)
        if not user:
            return 0
        return (await self.premium_usage.get_custom_builder_snapshot(user)).remaining
    
    async def can_use_free_custom_builder(self, user_id: str) -> bool:
        """
        Check if free user can use custom builder (weekly limit).
        
        Returns True if:
        - User is premium (handled separately)
        - User is free and hasn't used weekly custom builder limit (5 per rolling 7-day window)
        """
        from app.core.config import settings
        
        if await self.is_user_premium(user_id):
            # Premium users handled by can_use_custom_builder
            return False
        
        usage = await self.usage_repo.get_or_create_weekly(user_id)
        return usage.can_build_free_custom_parlay(max_allowed=settings.free_custom_parlays_per_week)
    
    async def get_remaining_free_custom_parlays(self, user_id: str) -> int:
        """
        Get remaining free custom builder parlays for current rolling 7-day window.
        
        Returns 0 if user is premium (they use premium limits instead).
        """
        if await self.is_user_premium(user_id):
            return 0
        
        usage = await self.usage_repo.get_or_create_weekly(user_id)
        return usage.remaining_free_custom_parlays
    
    async def increment_free_custom_parlay_usage(self, user_id: str) -> int:
        """
        Increment the free custom builder counter for current rolling 7-day window.
        
        Returns the new count after incrementing.
        Call this AFTER successfully generating a custom parlay.
        """
        usage = await self.usage_repo.get_or_create_weekly(user_id)
        # Reset window if expired before incrementing
        if usage.is_window_expired(days=7):
            usage.reset_window()
        usage.custom_parlays_built += 1
        await self.db.commit()
        await self.db.refresh(usage)
        return usage.custom_parlays_built
    
    async def increment_custom_parlay_usage(self, user_id: str) -> int:
        """
        Increment the premium-included custom builder counter for the current rolling period.

        NOTE: This is used only when the user is consuming included premium quota.
        If the user is paying via credits (premium overage or non-premium), callers
        should deduct credits instead of incrementing this counter.
        """
        user = await self._get_user(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
        return await self.premium_usage.increment_custom_builder_used(user, count=1)
    
    async def get_remaining_free_parlays(self, user_id: str) -> int:
        """
        Get remaining AI parlay count.
        
        Returns:
        - For premium: remaining out of 100 monthly total (resets every 30 days)
        - For free: remaining out of weekly limit (5 per rolling 7-day window)
        """
        from app.core.config import settings
        
        if await self.is_user_premium(user_id):
            user = await self._get_user(user_id)
            if user:
                return (await self.premium_usage.get_premium_ai_snapshot(user)).remaining
            return settings.premium_ai_parlays_per_month  # Fallback
        
        usage = await self.usage_repo.get_or_create_weekly(user_id)
        return usage.remaining_free_parlays
    
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
    
    # Premium period reset logic is centralized in `PremiumUsageService`.
    
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

