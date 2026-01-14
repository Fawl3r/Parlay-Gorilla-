"""
Access Control utilities for feature gating.

FastAPI dependencies for enforcing:
- Premium-only features
- Free tier usage limits
- Subscription status checks

Error codes returned:
- PREMIUM_REQUIRED: Feature requires premium subscription
- FREE_LIMIT_REACHED: Daily free limit exhausted (upgrade to continue)
- LOGIN_REQUIRED: User must be logged in
"""

from fastapi import HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from dataclasses import dataclass
import logging

from app.core.dependencies import get_db, get_current_user, get_optional_user
from app.models.user import User
from app.services.subscription_service import SubscriptionService
from app.services.subscription_access_level import UserAccessLevel

logger = logging.getLogger(__name__)


# Error codes for frontend to handle
class AccessErrorCode:
    PREMIUM_REQUIRED = "PREMIUM_REQUIRED"
    FREE_LIMIT_REACHED = "FREE_LIMIT_REACHED"
    PAY_PER_USE_REQUIRED = "PAY_PER_USE_REQUIRED"  # User needs to purchase a parlay
    LOGIN_REQUIRED = "LOGIN_REQUIRED"
    FEATURE_DISABLED = "FEATURE_DISABLED"


class PaywallException(HTTPException):
    """
    Custom exception for paywall-related errors.
    
    Returns 402 Payment Required with structured error response
    for frontend to display appropriate paywall modal.
    """
    def __init__(
        self,
        error_code: str,
        message: str,
        remaining_today: int = 0,
        feature: Optional[str] = None,
        parlay_type: Optional[str] = None,
        single_price: Optional[float] = None,
        multi_price: Optional[float] = None,
    ):
        detail = {
            "error_code": error_code,
            "message": message,
            "remaining_today": remaining_today,
            "feature": feature,
            "upgrade_url": "/pricing",
        }
        # Add pay-per-use specific fields
        if parlay_type:
            detail["parlay_type"] = parlay_type
        if single_price is not None:
            detail["single_price"] = single_price
        if multi_price is not None:
            detail["multi_price"] = multi_price
        
        super().__init__(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=detail,
        )


@dataclass(frozen=True)
class CustomBuilderAccess:
    """
    Resolved access decision for custom builder AI actions.

    - `use_credits=False`: consuming included premium quota
    - `use_credits=True`: user must spend credits for this action (premium overage or non-premium)
    """

    user: User
    use_credits: bool
    credits_required: int
    remaining_included: int
    included_limit: int


async def get_user_access(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserAccessLevel:
    """
    Dependency that returns user's access level.
    
    Use this when you need access info but don't want to enforce anything.
    Requires authenticated user.
    """
    service = SubscriptionService(db)
    return await service.get_user_access_level(str(user.id))


async def get_optional_user_access(
    user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
) -> Optional[UserAccessLevel]:
    """
    Dependency that returns user's access level or None for anonymous users.
    
    Use this for routes that work for both logged-in and anonymous users.
    """
    if not user:
        return None
    
    service = SubscriptionService(db)
    return await service.get_user_access_level(str(user.id))


async def require_premium(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency that enforces premium subscription.
    
    Raises PaywallException if user is not premium.
    Use this for premium-only features like custom parlay builder.
    
    Usage:
        @router.post("/premium-feature")
        async def premium_feature(user: User = Depends(require_premium)):
            # Only premium users reach here
            ...
    """
    service = SubscriptionService(db)
    is_premium = await service.is_user_premium(str(user.id))
    
    if not is_premium:
        logger.info(f"User {user.id} blocked from premium feature (not premium)")
        raise PaywallException(
            error_code=AccessErrorCode.PREMIUM_REQUIRED,
            message="This feature requires a Gorilla Premium subscription.",
            feature="premium_feature",
        )
    
    return user


async def require_custom_builder_access(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CustomBuilderAccess:
    """
    Dependency that enforces custom parlay builder access.
    
    Allows:
    - Premium users: included quota (25 per rolling period), then credits for overage
    - Free users: 5 free custom builder parlays per rolling 7-day window (no verification)
    - Credit users: pay via credits per action
    
    Raises PaywallException if user cannot use custom builder.
    """
    from app.core.config import settings
    service = SubscriptionService(db)
    credits_required = int(getattr(settings, "credits_cost_custom_builder_action", 3))
    credits_available = int(getattr(user, "credit_balance", 0) or 0)
    
    # Premium path (included monthly quota, then credits overage)
    is_premium = await service.is_user_premium(str(user.id))
    if is_premium:
        remaining = await service.get_remaining_custom_parlays(str(user.id))
        included_limit = int(getattr(settings, "premium_custom_builder_per_month", 0) or 0)

        if remaining > 0:
            return CustomBuilderAccess(
                user=user,
                use_credits=False,
                credits_required=0,
                remaining_included=remaining,
                included_limit=included_limit,
            )

        # Premium user has exhausted included quota; allow credits overage.
        if credits_available >= credits_required:
            return CustomBuilderAccess(
                user=user,
                use_credits=True,
                credits_required=credits_required,
                remaining_included=0,
                included_limit=included_limit,
            )

        logger.info("Premium user %s hit custom builder included quota and lacks credits", user.id)
        raise PaywallException(
            error_code=AccessErrorCode.FREE_LIMIT_REACHED,
            message=(
                f"You've used all {included_limit} included custom builder actions in your current "
                f"{settings.premium_custom_builder_period_days}-day period. "
                f"Additional actions cost {credits_required} credits each."
            ),
            remaining_today=0,
            feature="custom_builder",
        )

    # Free user path (weekly limit, no verification)
    can_use_free = await service.can_use_free_custom_builder(str(user.id))
    if can_use_free:
        remaining_free = await service.get_remaining_free_custom_parlays(str(user.id))
        return CustomBuilderAccess(
            user=user,
            use_credits=False,
            credits_required=0,
            remaining_included=remaining_free,
            included_limit=settings.free_custom_parlays_per_week,
        )

    # Free user hit weekly limit - check if they have credits
    if credits_available >= credits_required:
        return CustomBuilderAccess(
            user=user,
            use_credits=True,
            credits_required=credits_required,
            remaining_included=0,
            included_limit=0,
        )

    logger.info(f"User {user.id} blocked from custom builder (hit weekly limit, no credits)")
    raise PaywallException(
        error_code=AccessErrorCode.FREE_LIMIT_REACHED,
        message=(
            f"You've used all {settings.free_custom_parlays_per_week} free custom builder parlays for this week. "
            f"Buy credits ({credits_required} per action) or upgrade to Elite."
        ),
        remaining_today=0,
        feature="custom_builder",
    )


async def require_upset_finder_access(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency that enforces upset finder access.
    
    Raises PaywallException if user cannot use upset finder.
    """
    service = SubscriptionService(db)
    access = await service.get_user_access_level(str(user.id))
    
    if not access.can_use_upset_finder:
        logger.info(f"User {user.id} blocked from upset finder (tier: {access.tier})")
        raise PaywallException(
            error_code=AccessErrorCode.PREMIUM_REQUIRED,
            message="The Gorilla Upset Finder requires Gorilla Premium.",
            feature="upset_finder",
        )
    
    return user


async def enforce_free_parlay_limit(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency that enforces parlay limit.
    
    - Premium users: Allowed if within the rolling premium AI limit (settings.premium_ai_parlays_per_month / settings.premium_ai_parlays_period_days)
    - Free users: Allowed if haven't used weekly limit (5 per rolling 7-day window)
    
    Raises PaywallException with FREE_LIMIT_REACHED if limit exceeded.
    
    IMPORTANT: Call consume_parlay_access() AFTER successfully
    generating the parlay, not before.
    """
    from app.core.config import settings
    service = SubscriptionService(db)
    
    is_premium = await service.is_user_premium(str(user.id))
    remaining = await service.get_remaining_free_parlays(str(user.id))
    
    if is_premium:
        # Check premium monthly limit
        if remaining <= 0:
            logger.info(f"Premium user {user.id} hit premium AI parlay limit (used {settings.premium_ai_parlays_per_month})")
            raise PaywallException(
                error_code=AccessErrorCode.FREE_LIMIT_REACHED,
                message=(
                    f"You've used all {settings.premium_ai_parlays_per_month} parlays in your current "
                    f"{settings.premium_ai_parlays_period_days}-day period. Limit resets automatically."
                ),
                remaining_today=0,
                feature="ai_parlay",
            )
        return user
    
    # Check free limit (weekly)
    can_use = await service.can_use_free_parlay(str(user.id))
    
    if not can_use:
        logger.info(f"User {user.id} hit free parlay limit (remaining: {remaining})")
        raise PaywallException(
            error_code=AccessErrorCode.FREE_LIMIT_REACHED,
            message=(
                f"You've used all {settings.free_parlays_per_week} free parlays for this week. "
                f"Buy credits or upgrade to Elite."
            ),
            remaining_today=remaining,
            feature="ai_parlay",
        )
    
    return user


async def check_and_increment_parlay_usage(
    user: User,
    db: AsyncSession,
) -> None:
    """
    Helper to increment parlay usage for free users.
    
    Call this AFTER successfully generating a parlay.
    Premium users are not affected.
    """
    service = SubscriptionService(db)
    
    if not await service.is_user_premium(str(user.id)):
        await service.increment_free_parlay_usage(str(user.id))
        logger.info(f"Incremented parlay usage for free user {user.id}")


async def check_parlay_access_with_purchase(
    user: User,
    db: AsyncSession,
    is_multi_sport: bool = False,
    usage_units: int = 1,
    allow_purchases: bool = True,
) -> dict:
    """
    Check if user can generate a parlay, considering free limit and purchases.
    
    Returns a dict with:
    - can_generate: bool - whether user can generate parlay
    - use_purchase: bool - whether a purchase will be consumed
    - use_free: bool - whether a free parlay will be used
    - error_code: str - error code if cannot generate
    
    This doesn't raise exceptions - let the caller decide how to handle.
    """
    from app.services.parlay_purchase_service import ParlayPurchaseService
    from app.core.config import settings
    
    try:
        subscription_service = SubscriptionService(db)
        purchase_service = ParlayPurchaseService(db)
        units = max(1, int(usage_units or 1))
        credits_required = int(getattr(settings, "credits_cost_ai_parlay", 3)) * units
        credits_available = int(getattr(user, "credit_balance", 0) or 0)
        
        # Check premium monthly limit
        try:
            is_premium = await subscription_service.is_user_premium(str(user.id))
        except Exception as e:
            logger.error(f"Error checking premium status for user {user.id}: {e}", exc_info=True)
            # Default to non-premium on error
            is_premium = False
        
        if is_premium:
            try:
                remaining = await subscription_service.get_remaining_free_parlays(str(user.id))
            except Exception as e:
                logger.error(f"Error getting remaining parlays for premium user {user.id}: {e}", exc_info=True)
                # Default to 0 remaining on error (conservative - blocks generation)
                remaining = 0
            if remaining >= units:
                return {
                    "can_generate": True,
                    "use_purchase": False,
                    "use_free": False,
                    "use_credits": False,
                    "is_premium": True,
                    "usage_units": units,
                    "error_code": None,
                }
            else:
                # Premium user hit monthly limit
                return {
                    "can_generate": False,
                    "use_purchase": False,
                    "use_free": False,
                    "use_credits": False,
                    "is_premium": True,
                    "usage_units": units,
                    "remaining_free": remaining,
                    "credits_required": credits_required,
                    "credits_available": credits_available,
                    "error_code": AccessErrorCode.FREE_LIMIT_REACHED,
                }
        
        # Check free limit first
        try:
            remaining_free = await subscription_service.get_remaining_free_parlays(str(user.id))
        except Exception as e:
            logger.error(f"Error getting remaining free parlays for user {user.id}: {e}", exc_info=True)
            # Default to 0 remaining on error (conservative - blocks generation)
            remaining_free = 0
        
        if remaining_free >= units:
            return {
                "can_generate": True,
                "use_purchase": False,
                "use_free": True,
                "use_credits": False,
                "is_premium": False,
                "remaining_free": remaining_free,
                "usage_units": units,
                "credits_required": credits_required,
                "credits_available": credits_available,
                "error_code": None,
            }

        # Free limit reached - check credits next
        if credits_available >= credits_required:
            return {
                "can_generate": True,
                "use_purchase": False,
                "use_free": False,
                "use_credits": True,
                "is_premium": False,
                "remaining_free": remaining_free,
                "usage_units": units,
                "credits_required": credits_required,
                "credits_available": credits_available,
                "error_code": None,
            }

        # Then check for purchases (only supported for single-use requests)
        if allow_purchases and units == 1:
            try:
                has_purchase = await purchase_service.has_unused_purchase(str(user.id), is_multi_sport)
            except Exception as e:
                logger.error(f"Error checking purchases for user {user.id}: {e}", exc_info=True)
                # Default to no purchase on error (conservative)
                has_purchase = False
            if has_purchase:
                return {
                    "can_generate": True,
                    "use_purchase": True,
                    "use_free": False,
                    "use_credits": False,
                    "is_premium": False,
                    "usage_units": units,
                    "remaining_free": 0,
                    "credits_required": credits_required,
                    "credits_available": credits_available,
                    "error_code": None,
                }
        
        # No free parlays and no purchase - need to pay
        return {
            "can_generate": False,
            "use_purchase": False,
            "use_free": False,
            "use_credits": False,
            "is_premium": False,
            "usage_units": units,
            "remaining_free": remaining_free,
            "credits_required": credits_required,
            "credits_available": credits_available,
            "error_code": AccessErrorCode.PAY_PER_USE_REQUIRED if allow_purchases and units == 1 else AccessErrorCode.FREE_LIMIT_REACHED,
            "is_multi_sport": is_multi_sport,
            "single_price": settings.single_parlay_price_dollars,
            "multi_price": settings.multi_parlay_price_dollars,
        }
    except Exception as e:
        # Catch any unexpected errors and return a safe default response
        logger.error(f"Unexpected error in check_parlay_access_with_purchase for user {user.id}: {e}", exc_info=True)
        try:
            units = max(1, int(usage_units or 1))
            credits_required = int(getattr(settings, "credits_cost_ai_parlay", 3)) * units
            credits_available = int(getattr(user, "credit_balance", 0) or 0)
        except:
            units = 1
            credits_required = 3
            credits_available = 0
        return {
            "can_generate": False,
            "use_purchase": False,
            "use_free": False,
            "use_credits": False,
            "is_premium": False,
            "usage_units": units,
            "remaining_free": 0,
            "credits_required": credits_required,
            "credits_available": credits_available,
            "error_code": AccessErrorCode.FREE_LIMIT_REACHED,
            "is_multi_sport": is_multi_sport,
            "single_price": settings.single_parlay_price_dollars,
            "multi_price": settings.multi_parlay_price_dollars,
        }


async def consume_parlay_access(
    user: User,
    db: AsyncSession,
    access_info: dict,
    parlay_id: Optional[str] = None,
) -> None:
    """
    Consume parlay access after successful generation.
    
    Based on access_info from check_parlay_access_with_purchase(),
    either increments free usage, premium monthly usage, or marks purchase as used.
    
    Call this AFTER successfully generating the parlay.
    """
    from app.services.parlay_purchase_service import ParlayPurchaseService
    from app.core.config import settings
    
    units = max(1, int(access_info.get("usage_units") or 1))

    if access_info.get("is_premium"):
        # Increment premium AI parlay count (monthly)
        subscription_service = SubscriptionService(db)
        await subscription_service.increment_premium_ai_parlay_usage(str(user.id), count=units)
        logger.info(f"Used premium AI parlay x{units} for user {user.id}")
        return
    
    if access_info.get("use_free"):
        # Increment free usage
        subscription_service = SubscriptionService(db)
        await subscription_service.increment_free_parlay_usage(str(user.id), count=units)
        logger.info(f"Used free AI parlay x{units} for user {user.id}")

    elif access_info.get("use_credits"):
        from app.services.credit_balance_service import CreditBalanceService
        credits_required = int(access_info.get("credits_required") or 0)
        credits_required = credits_required if credits_required > 0 else int(getattr(settings, "credits_cost_ai_parlay", 3)) * units
        credit_service = CreditBalanceService(db)
        new_balance = await credit_service.try_spend(str(user.id), credits_required)
        if new_balance is None:
            # Best-effort: don't block response; log for investigation.
            logger.error(
                "Failed to spend credits (user=%s, required=%s, units=%s)",
                user.id,
                credits_required,
                units,
            )
        else:
            logger.info(f"Spent {credits_required} credits for user {user.id} (new balance: {new_balance})")
    
    elif access_info.get("use_purchase"):
        # Mark purchase as used
        if units != 1:
            logger.warning("Attempted to consume purchase with units=%s (user=%s). Skipping.", units, user.id)
            return
        purchase_service = ParlayPurchaseService(db)
        is_multi = access_info.get("is_multi_sport", False)
        await purchase_service.mark_purchase_used(str(user.id), is_multi, parlay_id)
        logger.info(f"Used purchased parlay for user {user.id}")

