"""
Access Control Service for parlay generation.

Implements the hybrid access model:
1. Free parlays for new users (2 lifetime)
2. Subscription-based access (daily limits)
3. Credit-based access (per-use)

Business logic:
1. If free_parlays_used < free_parlays_total → use free
2. Else if active subscription AND within daily_parlay_limit → use subscription
3. Else if credit_balance >= required_credits → use credits
4. Else → deny
"""

from dataclasses import dataclass
from typing import Optional, Tuple
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date
import uuid
import logging

from app.models.user import User, SubscriptionStatusEnum
from app.core.billing_config import (
    get_subscription_plan,
    get_parlay_credit_cost,
    ParlayType,
    PARLAY_CREDIT_COSTS,
)

logger = logging.getLogger(__name__)


@dataclass
class AccessCheckResult:
    """Result of an access check"""
    allowed: bool
    access_type: Optional[str] = None  # 'free', 'subscription', 'credits', None
    reason: Optional[str] = None
    credits_required: int = 0
    credits_available: int = 0
    free_remaining: int = 0
    subscription_remaining: int = 0
    
    def to_dict(self) -> dict:
        return {
            "allowed": self.allowed,
            "access_type": self.access_type,
            "reason": self.reason,
            "credits_required": self.credits_required,
            "credits_available": self.credits_available,
            "free_remaining": self.free_remaining,
            "subscription_remaining": self.subscription_remaining,
        }


@dataclass
class AccessStatus:
    """Full access status for a user"""
    # Free tier
    free_total: int
    free_used: int
    free_remaining: int
    
    # Subscription
    has_subscription: bool
    subscription_plan: Optional[str]
    subscription_daily_limit: int
    subscription_used_today: int
    subscription_remaining_today: int
    
    # Credits
    credit_balance: int

    # Premium rolling-period usage (display-only)
    custom_builder_used: int
    custom_builder_limit: int
    custom_builder_remaining: int
    custom_builder_period_start: Optional[str]

    inscriptions_used: int
    inscriptions_limit: int
    inscriptions_remaining: int
    inscriptions_period_start: Optional[str]
    
    # Computed
    can_generate_standard: bool
    can_generate_elite: bool
    
    def to_dict(self) -> dict:
        return {
            "free": {
                "total": self.free_total,
                "used": self.free_used,
                "remaining": self.free_remaining,
            },
            "subscription": {
                "active": self.has_subscription,
                "plan": self.subscription_plan,
                "daily_limit": self.subscription_daily_limit,
                "used_today": self.subscription_used_today,
                "remaining_today": self.subscription_remaining_today,
            },
            "custom_builder": {
                "used": self.custom_builder_used,
                "limit": self.custom_builder_limit,
                "remaining": self.custom_builder_remaining,
                "period_start": self.custom_builder_period_start,
            },
            "inscriptions": {
                "used": self.inscriptions_used,
                "limit": self.inscriptions_limit,
                "remaining": self.inscriptions_remaining,
                "period_start": self.inscriptions_period_start,
            },
            "credits": {
                "balance": self.credit_balance,
                "standard_cost": PARLAY_CREDIT_COSTS[ParlayType.STANDARD.value],
                "elite_cost": PARLAY_CREDIT_COSTS[ParlayType.ELITE.value],
            },
            "can_generate": {
                "standard": self.can_generate_standard,
                "elite": self.can_generate_elite,
            },
        }


class AccessControlService:
    """
    Service for controlling access to parlay generation.
    
    Implements a hybrid access model with the following priority:
    1. Free parlays (lifetime, not daily)
    2. Subscription (daily limits based on plan)
    3. Credits (per-use, deducted on use)
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        try:
            user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        except ValueError:
            logger.error(f"Invalid user_id format: {user_id}")
            return None
        
        result = await self.db.execute(
            select(User).where(User.id == user_uuid)
        )
        return result.scalar_one_or_none()
    
    async def get_access_status(self, user_id: str) -> Optional[AccessStatus]:
        """
        Get the full access status for a user.
        
        Returns detailed information about free parlays, subscription,
        and credits for display in the UI.
        """
        user = await self.get_user(user_id)
        if not user:
            return None
        
        # Reset daily counter if needed
        await self._reset_daily_counter_if_needed(user)
        
        # Calculate values
        free_remaining = user.free_parlays_remaining
        
        sub_daily_limit = user.get_subscription_daily_limit() if user.has_active_subscription else 0
        sub_remaining = user.subscription_parlays_remaining_today
        
        standard_cost = get_parlay_credit_cost(ParlayType.STANDARD.value)
        elite_cost = get_parlay_credit_cost(ParlayType.ELITE.value)
        
        # Determine if user can generate
        can_standard = (
            free_remaining > 0 or
            sub_remaining > 0 or
            user.credit_balance >= standard_cost
        )
        can_elite = (
            free_remaining > 0 or
            sub_remaining > 0 or
            user.credit_balance >= elite_cost
        )
        
        # Premium rolling-period usage (custom builder + inscriptions)
        custom_used = 0
        custom_limit = 0
        custom_remaining = 0
        custom_period_start = None

        ins_used = 0
        ins_limit = 0
        ins_remaining = 0
        ins_period_start = None

        try:
            from app.services.subscription_service import SubscriptionService
            from app.services.premium_usage_service import PremiumUsageService

            is_premium = await SubscriptionService(self.db).is_user_premium(user_id)
            if is_premium:
                usage_service = PremiumUsageService(self.db)
                custom_snap = await usage_service.get_custom_builder_snapshot(user)
                custom_used = custom_snap.used
                custom_limit = custom_snap.limit
                custom_remaining = custom_snap.remaining
                custom_period_start = custom_snap.period_start.isoformat() if custom_snap.period_start else None

                ins_snap = await usage_service.get_inscriptions_snapshot(user)
                ins_used = ins_snap.used
                ins_limit = ins_snap.limit
                ins_remaining = ins_snap.remaining
                ins_period_start = ins_snap.period_start.isoformat() if ins_snap.period_start else None
        except Exception as e:
            logger.warning("Failed to compute premium usage snapshots for billing UI: %s", e)

        return AccessStatus(
            free_total=user.free_parlays_total,
            free_used=user.free_parlays_used,
            free_remaining=free_remaining,
            has_subscription=user.has_active_subscription,
            subscription_plan=user.subscription_plan,
            subscription_daily_limit=sub_daily_limit,
            subscription_used_today=user.daily_parlays_used if user.daily_parlays_usage_date == date.today() else 0,
            subscription_remaining_today=sub_remaining,
            credit_balance=user.credit_balance,
            custom_builder_used=custom_used,
            custom_builder_limit=custom_limit,
            custom_builder_remaining=custom_remaining,
            custom_builder_period_start=custom_period_start,
            inscriptions_used=ins_used,
            inscriptions_limit=ins_limit,
            inscriptions_remaining=ins_remaining,
            inscriptions_period_start=ins_period_start,
            can_generate_standard=can_standard,
            can_generate_elite=can_elite,
        )
    
    async def can_generate_parlay(
        self,
        user_id: str,
        parlay_type: str = ParlayType.STANDARD.value
    ) -> AccessCheckResult:
        """
        Check if user can generate a parlay.
        
        Returns an AccessCheckResult indicating:
        - Whether access is allowed
        - Which access type would be used (free/subscription/credits)
        - Reason if denied
        """
        user = await self.get_user(user_id)
        if not user:
            return AccessCheckResult(
                allowed=False,
                reason="User not found",
            )
        
        # Reset daily counter if needed
        await self._reset_daily_counter_if_needed(user)
        
        credits_required = get_parlay_credit_cost(parlay_type)
        
        # 1. Check free parlays first
        if user.has_free_parlays_remaining:
            return AccessCheckResult(
                allowed=True,
                access_type="free",
                free_remaining=user.free_parlays_remaining,
                subscription_remaining=user.subscription_parlays_remaining_today,
                credits_available=user.credit_balance,
            )
        
        # 2. Check subscription
        if user.has_active_subscription:
            if user.is_within_daily_subscription_limit:
                return AccessCheckResult(
                    allowed=True,
                    access_type="subscription",
                    free_remaining=0,
                    subscription_remaining=user.subscription_parlays_remaining_today,
                    credits_available=user.credit_balance,
                )
            else:
                # Subscription active but daily limit reached
                # Fall through to check credits
                pass
        
        # 3. Check credits
        if user.has_credits(credits_required):
            return AccessCheckResult(
                allowed=True,
                access_type="credits",
                credits_required=credits_required,
                free_remaining=0,
                subscription_remaining=0,
                credits_available=user.credit_balance,
            )
        
        # 4. Access denied
        if user.has_active_subscription:
            reason = f"Daily subscription limit reached ({user.daily_parlays_used}/{user.get_subscription_daily_limit()}). Buy credits to generate more parlays."
        else:
            reason = "No free parlays remaining. Subscribe or buy credits to continue."
        
        return AccessCheckResult(
            allowed=False,
            reason=reason,
            credits_required=credits_required,
            free_remaining=0,
            subscription_remaining=0,
            credits_available=user.credit_balance,
        )
    
    async def record_parlay_usage(
        self,
        user_id: str,
        parlay_type: str = ParlayType.STANDARD.value,
        force_access_type: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Record parlay usage after successful generation.
        
        This should be called AFTER the parlay is successfully generated.
        
        Args:
            user_id: User ID
            parlay_type: Type of parlay generated
            force_access_type: If provided, forces the specific access type (for testing)
        
        Returns:
            Tuple of (success, access_type_used or error_message)
        """
        user = await self.get_user(user_id)
        if not user:
            return False, "User not found"
        
        # Reset daily counter if needed
        await self._reset_daily_counter_if_needed(user)
        
        credits_required = get_parlay_credit_cost(parlay_type)
        
        # Determine access type if not forced
        if force_access_type:
            access_type = force_access_type
        else:
            check = await self.can_generate_parlay(user_id, parlay_type)
            if not check.allowed:
                return False, check.reason or "Access denied"
            access_type = check.access_type
        
        # Record usage based on access type
        try:
            if access_type == "free":
                if user.use_free_parlay():
                    await self.db.commit()
                    logger.info(f"User {user_id} used free parlay ({user.free_parlays_remaining} remaining)")
                    return True, "free"
                return False, "No free parlays remaining"
            
            elif access_type == "subscription":
                if user.use_subscription_parlay():
                    await self.db.commit()
                    logger.info(f"User {user_id} used subscription parlay ({user.subscription_parlays_remaining_today} remaining today)")
                    return True, "subscription"
                return False, "Subscription limit reached"
            
            elif access_type == "credits":
                if user.use_credits(credits_required):
                    await self.db.commit()
                    logger.info(f"User {user_id} used {credits_required} credits ({user.credit_balance} remaining)")
                    return True, "credits"
                return False, f"Insufficient credits (need {credits_required}, have {user.credit_balance})"
            
            else:
                return False, f"Unknown access type: {access_type}"
        
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error recording parlay usage for user {user_id}: {e}")
            return False, str(e)
    
    async def add_credits(self, user_id: str, amount: int) -> Tuple[bool, int]:
        """
        Add credits to user's balance.
        
        Returns:
            Tuple of (success, new_balance or 0 on failure)
        """
        user = await self.get_user(user_id)
        if not user:
            return False, 0
        
        try:
            user.add_credits(amount)
            await self.db.commit()
            await self.db.refresh(user)
            logger.info(f"Added {amount} credits to user {user_id}. New balance: {user.credit_balance}")
            return True, user.credit_balance
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error adding credits for user {user_id}: {e}")
            return False, 0
    
    async def _reset_daily_counter_if_needed(self, user: User) -> bool:
        """
        Reset daily parlay counter if it's a new day.
        
        Returns True if counter was reset.
        """
        today = date.today()
        if user.daily_parlays_usage_date != today:
            user.daily_parlays_used = 0
            user.daily_parlays_usage_date = today
            return True
        return False


# Factory function for dependency injection
async def get_access_control_service(db: AsyncSession) -> AccessControlService:
    """Get access control service instance."""
    return AccessControlService(db)




