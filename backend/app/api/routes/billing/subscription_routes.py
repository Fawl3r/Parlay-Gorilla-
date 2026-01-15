"""
Billing API routes for subscription checkout sessions.

Handles checkout creation for:
- Stripe (card payments, recurring subscriptions and one-time payments)
- LemonSqueezy (card payments, recurring subscriptions) - DEPRECATED
- Coinbase Commerce (crypto payments, lifetime access) - DEPRECATED
"""

from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import httpx
import logging

from app.core.config import settings
from app.core.dependencies import get_current_user, get_db, require_email_verified
from app.models.subscription_plan import SubscriptionPlan
from app.models.user import User
from app.services.subscription_service import SubscriptionService
from app.services.stripe_service import StripeService
from app.api.routes.billing.subscription_schemas import (
    AiParlaysBalance,
    CheckoutRequest,
    CheckoutResponse,
    CustomAiParlaysBalance,
    PlanResponse,
    SubscriptionBalancesResponse,
    SubscriptionStatusResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()




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

        # Rolling-period snapshots (premium-only); safe defaults for free users.
        from app.services.premium_usage_service import PremiumUsageService

        usage_service = PremiumUsageService(db)

        premium_used = int(getattr(user, "premium_ai_parlays_used", 0) or 0)
        premium_period_start_str = None
        custom_used = int(getattr(user, "premium_custom_builder_used", 0) or 0)
        custom_period_start_str = None
        custom_remaining = 0
        custom_limit = int(getattr(settings, "premium_custom_builder_per_month", 0) or 0)
        ins_used = int(getattr(user, "premium_inscriptions_used", 0) or 0)
        ins_period_start_str = None
        ins_remaining = 0
        ins_limit = int(getattr(settings, "premium_inscriptions_per_month", 0) or 0)

        if access.tier == "premium":
            ai_snap = await usage_service.get_premium_ai_snapshot(user)
            premium_used = ai_snap.used
            premium_period_start_str = ai_snap.period_start.isoformat() if ai_snap.period_start else None

            custom_snap = await usage_service.get_custom_builder_snapshot(user)
            custom_used = custom_snap.used
            custom_limit = custom_snap.limit
            custom_remaining = custom_snap.remaining
            custom_period_start_str = custom_snap.period_start.isoformat() if custom_snap.period_start else None

            ins_snap = await usage_service.get_inscriptions_snapshot(user)
            ins_used = ins_snap.used
            ins_limit = ins_snap.limit
            ins_remaining = ins_snap.remaining
            ins_period_start_str = ins_snap.period_start.isoformat() if ins_snap.period_start else None

        ai_limit = int(getattr(access, "max_ai_parlays_per_day", 0) or 0)
        ai_remaining = int(getattr(access, "remaining_ai_parlays_today", 0) or 0)
        ai_used = int(premium_used or 0) if access.tier == "premium" else (max(0, ai_limit - ai_remaining) if ai_limit >= 0 else 0)

        ai_balance = AiParlaysBalance(
            monthly_limit=ai_limit,
            used=ai_used,
            remaining=max(0, ai_remaining),
        )

        # For free users, get custom AI parlays from weekly limits
        if access.tier == "free":
            custom_limit_free = int(getattr(access, "max_custom_parlays_per_day", 0) or 0)
            custom_remaining_free = int(getattr(access, "remaining_custom_parlays_today", 0) or 0)
            custom_used_free = max(0, custom_limit_free - custom_remaining_free) if custom_limit_free >= 0 else 0
            custom_ai_balance = CustomAiParlaysBalance(
                monthly_limit=custom_limit_free,
                used=custom_used_free,
                remaining=max(0, custom_remaining_free),
                inscription_cost_usd=float(getattr(settings, "inscription_cost_usd", 0.37) or 0.37),
                requires_manual_opt_in=True,
            )
        else:
            custom_ai_balance = CustomAiParlaysBalance(
                monthly_limit=int(custom_limit or 0),
                used=int(custom_used or 0),
                remaining=int(custom_remaining or 0),
                inscription_cost_usd=float(getattr(settings, "inscription_cost_usd", 0.37) or 0.37),
                requires_manual_opt_in=True,
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
                premium_custom_builder_used=custom_used,
                premium_custom_builder_limit=custom_limit,
                premium_custom_builder_remaining=custom_remaining,
                premium_custom_builder_period_start=custom_period_start_str,
                premium_inscriptions_used=ins_used,
                premium_inscriptions_limit=ins_limit,
                premium_inscriptions_remaining=ins_remaining,
                premium_inscriptions_period_start=ins_period_start_str,
                ai_parlays=ai_balance,
                custom_ai_parlays=custom_ai_balance,
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
                premium_custom_builder_used=0,
                premium_custom_builder_limit=0,
                premium_custom_builder_remaining=0,
                premium_custom_builder_period_start=None,
                premium_inscriptions_used=0,
                premium_inscriptions_limit=0,
                premium_inscriptions_remaining=0,
                premium_inscriptions_period_start=None,
                ai_parlays=AiParlaysBalance(monthly_limit=1, used=0, remaining=1),
                custom_ai_parlays=CustomAiParlaysBalance(
                    monthly_limit=0,
                    used=0,
                    remaining=0,
                    inscription_cost_usd=float(getattr(settings, "inscription_cost_usd", 0.37) or 0.37),
                    requires_manual_opt_in=True,
                ),
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


@router.post("/billing/stripe/checkout", response_model=CheckoutResponse)
async def create_stripe_checkout(
    request: CheckoutRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a Stripe checkout session for subscription.

    Returns a hosted checkout URL that the frontend should redirect to.

    Process:
    1. Validate plan_code exists and is Stripe provider
    2. Create checkout via Stripe API
    3. Return checkout URL for redirect

    After payment, Stripe webhook will activate the subscription.
    """
    # Validate configuration
    if not settings.stripe_secret_key:
        logger.error("Stripe not configured")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment system not configured. Please contact support.",
        )

    # Get plan
    result = await db.execute(
        select(SubscriptionPlan).where(
            and_(
                SubscriptionPlan.code == request.plan_code,
                SubscriptionPlan.provider == "stripe",
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

    # Require email verification before allowing purchase
    require_email_verified(user)

    # Create Stripe checkout
    try:
        stripe_service = StripeService(db)
        checkout_url = await stripe_service.create_checkout_session(
            user=user,
            plan=plan,
        )

        logger.info(f"Created Stripe checkout for user {user.id}, plan {plan.code}")

        return CheckoutResponse(
            checkout_url=checkout_url,
            provider="stripe",
            plan_code=plan.code,
        )

    except Exception as e:
        logger.error(f"Stripe checkout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session. Please try again.",
        )


@router.post("/billing/stripe/portal", response_model=CheckoutResponse)
async def create_stripe_portal(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a Stripe Customer Portal session.

    Returns a portal URL where the user can manage their subscription,
    update payment methods, view invoices, and cancel.

    Requires the user to have an active Stripe customer ID.
    """
    # Validate configuration
    if not settings.stripe_secret_key:
        logger.error("Stripe not configured")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment system not configured. Please contact support.",
        )

    if not user.stripe_customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active subscription found. Please create a subscription first.",
        )

    try:
        stripe_service = StripeService(db)
        portal_url = await stripe_service.create_portal_session(user=user)

        logger.info(f"Created Stripe portal session for user {user.id}")

        return CheckoutResponse(
            checkout_url=portal_url,
            provider="stripe",
            plan_code="portal",
        )

    except Exception as e:
        logger.error(f"Stripe portal error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create portal session. Please try again.",
        )


# ============================================================================
# COINBASE COMMERCE ROUTES - DISABLED FOR LEMONSQUEEZY COMPLIANCE
# ============================================================================
# Crypto payments have been disabled to ensure LemonSqueezy approval.
# Code kept for reference only. Do not re-enable without compliance review.
# ============================================================================

# @router.post("/billing/coinbase/checkout", response_model=CheckoutResponse)
# async def create_coinbase_checkout(
#     request: CheckoutRequest,
#     user: User = Depends(get_current_user),
#     db: AsyncSession = Depends(get_db),
# ):
#     """
#     Create a Coinbase Commerce checkout for crypto payments.
#
#     Typically used for lifetime access purchases.
#     Returns a hosted checkout URL that the frontend should redirect to.
#
#     Process:
#     1. Validate plan_code exists and is Coinbase provider
#     2. Create charge via Coinbase Commerce API
#     3. Return hosted URL for redirect
#
#     After payment, Coinbase webhook will activate the subscription.
#     """
#     # Validate configuration
#     if not settings.coinbase_commerce_api_key:
#         logger.error("Coinbase Commerce not configured")
#         raise HTTPException(
#             status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
#             detail="Crypto payment system not configured. Please contact support.",
#         )
#
#     # Get plan
#     result = await db.execute(
#         select(SubscriptionPlan).where(
#             and_(
#                 SubscriptionPlan.code == request.plan_code,
#                 SubscriptionPlan.provider == "coinbase",
#                 SubscriptionPlan.is_active == True,
#             )
#         )
#     )
#     plan = result.scalar_one_or_none()
#
#     if not plan:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"Plan not found: {request.plan_code}",
#         )
#
#     # Create Coinbase Commerce charge
#     try:
#         checkout_url = await _create_coinbase_charge(
#             user=user,
#             plan=plan,
#         )
#
#         logger.info(f"Created Coinbase charge for user {user.id}, plan {plan.code}")
#
#         return CheckoutResponse(
#             checkout_url=checkout_url,
#             provider="coinbase",
#             plan_code=plan.code,
#         )
#
#     except Exception as e:
#         logger.error(f"Coinbase Commerce error: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Failed to create crypto checkout. Please try again.",
#         )


# async def _create_coinbase_charge(user: User, plan: SubscriptionPlan) -> str:
#     """Create charge via Coinbase Commerce API."""
#
#     # Coinbase Commerce API endpoint
#     api_url = "https://api.commerce.coinbase.com/charges"
#
#     # Build charge data
#     # See: https://docs.cloud.coinbase.com/commerce/reference/createcharge
#     charge_data = {
#         "name": plan.name,
#         "description": plan.description or f"Parlay Gorilla - {plan.name}",
#         "pricing_type": "fixed_price",
#         "local_price": {
#             "amount": str(plan.price_dollars),
#             "currency": plan.currency,
#         },
#         "metadata": {
#             "user_id": str(user.id),
#             "user_email": user.email,
#             "plan_code": plan.code,
#         },
#         "redirect_url": f"{settings.app_url}/billing/success?provider=coinbase",
#         "cancel_url": f"{settings.app_url}/pricing",
#     }
#
#     headers = {
#         "Content-Type": "application/json",
#         "X-CC-Api-Key": settings.coinbase_commerce_api_key,
#         "X-CC-Version": "2018-03-22",
#     }
#
#     async with httpx.AsyncClient() as client:
#         response = await client.post(
#             api_url,
#             json=charge_data,
#             headers=headers,
#             timeout=30.0,
#         )
#
#         if response.status_code != 201:
#             logger.error(f"Coinbase Commerce API error: {response.status_code} - {response.text}")
#             raise Exception(f"Coinbase Commerce API error: {response.status_code}")
#
#         data = response.json()
#         checkout_url = data["data"]["hosted_url"]
#
#         return checkout_url


