"""
Subscription API routes for subscription management.

Endpoints:
- GET /api/subscription/me - Get current subscription state
- GET /api/subscription/history - Get billing/payment history
- POST /api/subscription/cancel - Request subscription cancellation
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
import logging

from app.core.dependencies import get_db, get_current_user
from app.core.config import settings
from app.models.user import SubscriptionStatusEnum, User
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.subscription_plan import SubscriptionPlan
from app.models.payment import Payment
from app.services.stripe_service import StripeService
from app.services.subscription_service import SubscriptionService
from app.services.lemonsqueezy_subscription_client import LemonSqueezySubscriptionClient
from app.utils.datetime_utils import coerce_utc, now_utc

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# Response Schemas
# ============================================================================

class SubscriptionMeResponse(BaseModel):
    """Current subscription state response."""
    has_subscription: bool
    plan_id: Optional[str] = None
    plan_name: Optional[str] = None
    status: str  # "active", "trialing", "canceled", "expired", "free"
    current_period_end: Optional[str] = None
    cancel_at_period_end: bool = False
    provider: Optional[str] = None
    is_lifetime: bool = False
    is_on_trial: bool = False


class PaymentHistoryItem(BaseModel):
    """Single payment history entry."""
    id: str
    amount: float
    currency: str
    plan: str
    status: str
    provider: str
    created_at: str
    paid_at: Optional[str] = None


class PaymentHistoryResponse(BaseModel):
    """Payment history response."""
    payments: List[PaymentHistoryItem]
    total_count: int


class CancelSubscriptionResponse(BaseModel):
    """Subscription cancellation response."""
    message: str
    cancel_at_period_end: bool
    current_period_end: Optional[str] = None


# ============================================================================
# Subscription Endpoints
# ============================================================================

@router.get("/subscription/me", response_model=SubscriptionMeResponse)
async def get_my_subscription(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get current user's subscription state.
    
    Returns subscription info if active, or free tier status if not.
    
    Reads from DB (populated by webhooks), NOT live API calls.
    """
    try:
        # Single source of truth: use SubscriptionService so this endpoint stays consistent with
        # /api/billing/status (used by the avatar dropdown + paywall checks).
        subscription = await SubscriptionService(db).get_user_active_subscription(str(user.id))
    except Exception as e:
        logger.error("Error fetching subscription for user %s: %s", user.id, str(e), exc_info=True)
        subscription = None

    if not subscription:
        return SubscriptionMeResponse(
            has_subscription=False,
            plan_id=None,
            plan_name="Free",
            status="free",
            current_period_end=None,
            cancel_at_period_end=False,
            provider=None,
            is_lifetime=False,
            is_on_trial=False,
        )

    # Plan name (best-effort)
    try:
        plan_name = await _get_plan_name(db, subscription.plan)
    except Exception:
        plan_name = (subscription.plan or "Premium").replace("_", " ").title()

    raw_status = str(getattr(subscription, "status", "") or "").strip().lower()

    try:
        is_lifetime = bool(getattr(subscription, "is_lifetime", False) or False)
    except Exception:
        is_lifetime = False

    # Normalize for frontend expectations:
    # - lifetime => always "active"
    # - "cancelled" => "canceled" (single-L spelling used in the UI)
    if is_lifetime:
        status_value = "active"
    elif raw_status == SubscriptionStatus.cancelled.value:
        status_value = "canceled"
    else:
        status_value = raw_status or "active"

    return SubscriptionMeResponse(
        has_subscription=True,
        plan_id=subscription.plan,
        plan_name=plan_name,
        status=status_value,
        current_period_end=subscription.current_period_end.isoformat() if subscription.current_period_end else None,
        cancel_at_period_end=bool(getattr(subscription, "cancel_at_period_end", False) or False),
        provider=getattr(subscription, "provider", None),
        is_lifetime=is_lifetime,
        is_on_trial=raw_status == SubscriptionStatus.trialing.value,
    )


@router.get("/subscription/history", response_model=PaymentHistoryResponse)
async def get_subscription_history(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 20,
    offset: int = 0,
):
    """
    Get user's payment/billing history.
    
    Returns list of past payments with status, amount, and dates.
    """
    # Get total count
    from sqlalchemy import func
    count_result = await db.execute(
        select(func.count(Payment.id)).where(Payment.user_id == user.id)
    )
    total_count = count_result.scalar() or 0
    
    # Get payments
    result = await db.execute(
        select(Payment)
        .where(Payment.user_id == user.id)
        .order_by(Payment.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    payments = result.scalars().all()
    
    payment_items = [
        PaymentHistoryItem(
            id=str(payment.id),
            amount=float(payment.amount),
            currency=payment.currency,
            plan=payment.plan,
            status=payment.status,
            provider=payment.provider,
            created_at=payment.created_at.isoformat() if payment.created_at else "",
            paid_at=payment.paid_at.isoformat() if payment.paid_at else None,
        )
        for payment in payments
    ]
    
    return PaymentHistoryResponse(
        payments=payment_items,
        total_count=total_count,
    )


@router.post("/subscription/cancel", response_model=CancelSubscriptionResponse)
async def cancel_subscription(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Request subscription cancellation.
    
    Sets cancel_at_period_end = True.
    User keeps access until current period ends.
    
    For Stripe, this cancels at the payment provider (stops future renewals),
    then updates our DB. The user keeps access until current_period_end.
    """
    # Find active subscription
    result = await db.execute(
        select(Subscription).where(
            and_(
                Subscription.user_id == user.id,
                Subscription.status.in_([
                    SubscriptionStatus.active.value,
                    SubscriptionStatus.trialing.value,
                ])
            )
        ).order_by(Subscription.created_at.desc())
    )
    subscription = result.scalar_one_or_none()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found"
        )
    
    if subscription.is_lifetime:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lifetime subscriptions cannot be canceled"
        )
    
    if subscription.cancel_at_period_end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subscription is already scheduled for cancellation"
        )
    
    if subscription.provider == "coinbase":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Crypto subscriptions do not auto-renew, so cancellation is not required.",
        )
    
    if subscription.provider not in {"stripe", "lemonsqueezy"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Provider does not support cancellation via API: {subscription.provider}",
        )

    if not subscription.provider_subscription_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Subscription is missing provider subscription ID. Please contact support.",
        )

    provider_payload = None
    try:
        if subscription.provider == "stripe":
            if not settings.stripe_secret_key:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Payment system not configured. Please contact support.",
                )
            provider_payload = await StripeService(db).cancel_subscription(subscription.provider_subscription_id)
        else:
            if not settings.lemonsqueezy_api_key:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Payment system not configured. Please contact support.",
                )
            provider_payload = await LemonSqueezySubscriptionClient(api_key=settings.lemonsqueezy_api_key).cancel_subscription(
                subscription.provider_subscription_id
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Provider cancellation failed for user=%s subscription=%s provider_subscription_id=%s provider=%s error=%s",
            user.id,
            subscription.id,
            subscription.provider_subscription_id,
            subscription.provider,
            str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to cancel subscription with payment provider. Please try again or contact support.",
        )

    # Update period end from provider response
    provider_status_value = ""
    if isinstance(provider_payload, dict):
        if subscription.provider == "stripe":
            current_period_end = provider_payload.get("current_period_end")
            if current_period_end:
                try:
                    subscription.current_period_end = datetime.fromtimestamp(current_period_end, tz=timezone.utc)
                except Exception:
                    pass
            provider_status_value = str(provider_payload.get("status") or "").strip().lower()
        else:
            attrs = (provider_payload.get("data") or {}).get("attributes") if isinstance(provider_payload.get("data"), dict) else {}
            if isinstance(attrs, dict):
                ends_at = attrs.get("ends_at")
                if ends_at:
                    try:
                        subscription.current_period_end = coerce_utc(datetime.fromisoformat(str(ends_at).replace("Z", "+00:00")))
                    except Exception:
                        pass
                provider_status_value = str(attrs.get("status") or "").strip().lower()

        # Store provider metadata for audit/debug
        try:
            subscription.provider_metadata = provider_payload
        except Exception:
            pass

    # Update our subscription record.
    subscription.cancel_at_period_end = True
    subscription.cancelled_at = datetime.now(timezone.utc)

    # Prefer the provider status if present.
    if provider_status_value:
        status_map = {
            "active": SubscriptionStatus.active.value,
            "past_due": SubscriptionStatus.past_due.value,
            "cancelled": SubscriptionStatus.cancelled.value,
            "expired": SubscriptionStatus.expired.value,
            "on_trial": SubscriptionStatus.trialing.value,
            "paused": SubscriptionStatus.paused.value,
        }
        subscription.status = status_map.get(provider_status_value, subscription.status)

    # Keep user access until renewal date; mark user as canceled for billing UI.
    try:
        user.subscription_status = SubscriptionStatusEnum.canceled.value
        if subscription.current_period_end:
            user.subscription_renewal_date = subscription.current_period_end
    except Exception:
        pass

    await db.commit()

    logger.info(
        "Subscription %s cancelled at provider and marked for period-end cancellation for user %s",
        subscription.id,
        user.id,
    )
    
    return CancelSubscriptionResponse(
        message="Subscription will be canceled at the end of the current billing period",
        cancel_at_period_end=True,
        current_period_end=subscription.current_period_end.isoformat() if subscription.current_period_end else None,
    )


# ============================================================================
# Helper Functions
# ============================================================================

async def _get_plan_name(db: AsyncSession, plan_code: str) -> str:
    """Get plan display name from plan code."""
    result = await db.execute(
        select(SubscriptionPlan.name).where(SubscriptionPlan.code == plan_code)
    )
    plan_name = result.scalar_one_or_none()
    return plan_name or plan_code.replace("_", " ").title()

