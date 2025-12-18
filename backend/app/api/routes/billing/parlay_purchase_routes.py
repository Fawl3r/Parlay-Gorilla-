"""
Billing API routes for pay-per-use one-time parlay purchases.

These are separate from credit packs:
- Parlay purchase: buy a single parlay (valid for 24h) once daily limits are hit.
- Credit packs: buy credits and spend them per-generation.
"""

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

logger = logging.getLogger(__name__)
router = APIRouter()


class ParlayPurchaseCheckoutRequest(BaseModel):
    parlay_type: str  # "single" or "multi"
    provider: str = "lemonsqueezy"  # "lemonsqueezy" or "coinbase"


class ParlayPurchaseCheckoutResponse(BaseModel):
    checkout_url: str
    provider: str
    parlay_type: str
    purchase_id: str
    amount: float
    currency: str


@router.post("/billing/parlay-purchase/checkout", response_model=ParlayPurchaseCheckoutResponse)
async def create_parlay_purchase_checkout(
    request: ParlayPurchaseCheckoutRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a checkout session for one-time parlay purchase.

    This is for free users who have used their daily free parlays
    and want to purchase additional parlays:
    - $3 for single-sport parlay
    - $5 for multi-sport parlay

    Process:
    1. Validate parlay_type (single/multi)
    2. Create ParlayPurchase record in pending state
    3. Create checkout session with provider
    4. Return checkout URL

    After payment, webhook will mark purchase as available.
    """
    from app.services.parlay_purchase_service import ParlayPurchaseService
    from app.models.parlay_purchase import ParlayType

    # Validate parlay_type
    if request.parlay_type not in [ParlayType.single.value, ParlayType.multi.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid parlay_type: {request.parlay_type}. Must be 'single' or 'multi'.",
        )

    # Get the appropriate plan
    if request.parlay_type == ParlayType.single.value:
        plan_code = "PG_SINGLE_PARLAY_ONETIME"
        amount = settings.single_parlay_price_dollars
    else:
        plan_code = "PG_MULTI_PARLAY_ONETIME"
        amount = settings.multi_parlay_price_dollars

    # Validate provider configuration
    if request.provider == "lemonsqueezy":
        if not settings.lemonsqueezy_api_key or not settings.lemonsqueezy_store_id:
            logger.error("LemonSqueezy not configured for parlay purchase")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Payment system not configured. Please contact support.",
            )
    elif request.provider == "coinbase":
        if not settings.coinbase_commerce_api_key:
            logger.error("Coinbase Commerce not configured for parlay purchase")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Crypto payment system not configured. Please contact support.",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid provider: {request.provider}. Must be 'lemonsqueezy' or 'coinbase'.",
        )

    # Get the plan (for provider product IDs if configured)
    result = await db.execute(
        select(SubscriptionPlan).where(
            and_(
                SubscriptionPlan.code == plan_code,
                SubscriptionPlan.is_active == True,
            )
        )
    )
    plan = result.scalar_one_or_none()

    # Create purchase record
    purchase_service = ParlayPurchaseService(db)

    try:
        # Create checkout session based on provider
        if request.provider == "lemonsqueezy":
            checkout_url = await _create_parlay_purchase_lemonsqueezy_checkout(
                user=user,
                parlay_type=request.parlay_type,
                amount=amount,
                plan=plan,
            )
        else:  # coinbase
            checkout_url = await _create_parlay_purchase_coinbase_checkout(
                user=user,
                parlay_type=request.parlay_type,
                amount=amount,
            )

        # Extract checkout ID from URL or generate one
        # For LemonSqueezy, the checkout ID is in the URL
        # For Coinbase, we'll use the charge ID from the webhook
        checkout_id = checkout_url.split("/")[-1] if checkout_url else None

        # Create the purchase record
        purchase = await purchase_service.create_parlay_purchase(
            user_id=str(user.id),
            parlay_type=request.parlay_type,
            provider=request.provider,
            provider_checkout_id=checkout_id,
        )

        logger.info(
            f"Created parlay purchase checkout for user {user.id}, "
            f"type={request.parlay_type}, provider={request.provider}"
        )

        return ParlayPurchaseCheckoutResponse(
            checkout_url=checkout_url,
            provider=request.provider,
            parlay_type=request.parlay_type,
            purchase_id=str(purchase.id),
            amount=float(amount),
            currency="USD",
        )

    except Exception as e:
        logger.error(f"Parlay purchase checkout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session. Please try again.",
        )


async def _create_parlay_purchase_lemonsqueezy_checkout(
    user: User,
    parlay_type: str,
    amount: float,
    plan: Optional[SubscriptionPlan] = None,
) -> str:
    """Create a LemonSqueezy checkout for one-time parlay purchase."""

    api_url = "https://api.lemonsqueezy.com/v1/checkouts"

    # Build product name
    product_name = "Single-Sport Parlay" if parlay_type == "single" else "Multi-Sport Parlay"

    # If we have a configured product ID, use it; otherwise create a custom checkout
    checkout_data = {
        "data": {
            "type": "checkouts",
            "attributes": {
                "checkout_data": {
                    "email": user.email,
                    "custom": {
                        "user_id": str(user.id),
                        "parlay_type": parlay_type,
                        "purchase_type": "parlay_one_time",
                    },
                },
                "checkout_options": {
                    "embed": False,
                    "media": True,
                    "logo": True,
                },
                "product_options": {
                    "name": product_name,
                    "description": f"One-time {product_name.lower()} purchase for Parlay Gorilla",
                    "redirect_url": f"{settings.app_url}/billing/success?provider=lemonsqueezy&type=parlay_purchase&parlay_type={parlay_type}",
                },
            },
            "relationships": {
                "store": {
                    "data": {
                        "type": "stores",
                        "id": settings.lemonsqueezy_store_id,
                    }
                }
            },
        }
    }

    # If we have a provider product ID, use the variant relationship
    if plan and plan.provider_product_id:
        checkout_data["data"]["relationships"]["variant"] = {
            "data": {
                "type": "variants",
                "id": plan.provider_product_id,
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
            logger.error(
                f"LemonSqueezy API error for parlay purchase: {response.status_code} - {response.text}"
            )
            raise Exception(f"LemonSqueezy API error: {response.status_code}")

        data = response.json()
        checkout_url = data["data"]["attributes"]["url"]

        return checkout_url


async def _create_parlay_purchase_coinbase_checkout(
    user: User,
    parlay_type: str,
    amount: float,
) -> str:
    """Create a Coinbase Commerce charge for one-time parlay purchase."""

    api_url = "https://api.commerce.coinbase.com/charges"

    product_name = "Single-Sport Parlay" if parlay_type == "single" else "Multi-Sport Parlay"

    charge_data = {
        "name": product_name,
        "description": f"One-time {product_name.lower()} purchase for Parlay Gorilla",
        "pricing_type": "fixed_price",
        "local_price": {
            "amount": str(amount),
            "currency": "USD",
        },
        "metadata": {
            "user_id": str(user.id),
            "user_email": user.email,
            "parlay_type": parlay_type,
            "purchase_type": "parlay_one_time",
        },
        "redirect_url": f"{settings.app_url}/billing/success?provider=coinbase&type=parlay_purchase&parlay_type={parlay_type}",
        "cancel_url": f"{settings.app_url}/app",
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
            logger.error(
                f"Coinbase Commerce API error for parlay purchase: {response.status_code} - {response.text}"
            )
            raise Exception(f"Coinbase Commerce API error: {response.status_code}")

        data = response.json()
        checkout_url = data["data"]["hosted_url"]

        return checkout_url


@router.get("/billing/parlay-purchases")
async def get_user_parlay_purchases(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get user's parlay purchase history and stats.

    Returns available purchases and purchase statistics.
    """
    from app.services.parlay_purchase_service import ParlayPurchaseService

    service = ParlayPurchaseService(db)

    purchases = await service.get_user_purchases(str(user.id), limit=20)
    stats = await service.get_purchase_stats(str(user.id))

    return {
        "purchases": [p.to_dict() for p in purchases],
        "stats": stats,
    }


@router.get("/billing/parlay-purchase/available")
async def check_available_parlay_purchase(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Check if user has any available (unused) parlay purchases.

    Returns available purchases by type.
    """
    from app.services.parlay_purchase_service import ParlayPurchaseService
    from app.models.parlay_purchase import ParlayType

    service = ParlayPurchaseService(db)

    single_purchase = await service.get_unused_purchase(str(user.id), ParlayType.single.value)
    multi_purchase = await service.get_unused_purchase(str(user.id), ParlayType.multi.value)

    return {
        "has_single": single_purchase is not None,
        "has_multi": multi_purchase is not None,
        "single_purchase": single_purchase.to_dict() if single_purchase else None,
        "multi_purchase": multi_purchase.to_dict() if multi_purchase else None,
    }


