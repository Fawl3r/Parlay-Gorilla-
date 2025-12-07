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
    ):
        detail = {
            "error_code": error_code,
            "message": message,
            "remaining_today": remaining_today,
            "feature": feature,
            "upgrade_url": "/pricing",
        }
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
    
    Raises PaywallException if user cannot use custom builder.
    """
    service = SubscriptionService(db)
    access = await service.get_user_access_level(str(user.id))
    
    if not access.can_use_custom_builder:
        logger.info(f"User {user.id} blocked from custom builder (tier: {access.tier})")
        raise PaywallException(
            error_code=AccessErrorCode.PREMIUM_REQUIRED,
            message="The custom parlay builder requires Gorilla Premium.",
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
    Dependency that enforces free tier parlay limit.
    
    - Premium users: Always allowed (returns user)
    - Free users: Allowed if haven't used daily limit
    
    Raises PaywallException with FREE_LIMIT_REACHED if limit exceeded.
    
    IMPORTANT: Call increment_free_parlay_usage() AFTER successfully
    generating the parlay, not before.
    
    Usage:
        @router.post("/ai-parlay")
        async def generate_parlay(
            user: User = Depends(enforce_free_parlay_limit),
            db: AsyncSession = Depends(get_db),
        ):
            # Generate parlay...
            
            # Only increment if NOT premium
            service = SubscriptionService(db)
            if not await service.is_user_premium(str(user.id)):
                await service.increment_free_parlay_usage(str(user.id))
    """
    service = SubscriptionService(db)
    
    # Premium users bypass limit
    if await service.is_user_premium(str(user.id)):
        return user
    
    # Check free limit
    can_use = await service.can_use_free_parlay(str(user.id))
    remaining = await service.get_remaining_free_parlays(str(user.id))
    
    if not can_use:
        logger.info(f"User {user.id} hit free parlay limit (remaining: {remaining})")
        raise PaywallException(
            error_code=AccessErrorCode.FREE_LIMIT_REACHED,
            message="You've used your free AI parlay for today. Upgrade to Gorilla Premium for unlimited parlays!",
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

