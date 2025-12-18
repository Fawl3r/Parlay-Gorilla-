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
import logging

from app.core.dependencies import get_db, get_current_user, get_optional_user
from app.models.user import User
from app.services.subscription_service import SubscriptionService, UserAccessLevel

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
) -> User:
    """
    Dependency that enforces custom parlay builder access.
    
    Requires:
    - Active premium subscription (no credits/pay-per-use allowed)
    - Within daily limit (15 custom parlays per day)
    
    Raises PaywallException if user cannot use custom builder.
    """
    from app.core.config import settings
    service = SubscriptionService(db)
    
    # Check if user has premium subscription
    is_premium = await service.is_user_premium(str(user.id))
    if not is_premium:
        logger.info(f"User {user.id} blocked from custom builder (not premium)")
        raise PaywallException(
            error_code=AccessErrorCode.PREMIUM_REQUIRED,
            message="The custom parlay builder requires an active Gorilla Premium subscription. Credits cannot be used for this feature.",
            feature="custom_builder",
        )
    
    # Check daily limit
    can_use = await service.can_use_custom_builder(str(user.id))
    remaining = await service.get_remaining_custom_parlays(str(user.id))
    
    if not can_use:
        logger.info(f"Premium user {user.id} hit custom parlay daily limit (remaining: {remaining})")
        raise PaywallException(
            error_code=AccessErrorCode.FREE_LIMIT_REACHED,
            message=f"You've used all {settings.premium_custom_parlays_per_day} custom parlays for today. Your limit will reset tomorrow.",
            remaining_today=remaining,
            feature="custom_builder",
        )
    
    return user


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
    
    - Premium users: Allowed if haven't used 100 AI parlays this month
    - Free users: Allowed if haven't used daily limit
    
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
            logger.info(f"Premium user {user.id} hit monthly AI parlay limit (used 100)")
            raise PaywallException(
                error_code=AccessErrorCode.FREE_LIMIT_REACHED,
                message="You've used all 100 AI parlays this month. Your limit will reset in 30 days. Custom parlays remain unlimited!",
                remaining_today=0,
                feature="ai_parlay",
            )
        return user
    
    # Check free limit
    can_use = await service.can_use_free_parlay(str(user.id))
    
    if not can_use:
        logger.info(f"User {user.id} hit free parlay limit (remaining: {remaining})")
        raise PaywallException(
            error_code=AccessErrorCode.FREE_LIMIT_REACHED,
            message="You've used all 3 free AI parlays for today. Upgrade to Gorilla Premium for 100 AI parlays per month!",
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
    
    subscription_service = SubscriptionService(db)
    purchase_service = ParlayPurchaseService(db)
    
    # Check premium monthly limit
    is_premium = await subscription_service.is_user_premium(str(user.id))
    if is_premium:
        remaining = await subscription_service.get_remaining_free_parlays(str(user.id))
        if remaining > 0:
            return {
                "can_generate": True,
                "use_purchase": False,
                "use_free": False,
                "is_premium": True,
                "error_code": None,
            }
        else:
            # Premium user hit monthly limit
            return {
                "can_generate": False,
                "use_purchase": False,
                "use_free": False,
                "is_premium": True,
                "remaining_free": 0,
                "error_code": AccessErrorCode.FREE_LIMIT_REACHED,
            }
    
    # Check free limit first
    can_use_free = await subscription_service.can_use_free_parlay(str(user.id))
    remaining_free = await subscription_service.get_remaining_free_parlays(str(user.id))
    
    if can_use_free:
        return {
            "can_generate": True,
            "use_purchase": False,
            "use_free": True,
            "is_premium": False,
            "remaining_free": remaining_free,
            "error_code": None,
        }
    
    # Free limit reached - check for purchases
    has_purchase = await purchase_service.has_unused_purchase(str(user.id), is_multi_sport)
    
    if has_purchase:
        return {
            "can_generate": True,
            "use_purchase": True,
            "use_free": False,
            "is_premium": False,
            "remaining_free": 0,
            "error_code": None,
        }
    
    # No free parlays and no purchase - need to pay
    return {
        "can_generate": False,
        "use_purchase": False,
        "use_free": False,
        "is_premium": False,
        "remaining_free": 0,
        "error_code": AccessErrorCode.PAY_PER_USE_REQUIRED,
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
    
    if access_info.get("is_premium"):
        # Increment premium AI parlay count (monthly)
        subscription_service = SubscriptionService(db)
        await subscription_service.increment_premium_ai_parlay_usage(str(user.id))
        logger.info(f"Used premium AI parlay for user {user.id}")
        return
    
    if access_info.get("use_free"):
        # Increment free usage
        subscription_service = SubscriptionService(db)
        await subscription_service.increment_free_parlay_usage(str(user.id))
        logger.info(f"Used free parlay for user {user.id}")
    
    elif access_info.get("use_purchase"):
        # Mark purchase as used
        purchase_service = ParlayPurchaseService(db)
        is_multi = access_info.get("is_multi_sport", False)
        await purchase_service.mark_purchase_used(str(user.id), is_multi, parlay_id)
        logger.info(f"Used purchased parlay for user {user.id}")

