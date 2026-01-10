"""
Billing API routes for the hybrid model: access status, credit packs, and credit-pack checkout.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.core.config import settings
from app.core.dependencies import get_current_user, get_db
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/billing/access-status")
async def get_access_status(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get user's complete access status for the billing page.

    Returns information about:
    - Free parlays remaining
    - Subscription status and daily limits
    - Credit balance
    - Whether user can generate parlays
    """
    from app.services.access_control_service import AccessControlService

    service = AccessControlService(db)
    status_obj = await service.get_access_status(str(user.id))

    if not status_obj:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get access status",
        )

    return status_obj.to_dict()


@router.get("/billing/credit-packs")
async def get_credit_packs():
    """
    Get all available credit packs for purchase.

    Public endpoint - no auth required.
    """
    from app.core.billing_config import get_all_credit_packs

    return {
        "packs": get_all_credit_packs(),
    }


@router.get("/billing/subscription-plans")
async def get_subscription_plans(
    db: AsyncSession = Depends(get_db),
):
    """
    Get all available subscription plans from the database.

    Returns active subscription plans including monthly, annual, and lifetime plans.
    Public endpoint - no auth required.
    """
    from sqlalchemy import select, and_
    from app.models.subscription_plan import SubscriptionPlan, BillingCycle

    # Query all active subscription plans, excluding free plans and credit packs
    # Credit packs have billing_cycle = "one_time" or codes starting with "PG_CREDITS_"
    # Only return actual subscription plans: monthly, annual, or lifetime
    result = await db.execute(
        select(SubscriptionPlan).where(
            and_(
                SubscriptionPlan.is_active == True,
                SubscriptionPlan.price_cents > 0,  # Exclude free plans
                SubscriptionPlan.billing_cycle != BillingCycle.one_time.value,  # Exclude credit packs
                ~SubscriptionPlan.code.like("PG_CREDITS_%"),  # Exclude credit pack codes
                SubscriptionPlan.billing_cycle.in_([
                    BillingCycle.monthly.value,
                    BillingCycle.annual.value,
                    BillingCycle.lifetime.value,
                ]),  # Only actual subscription plans
            )
        ).order_by(
            SubscriptionPlan.display_order.asc(),
            SubscriptionPlan.is_featured.desc(),
            SubscriptionPlan.price_cents.asc()
        )
    )
    plans = result.scalars().all()

    # Transform plans to match frontend expected format
    transformed_plans = []
    for plan in plans:
        # Determine period from billing_cycle
        period = "monthly"
        if plan.billing_cycle == BillingCycle.annual.value:
            period = "yearly"
        elif plan.billing_cycle == BillingCycle.lifetime.value:
            period = "lifetime"

        # Build features list from plan features
        features = []
        if plan.has_unlimited_parlays:
            features.append("Unlimited AI parlays")
        elif plan.max_ai_parlays_per_day > 0:
            features.append(f"{plan.max_ai_parlays_per_day} AI parlays per day")
        
        if plan.can_use_custom_builder:
            features.append("Custom parlay builder")
        if plan.can_use_upset_finder:
            features.append("Gorilla Upset Finder")
        if plan.can_use_multi_sport:
            features.append("Multi-sport parlays")
        if plan.can_save_parlays:
            features.append("Save parlays")
        if plan.ad_free:
            features.append("Ad-free experience")
        
        # If no features, add a default
        if not features:
            features.append("Premium access")

        transformed_plans.append({
            "id": plan.code,  # Use code as ID for checkout
            "name": plan.name,
            "description": plan.description or "",
            "price": float(plan.price_dollars),
            "period": period,
            "daily_parlay_limit": plan.max_ai_parlays_per_day if plan.max_ai_parlays_per_day > 0 else -1,
            "features": features,
            "is_featured": plan.is_featured,
            "billing_cycle": plan.billing_cycle,  # Include for reference
            "is_lifetime": plan.is_lifetime,
        })

    return {
        "plans": transformed_plans,
    }


class CreditPackCheckoutRequest(BaseModel):
    credit_pack_id: str
    provider: str = "stripe"
    provider: str = "stripe"


class CreditPackCheckoutResponse(BaseModel):
    checkout_url: str
    provider: str
    credit_pack_id: str
    amount: float
    credits: int


@router.post("/billing/credits/checkout", response_model=CreditPackCheckoutResponse)
async def create_credit_pack_checkout(
    request: CreditPackCheckoutRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a checkout session for purchasing a credit pack.

    Returns a hosted checkout URL for the payment provider.
    """
    from app.core.billing_config import get_credit_pack

    # Get credit pack
    credit_pack = get_credit_pack(request.credit_pack_id)
    if not credit_pack:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Credit pack not found: {request.credit_pack_id}",
        )

    # Validate provider configuration
    if request.provider == "stripe":
        if not settings.stripe_secret_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Payment system not configured.",
            )

        from app.services.stripe_service import StripeService

        stripe_service = StripeService(db)
        
        # Get Stripe price ID from subscription_plans table
        # Credit packs should be configured as one-time payment plans in Stripe
        from app.models.subscription_plan import SubscriptionPlan
        from sqlalchemy import and_, select
        
        result = await db.execute(
            select(SubscriptionPlan).where(
                and_(
                    SubscriptionPlan.code == f"PG_{credit_pack.id.upper()}",
                    SubscriptionPlan.provider == "stripe",
                    SubscriptionPlan.is_active == True,
                )
            )
        )
        plan = result.scalar_one_or_none()
        
        # Get price ID from plan, env vars, or try to construct from credit pack config
        price_id = None
        if plan:
            price_id = plan.provider_product_id or plan.provider_price_id
        
        # Fallback to env vars if not in database
        if not price_id:
            credit_pack_id_upper = credit_pack.id.upper()
            if credit_pack_id_upper == "CREDITS_10":
                price_id = settings.stripe_price_id_credits_10
            elif credit_pack_id_upper == "CREDITS_25":
                price_id = settings.stripe_price_id_credits_25
            elif credit_pack_id_upper == "CREDITS_50":
                price_id = settings.stripe_price_id_credits_50
            elif credit_pack_id_upper == "CREDITS_100":
                price_id = settings.stripe_price_id_credits_100
        
        # If still no price ID, fail
        if not price_id:
            logger.warning(
                f"No Stripe price ID found for credit pack '{credit_pack.id}'. "
                "Please ensure the pack is configured in subscription_plans table or env vars."
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    f"Credit pack Stripe price ID not configured for pack '{credit_pack.id}'. "
                    "Please contact support."
                ),
            )

        checkout_url = await stripe_service.create_one_time_checkout_session(
            user=user,
            price_id=price_id,
            quantity=1,
            metadata={
                "user_id": str(user.id),
                "purchase_type": "credit_pack",
                "credit_pack_id": credit_pack.id,
            },
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid provider: {request.provider}. Only 'stripe' is supported.",
        )

    logger.info(f"Created credit pack checkout for user {user.id}, pack: {request.credit_pack_id}")

    return CreditPackCheckoutResponse(
        checkout_url=checkout_url,
        provider=request.provider,
        credit_pack_id=request.credit_pack_id,
        amount=float(credit_pack.price),
        credits=credit_pack.total_credits,
    )


# Coinbase Commerce disabled for LemonSqueezy compliance
# async def _create_credit_pack_coinbase_checkout(user: User, credit_pack) -> str:
#     """Create Coinbase Commerce checkout for credit pack."""
#     import httpx
#
#     api_url = "https://api.commerce.coinbase.com/charges"
#     before_balance = int(getattr(user, "credit_balance", 0) or 0)
#     expected_credits = int(getattr(credit_pack, "total_credits", 0) or 0)
#     redirect_url = (
#         f"{settings.app_url}/billing/success"
#         f"?provider=coinbase&type=credits&pack={credit_pack.id}"
#         f"&before={before_balance}&expected={expected_credits}"
#     )
#
#     charge_data = {
#         "name": credit_pack.name,
#         "description": f"{credit_pack.total_credits} credits for Parlay Gorilla",
#         "pricing_type": "fixed_price",
#         "local_price": {
#             "amount": str(credit_pack.price),
#             "currency": "USD",
#         },
#         "metadata": {
#             "user_id": str(user.id),
#             "user_email": user.email,
#             "credit_pack_id": credit_pack.id,
#             "purchase_type": "credit_pack",
#         },
#         "redirect_url": redirect_url,
#         "cancel_url": f"{settings.app_url}/billing",
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
#             logger.error(f"Coinbase credit pack checkout error: {response.status_code} - {response.text}")
#             raise Exception(f"Coinbase Commerce API error: {response.status_code}")
#
#         data = response.json()
#         return data["data"]["hosted_url"]


