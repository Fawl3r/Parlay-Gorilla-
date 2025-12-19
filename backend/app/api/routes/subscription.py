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
from app.services.lemonsqueezy_subscription_client import (
    LemonSqueezyApiError,
    LemonSqueezySubscriptionClient,
)
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
        # Find active subscription
        result = await db.execute(
            select(Subscription).where(
                and_(
                    Subscription.user_id == user.id,
                    Subscription.status.in_([
                        SubscriptionStatus.active.value,
                        SubscriptionStatus.trialing.value,
                        SubscriptionStatus.past_due.value,
                    ])
                )
            ).order_by(Subscription.created_at.desc())
        )
        subscription = result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Error fetching subscription for user {user.id}: {str(e)}", exc_info=True)
        # Return free tier on error
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
    
    if not subscription:
        try:
            # Check if there's a canceled subscription still in period
            result = await db.execute(
                select(Subscription).where(
                    and_(
                        Subscription.user_id == user.id,
                        Subscription.status == SubscriptionStatus.cancelled.value,
                        Subscription.cancel_at_period_end == True,
                    )
                ).order_by(Subscription.created_at.desc())
            )
            canceled_sub = result.scalar_one_or_none()
            
            if canceled_sub and canceled_sub.current_period_end:
                # Check if still within period
                if canceled_sub.current_period_end and coerce_utc(canceled_sub.current_period_end) > now_utc():
                    # Still has access until period end
                    plan_name = await _get_plan_name(db, canceled_sub.plan)
                    return SubscriptionMeResponse(
                        has_subscription=True,
                        plan_id=canceled_sub.plan,
                        plan_name=plan_name,
                        status="canceled",
                        current_period_end=canceled_sub.current_period_end.isoformat(),
                        cancel_at_period_end=True,
                        provider=canceled_sub.provider,
                        is_lifetime=getattr(canceled_sub, 'is_lifetime', False),
                        is_on_trial=False,
                    )
        except Exception as e:
            logger.error(f"Error checking canceled subscription for user {user.id}: {str(e)}", exc_info=True)
        
        # Free tier
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
    
    try:
        # Get plan name
        plan_name = await _get_plan_name(db, subscription.plan)
        
        # Determine status - handle missing is_lifetime column gracefully
        status = subscription.status
        try:
            # Try to get is_lifetime from the subscription object
            is_lifetime = getattr(subscription, 'is_lifetime', False)
            # If it's None, default to False
            if is_lifetime is None:
                is_lifetime = False
        except (AttributeError, KeyError):
            is_lifetime = False
        
        if is_lifetime:
            status = "active"  # Lifetime is always "active"
        
        return SubscriptionMeResponse(
            has_subscription=True,
            plan_id=subscription.plan,
            plan_name=plan_name,
            status=status,
            current_period_end=subscription.current_period_end.isoformat() if subscription.current_period_end else None,
            cancel_at_period_end=subscription.cancel_at_period_end or False,
            provider=subscription.provider,
            is_lifetime=bool(is_lifetime),  # Ensure it's a boolean
            is_on_trial=subscription.status == SubscriptionStatus.trialing.value,
        )
    except AttributeError as e:
        logger.error(f"Missing attribute in subscription for user {user.id}: {str(e)}", exc_info=True)
        # Return free tier on attribute error (likely missing column)
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
    except Exception as e:
        logger.error(f"Error processing subscription for user {user.id}: {str(e)}", exc_info=True)
        # Return free tier on error
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
    
    For LemonSqueezy, this cancels at the payment provider (stops future renewals),
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
    
    if subscription.provider != "lemonsqueezy":
        if subscription.provider == "coinbase":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Crypto subscriptions do not auto-renew, so cancellation is not required.",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Provider does not support cancellation via API: {subscription.provider}",
        )

    if not settings.lemonsqueezy_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment system not configured. Please contact support.",
        )

    if not subscription.provider_subscription_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Subscription is missing provider subscription ID. Please contact support.",
        )

    # Cancel at LemonSqueezy (stops renewals; access remains until ends_at).
    client = LemonSqueezySubscriptionClient(api_key=settings.lemonsqueezy_api_key)
    try:
        provider_payload = await client.cancel_subscription(subscription.provider_subscription_id)
    except LemonSqueezyApiError as e:
        logger.error(
            "LemonSqueezy cancellation failed for user=%s subscription=%s provider_subscription_id=%s status=%s",
            user.id,
            subscription.id,
            subscription.provider_subscription_id,
            e.status_code,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to cancel subscription with payment provider. Please try again or contact support.",
        )

    provider_attrs = (provider_payload or {}).get("data", {}).get("attributes", {}) or {}

    # Best-effort: update period end from provider "ends_at" (ISO8601).
    ends_at = provider_attrs.get("ends_at")
    if ends_at:
        try:
            subscription.current_period_end = datetime.fromisoformat(str(ends_at).replace("Z", "+00:00"))
        except Exception:
            pass

    # Best-effort: store provider metadata for audit/debug.
    try:
        subscription.provider_metadata = provider_attrs
    except Exception:
        pass

    # Update our subscription record.
    subscription.cancel_at_period_end = True
    subscription.cancelled_at = datetime.now(timezone.utc)

    # Prefer the provider status if present.
    status_value = str(provider_attrs.get("status") or "").strip().lower()
    if status_value:
        status_map = {
            "active": SubscriptionStatus.active.value,
            "past_due": SubscriptionStatus.past_due.value,
            "cancelled": SubscriptionStatus.cancelled.value,
            "expired": SubscriptionStatus.expired.value,
            "on_trial": SubscriptionStatus.trialing.value,
            "paused": SubscriptionStatus.paused.value,
        }
        subscription.status = status_map.get(status_value, subscription.status)

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

