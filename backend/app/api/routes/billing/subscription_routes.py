"""
Billing API routes for subscription checkout sessions.

Handles checkout creation for:
- LemonSqueezy (card payments, recurring subscriptions)
- Coinbase Commerce (crypto payments, lifetime access)
"""

from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import httpx
import logging

from app.core.config import settings
from app.core.dependencies import get_current_user, get_db
from app.models.subscription_plan import SubscriptionPlan
from app.models.user import User
from app.services.subscription_service import SubscriptionService
from app.services.lemonsqueezy_subscription_variant_resolver import (
    LemonSqueezySubscriptionVariantResolver,
)

logger = logging.getLogger(__name__)
router = APIRouter()


class CheckoutRequest(BaseModel):
    plan_code: str


class CheckoutResponse(BaseModel):
    checkout_url: str
    provider: str
    plan_code: str


class SubscriptionBalancesResponse(BaseModel):
    credit_balance: int

    free_parlays_total: int
    free_parlays_used: int
    free_parlays_remaining: int

    daily_ai_limit: int
    daily_ai_used: int
    daily_ai_remaining: int

    premium_ai_parlays_used: int
    premium_ai_period_start: Optional[str]


class SubscriptionStatusResponse(BaseModel):
    tier: str
    plan_code: Optional[str]
    can_use_custom_builder: bool
    can_use_upset_finder: bool
    can_use_multi_sport: bool
    can_save_parlays: bool
    max_ai_parlays_per_day: int
    remaining_ai_parlays_today: int
    unlimited_ai_parlays: bool
    credit_balance: int
    is_lifetime: bool
    subscription_end: Optional[str]
    balances: SubscriptionBalancesResponse


class PlanResponse(BaseModel):
    id: str
    code: str
    name: str
    description: Optional[str]
    price_cents: int
    price_dollars: float
    currency: str
    billing_cycle: str
    provider: str
    is_active: bool
    is_featured: bool
    is_free: bool
    is_lifetime: bool
    features: dict


@router.get("/billing/status", response_model=SubscriptionStatusResponse)
async def get_subscription_status(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get current user's subscription status and access level.

    Returns tier, feature permissions, and remaining usage.
    """
    try:
        service = SubscriptionService(db)
        access = await service.get_user_access_level(str(user.id))

        # Safely format subscription_end
        subscription_end_str = None
        if access.subscription_end:
            try:
                if hasattr(access.subscription_end, "isoformat"):
                    subscription_end_str = access.subscription_end.isoformat()
                else:
                    subscription_end_str = str(access.subscription_end)
            except Exception as e:
                logger.warning(f"Error formatting subscription_end: {e}")
                subscription_end_str = None

        credit_balance = int(getattr(user, "credit_balance", 0) or 0)

        free_total = int(getattr(user, "free_parlays_total", 0) or 0)
        free_used = int(getattr(user, "free_parlays_used", 0) or 0)
        free_remaining = max(0, free_total - free_used)

        # Daily counter reset is handled elsewhere; for display we treat it as 0 when the stored
        # usage date isn't today.
        daily_used_raw = int(getattr(user, "daily_parlays_used", 0) or 0)
        daily_date = getattr(user, "daily_parlays_usage_date", None)
        daily_used = daily_used_raw if daily_date == date.today() else 0

        premium_used = int(getattr(user, "premium_ai_parlays_used", 0) or 0)
        premium_period_start = getattr(user, "premium_ai_parlays_period_start", None)
        premium_period_start_str = (
            premium_period_start.isoformat()
            if getattr(premium_period_start, "isoformat", None)
            else None
        )

        return SubscriptionStatusResponse(
            tier=access.tier,
            plan_code=access.plan_code,
            can_use_custom_builder=access.can_use_custom_builder,
            can_use_upset_finder=access.can_use_upset_finder,
            can_use_multi_sport=access.can_use_multi_sport,
            can_save_parlays=access.can_save_parlays,
            max_ai_parlays_per_day=access.max_ai_parlays_per_day,
            remaining_ai_parlays_today=access.remaining_ai_parlays_today,
            unlimited_ai_parlays=access.max_ai_parlays_per_day == -1,
            credit_balance=credit_balance,
            is_lifetime=access.is_lifetime,
            subscription_end=subscription_end_str,
            balances=SubscriptionBalancesResponse(
                credit_balance=credit_balance,
                free_parlays_total=free_total,
                free_parlays_used=free_used,
                free_parlays_remaining=free_remaining,
                daily_ai_limit=access.max_ai_parlays_per_day,
                daily_ai_used=daily_used,
                daily_ai_remaining=access.remaining_ai_parlays_today,
                premium_ai_parlays_used=premium_used,
                premium_ai_period_start=premium_period_start_str,
            ),
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback

        error_detail = str(e)
        logger.error(f"Error fetching subscription status for user {user.id}: {error_detail}")
        logger.error(traceback.format_exc())

        # Return default free tier on error instead of 500
        return SubscriptionStatusResponse(
            tier="free",
            plan_code=None,
            can_use_custom_builder=False,
            can_use_upset_finder=False,
            can_use_multi_sport=False,
            can_save_parlays=False,
            max_ai_parlays_per_day=1,
            remaining_ai_parlays_today=1,
            unlimited_ai_parlays=False,
            credit_balance=0,
            is_lifetime=False,
            subscription_end=None,
            balances=SubscriptionBalancesResponse(
                credit_balance=0,
                free_parlays_total=0,
                free_parlays_used=0,
                free_parlays_remaining=0,
                daily_ai_limit=1,
                daily_ai_used=0,
                daily_ai_remaining=1,
                premium_ai_parlays_used=0,
                premium_ai_period_start=None,
            ),
        )


@router.get("/billing/plans", response_model=list[PlanResponse])
async def get_available_plans(
    db: AsyncSession = Depends(get_db),
):
    """
    Get all available subscription plans for the pricing page.

    Returns active plans ordered by display_order.
    """
    service = SubscriptionService(db)
    plans = await service.get_active_plans()
    return plans


@router.post("/billing/lemonsqueezy/checkout", response_model=CheckoutResponse)
async def create_lemonsqueezy_checkout(
    request: CheckoutRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a LemonSqueezy checkout session for card payments.

    Returns a hosted checkout URL that the frontend should redirect to.

    Process:
    1. Validate plan_code exists and is LemonSqueezy provider
    2. Create checkout via LemonSqueezy API
    3. Return checkout URL for redirect

    After payment, LemonSqueezy webhook will activate the subscription.
    """
    # Validate configuration
    if not settings.lemonsqueezy_api_key or not settings.lemonsqueezy_store_id:
        logger.error("LemonSqueezy not configured")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment system not configured. Please contact support.",
        )

    # Get plan
    result = await db.execute(
        select(SubscriptionPlan).where(
            and_(
                SubscriptionPlan.code == request.plan_code,
                SubscriptionPlan.provider == "lemonsqueezy",
                SubscriptionPlan.is_active == True,
            )
        )
    )
    plan = result.scalar_one_or_none()

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan not found: {request.plan_code}",
        )

    resolver = LemonSqueezySubscriptionVariantResolver(settings)
    variant_id = (plan.provider_product_id or "").strip() or resolver.get_variant_id(plan.code)
    if not variant_id:
        logger.error(f"Plan {plan.code} missing provider_product_id (and no env fallback variant configured)")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Plan configuration error. Please contact support.",
        )

    # Create LemonSqueezy checkout
    try:
        purchase_type = "lifetime_access" if getattr(plan, "is_lifetime", False) else None
        checkout_url = await _create_lemonsqueezy_checkout(
            user=user,
            plan=plan,
            variant_id=variant_id,
            purchase_type=purchase_type,
        )

        logger.info(f"Created LemonSqueezy checkout for user {user.id}, plan {plan.code}")

        return CheckoutResponse(
            checkout_url=checkout_url,
            provider="lemonsqueezy",
            plan_code=plan.code,
        )

    except Exception as e:
        logger.error(f"LemonSqueezy checkout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session. Please try again.",
        )


async def _create_lemonsqueezy_checkout(
    user: User,
    plan: SubscriptionPlan,
    variant_id: str,
    purchase_type: Optional[str] = None,
) -> str:
    """Create checkout session via LemonSqueezy API."""

    # LemonSqueezy API endpoint
    api_url = "https://api.lemonsqueezy.com/v1/checkouts"

    # Build checkout data
    # See: https://docs.lemonsqueezy.com/api/checkouts
    custom_data = {
        "user_id": str(user.id),
        "plan_code": plan.code,
    }
    if purchase_type:
        custom_data["purchase_type"] = purchase_type

    checkout_data = {
        "data": {
            "type": "checkouts",
            "attributes": {
                "checkout_data": {
                    "email": user.email,
                    "custom": custom_data,
                },
                "checkout_options": {
                    "embed": False,
                    "media": True,
                    "logo": True,
                },
                "product_options": {
                    "enabled_variants": [variant_id],
                    "redirect_url": f"{settings.app_url}/billing/success?provider=lemonsqueezy",
                },
            },
            "relationships": {
                "store": {
                    "data": {
                        "type": "stores",
                        "id": settings.lemonsqueezy_store_id,
                    }
                },
                "variant": {
                    "data": {
                        "type": "variants",
                        "id": variant_id,
                    }
                },
            },
        }
    }

    headers = {
        "Accept": "application/vnd.api+json",
        "Content-Type": "application/vnd.api+json",
        "Authorization": f"Bearer {settings.lemonsqueezy_api_key}",
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            api_url,
            json=checkout_data,
            headers=headers,
            timeout=30.0,
        )

        if response.status_code != 201:
            logger.error(f"LemonSqueezy API error: {response.status_code} - {response.text}")
            raise Exception(f"LemonSqueezy API error: {response.status_code}")

        data = response.json()
        checkout_url = data["data"]["attributes"]["url"]

        return checkout_url


@router.post("/billing/coinbase/checkout", response_model=CheckoutResponse)
async def create_coinbase_checkout(
    request: CheckoutRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a Coinbase Commerce checkout for crypto payments.

    Typically used for lifetime access purchases.
    Returns a hosted checkout URL that the frontend should redirect to.

    Process:
    1. Validate plan_code exists and is Coinbase provider
    2. Create charge via Coinbase Commerce API
    3. Return hosted URL for redirect

    After payment, Coinbase webhook will activate the subscription.
    """
    # Validate configuration
    if not settings.coinbase_commerce_api_key:
        logger.error("Coinbase Commerce not configured")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Crypto payment system not configured. Please contact support.",
        )

    # Get plan
    result = await db.execute(
        select(SubscriptionPlan).where(
            and_(
                SubscriptionPlan.code == request.plan_code,
                SubscriptionPlan.provider == "coinbase",
                SubscriptionPlan.is_active == True,
            )
        )
    )
    plan = result.scalar_one_or_none()

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan not found: {request.plan_code}",
        )

    # Create Coinbase Commerce charge
    try:
        checkout_url = await _create_coinbase_charge(
            user=user,
            plan=plan,
        )

        logger.info(f"Created Coinbase charge for user {user.id}, plan {plan.code}")

        return CheckoutResponse(
            checkout_url=checkout_url,
            provider="coinbase",
            plan_code=plan.code,
        )

    except Exception as e:
        logger.error(f"Coinbase Commerce error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create crypto checkout. Please try again.",
        )


async def _create_coinbase_charge(user: User, plan: SubscriptionPlan) -> str:
    """Create charge via Coinbase Commerce API."""

    # Coinbase Commerce API endpoint
    api_url = "https://api.commerce.coinbase.com/charges"

    # Build charge data
    # See: https://docs.cloud.coinbase.com/commerce/reference/createcharge
    charge_data = {
        "name": plan.name,
        "description": plan.description or f"Parlay Gorilla - {plan.name}",
        "pricing_type": "fixed_price",
        "local_price": {
            "amount": str(plan.price_dollars),
            "currency": plan.currency,
        },
        "metadata": {
            "user_id": str(user.id),
            "user_email": user.email,
            "plan_code": plan.code,
        },
        "redirect_url": f"{settings.app_url}/billing/success?provider=coinbase",
        "cancel_url": f"{settings.app_url}/pricing",
    }

    headers = {
        "Content-Type": "application/json",
        "X-CC-Api-Key": settings.coinbase_commerce_api_key,
        "X-CC-Version": "2018-03-22",
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            api_url,
            json=charge_data,
            headers=headers,
            timeout=30.0,
        )

        if response.status_code != 201:
            logger.error(f"Coinbase Commerce API error: {response.status_code} - {response.text}")
            raise Exception(f"Coinbase Commerce API error: {response.status_code}")

        data = response.json()
        checkout_url = data["data"]["hosted_url"]

        return checkout_url


