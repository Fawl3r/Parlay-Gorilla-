"""
Webhook diagnostics endpoint for debugging payment activation issues.

This endpoint helps diagnose why subscriptions/credits aren't activating
after a purchase in test mode.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel

import logging

from app.core.dependencies import get_db, get_current_user
from app.models.payment_event import PaymentEvent
from app.models.user import User
from app.models.subscription import Subscription
from app.models.subscription import SubscriptionStatus

logger = logging.getLogger(__name__)
router = APIRouter()


class WebhookEventDiagnostic(BaseModel):
    """Diagnostic info for a webhook event."""
    event_id: Optional[str]
    event_type: str
    provider: str
    processed: str
    processing_error: Optional[str]
    occurred_at: Optional[datetime]
    created_at: datetime
    processed_at: Optional[datetime]
    has_user_id: bool
    has_subscription_id: bool
    has_order_id: bool


class SubscriptionDiagnostic(BaseModel):
    """Diagnostic info for user subscription."""
    has_subscription: bool
    subscription_id: Optional[str]
    plan: Optional[str]
    status: Optional[str]
    provider: Optional[str]
    is_lifetime: bool
    current_period_end: Optional[datetime]
    user_subscription_status: Optional[str]
    user_subscription_plan: Optional[str]


class CreditDiagnostic(BaseModel):
    """Diagnostic info for user credits."""
    credit_balance: int
    recent_credit_pack_purchases: int


class WebhookDiagnosticsResponse(BaseModel):
    """Complete webhook diagnostics for a user."""
    user_id: str
    recent_webhook_events: List[WebhookEventDiagnostic]
    subscription: SubscriptionDiagnostic
    credits: CreditDiagnostic
    recommendations: List[str]


@router.get("/billing/webhook-diagnostics", response_model=WebhookDiagnosticsResponse)
async def get_webhook_diagnostics(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    hours: int = 24,
):
    """
    Get webhook diagnostics for the current user.
    
    Helps diagnose why subscriptions/credits aren't activating after purchase.
    Checks:
    - Recent webhook events (last 24 hours by default)
    - Subscription status
    - Credit balance
    - Provides recommendations for fixing issues
    """
    user_id = str(user.id)
    recommendations = []
    
    # Get recent webhook events (check all providers, filter by user metadata)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    
    # Get events from last N hours
    result = await db.execute(
        select(PaymentEvent)
        .where(PaymentEvent.created_at >= cutoff)
        .order_by(desc(PaymentEvent.created_at))
        .limit(50)
    )
    all_events = result.scalars().all()
    
    # Filter events that might be for this user
    # Check if user_id is in metadata or if event references user's customer/subscription IDs
    user_events = []
    user_customer_ids = set()
    user_subscription_ids = set()
    
    # Get user's customer/subscription IDs
    if user.stripe_customer_id:
        user_customer_ids.add(user.stripe_customer_id)
    if user.stripe_subscription_id:
        user_subscription_ids.add(user.stripe_subscription_id)
    
    # Get subscription IDs from subscriptions table
    sub_result = await db.execute(
        select(Subscription)
        .where(Subscription.user_id == user.id)
    )
    for sub in sub_result.scalars().all():
        if sub.provider_customer_id:
            user_customer_ids.add(sub.provider_customer_id)
        if sub.provider_subscription_id:
            user_subscription_ids.add(sub.provider_subscription_id)
    
    for event in all_events:
        # Check if event is for this user
        is_user_event = False
        
        # Check user_id in event
        if event.user_id == user.id:
            is_user_event = True
        
        # Check metadata in raw_payload
        if not is_user_event and event.raw_payload:
            payload = event.raw_payload
            metadata = payload.get("metadata", {}) or {}
            if isinstance(metadata, dict):
                event_user_id = metadata.get("user_id")
                if event_user_id and str(event_user_id) == user_id:
                    is_user_event = True
            
            # Check data.object for customer/subscription IDs
            data = payload.get("data", {})
            obj = data.get("object", {}) if isinstance(data, dict) else {}
            if isinstance(obj, dict):
                customer_id = obj.get("customer")
                subscription_id = obj.get("id") if event.event_type.startswith("customer.subscription") else obj.get("subscription")
                
                if customer_id and customer_id in user_customer_ids:
                    is_user_event = True
                if subscription_id and subscription_id in user_subscription_ids:
                    is_user_event = True
        
        if is_user_event:
            user_events.append(event)
    
    # Build diagnostic events
    diagnostic_events = []
    for event in user_events[:10]:  # Limit to 10 most recent
        payload = event.raw_payload or {}
        data = payload.get("data", {}) or {}
        obj = data.get("object", {}) or {}
        
        diagnostic_events.append(WebhookEventDiagnostic(
            event_id=event.event_id,
            event_type=event.event_type,
            provider=event.provider,
            processed=event.processed,
            processing_error=event.processing_error,
            occurred_at=event.occurred_at,
            created_at=event.created_at,
            processed_at=event.processed_at,
            has_user_id=event.user_id is not None,
            has_subscription_id=event.provider_subscription_id is not None,
            has_order_id=event.provider_order_id is not None,
        ))
    
    # Check subscription status
    sub_result = await db.execute(
        select(Subscription)
        .where(Subscription.user_id == user.id)
        .order_by(desc(Subscription.created_at))
        .limit(1)
    )
    subscription = sub_result.scalar_one_or_none()
    
    subscription_diag = SubscriptionDiagnostic(
        has_subscription=subscription is not None,
        subscription_id=str(subscription.id) if subscription else None,
        plan=subscription.plan if subscription else None,
        status=subscription.status if subscription else None,
        provider=subscription.provider if subscription else None,
        is_lifetime=getattr(subscription, 'is_lifetime', False) if subscription else False,
        current_period_end=subscription.current_period_end if subscription else None,
        user_subscription_status=user.subscription_status,
        user_subscription_plan=user.subscription_plan,
    )
    
    # Check credits
    credit_balance = int(getattr(user, "credit_balance", 0) or 0)
    
    # Count recent credit pack purchases (would need credit_pack_purchases table)
    credits_diag = CreditDiagnostic(
        credit_balance=credit_balance,
        recent_credit_pack_purchases=0,  # TODO: Query credit_pack_purchases table
    )
    
    # Generate recommendations
    if not diagnostic_events:
        recommendations.append(
            "⚠️ No webhook events found in the last 24 hours. "
            "This suggests webhooks aren't reaching your server. "
            "Check: 1) Webhook URL in Stripe/LemonSqueezy dashboard, 2) Tunnel/URL is accessible, 3) Webhook secret is configured correctly."
        )
    else:
        failed_events = [e for e in diagnostic_events if e.processed == "failed"]
        if failed_events:
            recommendations.append(
                f"⚠️ Found {len(failed_events)} failed webhook event(s). "
                f"Check processing_error for details. Common issues: missing metadata, invalid user_id, database errors."
            )
        
        pending_events = [e for e in diagnostic_events if e.processed == "pending"]
        if pending_events:
            recommendations.append(
                f"⚠️ Found {len(pending_events)} pending webhook event(s). "
                "These may still be processing or may have been interrupted."
            )
    
    if not subscription_diag.has_subscription and user.subscription_status:
        recommendations.append(
            "⚠️ User has subscription_status set but no subscription record found. "
            "This suggests webhook processing didn't complete. Check webhook logs."
        )
    
    if subscription_diag.has_subscription:
        if subscription_diag.status not in [SubscriptionStatus.active.value, SubscriptionStatus.trialing.value]:
            recommendations.append(
                f"⚠️ Subscription exists but status is '{subscription_diag.status}', not 'active' or 'trialing'. "
                "Subscription may not be activated yet or may have been cancelled."
            )
        elif subscription_diag.user_subscription_status != subscription_diag.status:
            recommendations.append(
                "⚠️ Subscription record status doesn't match user.subscription_status. "
                "User table may not be synced. This can happen if webhook processing was interrupted."
            )
    
    # Check for checkout.session.completed without subscription.created
    checkout_events = [e for e in diagnostic_events if e.event_type == "checkout.session.completed"]
    subscription_events = [e for e in diagnostic_events if "subscription.created" in e.event_type]
    
    if checkout_events and not subscription_events and not subscription_diag.has_subscription:
        recommendations.append(
            "⚠️ Found checkout.session.completed but no customer.subscription.created event. "
            "For subscription purchases, Stripe sends checkout.session.completed first, then subscription.created. "
            "If subscription.created never arrives, the subscription wasn't created in Stripe (check Stripe dashboard)."
        )
    
    return WebhookDiagnosticsResponse(
        user_id=user_id,
        recent_webhook_events=diagnostic_events,
        subscription=subscription_diag,
        credits=credits_diag,
        recommendations=recommendations,
    )

