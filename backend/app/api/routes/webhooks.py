"""
Webhook handlers for payment providers.

Handles incoming webhooks from:
- LemonSqueezy (subscription events)
- Coinbase Commerce (charge events)

Security:
- All webhooks are verified using provider-specific signatures
- Raw payloads are logged to payment_events for auditing
"""

from fastapi import APIRouter, Request, HTTPException, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone, timedelta
import hmac
import hashlib
import json
import logging
import uuid

from app.core.dependencies import get_db
from app.core.config import settings
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.subscription_plan import SubscriptionPlan
from app.models.payment_event import PaymentEvent
from app.models.user import User
from sqlalchemy import select, and_

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# LemonSqueezy Webhooks
# ============================================================================

@router.post("/webhooks/lemonsqueezy")
async def handle_lemonsqueezy_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_signature: str = Header(None, alias="X-Signature"),
):
    """
    Handle LemonSqueezy webhook events.
    
    Events handled:
    - subscription_created: New subscription activated
    - subscription_updated: Subscription renewed or changed
    - subscription_cancelled: Subscription cancelled
    - subscription_payment_success: Recurring payment succeeded
    - subscription_payment_failed: Recurring payment failed
    
    Security:
    - Verifies HMAC-SHA256 signature using webhook secret
    - Logs all events to payment_events table
    """
    # Get raw body for signature verification
    body = await request.body()
    body_str = body.decode("utf-8")
    
    # Verify signature
    if settings.lemonsqueezy_webhook_secret:
        if not x_signature:
            logger.warning("LemonSqueezy webhook missing signature")
            raise HTTPException(status_code=401, detail="Missing signature")
        
        expected_signature = hmac.new(
            settings.lemonsqueezy_webhook_secret.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()
        
        if not hmac.compare_digest(expected_signature, x_signature):
            logger.warning("LemonSqueezy webhook signature mismatch")
            raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Parse payload
    try:
        payload = json.loads(body_str)
    except json.JSONDecodeError:
        logger.error("Invalid JSON in LemonSqueezy webhook")
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    # Extract event info
    meta = payload.get("meta", {})
    event_name = meta.get("event_name", "unknown")
    event_id = meta.get("webhook_id")
    
    data = payload.get("data", {})
    attributes = data.get("attributes", {})
    
    # Log event
    event = PaymentEvent.from_webhook(
        provider="lemonsqueezy",
        event_type=event_name,
        payload=payload,
        event_id=event_id,
    )
    
    # Extract provider IDs
    event.provider_subscription_id = str(data.get("id", ""))
    event.provider_customer_id = str(attributes.get("customer_id", ""))
    
    # Try to find user from custom data
    custom_data = attributes.get("first_subscription_item", {}).get("custom_data", {})
    if not custom_data:
        custom_data = meta.get("custom_data", {})
    
    user_id = custom_data.get("user_id")
    if user_id:
        event.user_id = uuid.UUID(user_id)
    
    db.add(event)
    
    # Handle specific events
    try:
        if event_name == "subscription_created":
            await _handle_ls_subscription_created(db, payload, user_id)
        elif event_name == "subscription_updated":
            await _handle_ls_subscription_updated(db, payload)
        elif event_name in ("subscription_cancelled", "subscription_expired"):
            await _handle_ls_subscription_cancelled(db, payload)
        elif event_name == "subscription_payment_success":
            await _handle_ls_payment_success(db, payload)
        elif event_name == "subscription_payment_failed":
            await _handle_ls_payment_failed(db, payload)
        else:
            logger.info(f"Unhandled LemonSqueezy event: {event_name}")
            event.mark_skipped(f"Unhandled event type: {event_name}")
        
        event.mark_processed()
    except Exception as e:
        logger.error(f"Error processing LemonSqueezy webhook: {e}")
        event.mark_failed(str(e))
    
    await db.commit()
    return {"status": "ok"}


async def _handle_ls_subscription_created(db: AsyncSession, payload: dict, user_id: str = None):
    """Handle new LemonSqueezy subscription."""
    data = payload.get("data", {})
    attributes = data.get("attributes", {})
    
    # Find user
    if not user_id:
        email = attributes.get("user_email")
        if email:
            result = await db.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()
            if user:
                user_id = str(user.id)
    
    if not user_id:
        logger.warning("LemonSqueezy subscription_created: Could not find user")
        return
    
    # Get plan code from custom data or variant
    custom_data = attributes.get("first_subscription_item", {}).get("custom_data", {})
    plan_code = custom_data.get("plan_code", "PG_PREMIUM_MONTHLY")
    
    # Calculate period dates
    created_at = datetime.now(timezone.utc)
    period_end = created_at + timedelta(days=30)  # Default 30 days
    
    if attributes.get("renews_at"):
        try:
            period_end = datetime.fromisoformat(attributes["renews_at"].replace("Z", "+00:00"))
        except:
            pass
    
    # Create subscription record
    subscription = Subscription(
        id=uuid.uuid4(),
        user_id=uuid.UUID(user_id),
        plan=plan_code,
        provider="lemonsqueezy",
        provider_subscription_id=str(data.get("id", "")),
        provider_customer_id=str(attributes.get("customer_id", "")),
        status=SubscriptionStatus.active.value,
        current_period_start=created_at,
        current_period_end=period_end,
        is_lifetime=False,
        provider_metadata=attributes,
    )
    
    db.add(subscription)
    
    # Update user plan
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if user:
        user.plan = "standard"  # or elite based on plan_code
    
    logger.info(f"Created LemonSqueezy subscription for user {user_id}")


async def _handle_ls_subscription_updated(db: AsyncSession, payload: dict):
    """Handle LemonSqueezy subscription update (renewal)."""
    data = payload.get("data", {})
    attributes = data.get("attributes", {})
    subscription_id = str(data.get("id", ""))
    
    # Find existing subscription
    result = await db.execute(
        select(Subscription).where(
            Subscription.provider_subscription_id == subscription_id
        )
    )
    subscription = result.scalar_one_or_none()
    
    if not subscription:
        logger.warning(f"LemonSqueezy subscription_updated: Subscription not found: {subscription_id}")
        return
    
    # Update period dates
    if attributes.get("renews_at"):
        try:
            subscription.current_period_end = datetime.fromisoformat(
                attributes["renews_at"].replace("Z", "+00:00")
            )
        except:
            pass
    
    # Update status
    status = attributes.get("status", "active")
    status_map = {
        "active": SubscriptionStatus.active.value,
        "past_due": SubscriptionStatus.past_due.value,
        "cancelled": SubscriptionStatus.cancelled.value,
        "expired": SubscriptionStatus.expired.value,
        "on_trial": SubscriptionStatus.trialing.value,
        "paused": SubscriptionStatus.paused.value,
    }
    subscription.status = status_map.get(status, SubscriptionStatus.active.value)
    
    logger.info(f"Updated LemonSqueezy subscription {subscription_id}")


async def _handle_ls_subscription_cancelled(db: AsyncSession, payload: dict):
    """Handle LemonSqueezy subscription cancellation."""
    data = payload.get("data", {})
    attributes = data.get("attributes", {})
    subscription_id = str(data.get("id", ""))
    
    # Find existing subscription
    result = await db.execute(
        select(Subscription).where(
            Subscription.provider_subscription_id == subscription_id
        )
    )
    subscription = result.scalar_one_or_none()
    
    if not subscription:
        logger.warning(f"LemonSqueezy subscription_cancelled: Subscription not found: {subscription_id}")
        return
    
    # Mark as cancelled
    subscription.status = SubscriptionStatus.cancelled.value
    subscription.cancelled_at = datetime.now(timezone.utc)
    subscription.cancel_at_period_end = True
    
    # Update user plan if past period end
    if subscription.current_period_end and subscription.current_period_end < datetime.now(timezone.utc):
        result = await db.execute(select(User).where(User.id == subscription.user_id))
        user = result.scalar_one_or_none()
        if user:
            user.plan = "free"
    
    logger.info(f"Cancelled LemonSqueezy subscription {subscription_id}")


async def _handle_ls_payment_success(db: AsyncSession, payload: dict):
    """Handle successful LemonSqueezy payment."""
    # Mostly handled by subscription_updated
    logger.info("LemonSqueezy payment success")


async def _handle_ls_payment_failed(db: AsyncSession, payload: dict):
    """Handle failed LemonSqueezy payment."""
    data = payload.get("data", {})
    subscription_id = str(data.get("id", ""))
    
    # Find existing subscription
    result = await db.execute(
        select(Subscription).where(
            Subscription.provider_subscription_id == subscription_id
        )
    )
    subscription = result.scalar_one_or_none()
    
    if subscription:
        subscription.status = SubscriptionStatus.past_due.value
    
    logger.warning(f"LemonSqueezy payment failed for subscription {subscription_id}")


# ============================================================================
# Coinbase Commerce Webhooks
# ============================================================================

@router.post("/webhooks/coinbase")
async def handle_coinbase_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_cc_webhook_signature: str = Header(None, alias="X-CC-Webhook-Signature"),
):
    """
    Handle Coinbase Commerce webhook events.
    
    Events handled:
    - charge:confirmed: Payment confirmed, activate lifetime subscription
    - charge:failed: Payment failed
    - charge:pending: Payment pending (optional logging)
    
    Security:
    - Verifies HMAC-SHA256 signature using webhook secret
    - Logs all events to payment_events table
    """
    # Get raw body for signature verification
    body = await request.body()
    body_str = body.decode("utf-8")
    
    # Verify signature
    if settings.coinbase_commerce_webhook_secret:
        if not x_cc_webhook_signature:
            logger.warning("Coinbase webhook missing signature")
            raise HTTPException(status_code=401, detail="Missing signature")
        
        expected_signature = hmac.new(
            settings.coinbase_commerce_webhook_secret.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()
        
        if not hmac.compare_digest(expected_signature, x_cc_webhook_signature):
            logger.warning("Coinbase webhook signature mismatch")
            raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Parse payload
    try:
        payload = json.loads(body_str)
    except json.JSONDecodeError:
        logger.error("Invalid JSON in Coinbase webhook")
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    # Extract event info
    event_data = payload.get("event", {})
    event_type = event_data.get("type", "unknown")
    event_id = payload.get("id")
    
    charge_data = event_data.get("data", {})
    metadata = charge_data.get("metadata", {})
    
    # Log event
    event = PaymentEvent.from_webhook(
        provider="coinbase",
        event_type=event_type,
        payload=payload,
        event_id=event_id,
    )
    
    # Extract provider IDs
    event.provider_order_id = charge_data.get("id", "")
    
    # Try to find user from metadata
    user_id = metadata.get("user_id")
    if user_id:
        event.user_id = uuid.UUID(user_id)
    
    db.add(event)
    
    # Handle specific events
    try:
        if event_type == "charge:confirmed":
            await _handle_coinbase_charge_confirmed(db, payload, user_id, metadata)
        elif event_type == "charge:failed":
            logger.warning(f"Coinbase charge failed for user {user_id}")
            event.mark_processed()
        elif event_type == "charge:pending":
            logger.info(f"Coinbase charge pending for user {user_id}")
            event.mark_processed()
        else:
            logger.info(f"Unhandled Coinbase event: {event_type}")
            event.mark_skipped(f"Unhandled event type: {event_type}")
        
        event.mark_processed()
    except Exception as e:
        logger.error(f"Error processing Coinbase webhook: {e}")
        event.mark_failed(str(e))
    
    await db.commit()
    return {"status": "ok"}


async def _handle_coinbase_charge_confirmed(
    db: AsyncSession,
    payload: dict,
    user_id: str,
    metadata: dict,
):
    """Handle confirmed Coinbase charge - activate lifetime subscription."""
    event_data = payload.get("event", {})
    charge_data = event_data.get("data", {})
    
    # Find user
    if not user_id:
        email = metadata.get("user_email")
        if email:
            result = await db.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()
            if user:
                user_id = str(user.id)
    
    if not user_id:
        logger.warning("Coinbase charge_confirmed: Could not find user")
        return
    
    # Get plan code (usually lifetime)
    plan_code = metadata.get("plan_code", "PG_LIFETIME")
    
    # Create lifetime subscription
    subscription = Subscription(
        id=uuid.uuid4(),
        user_id=uuid.UUID(user_id),
        plan=plan_code,
        provider="coinbase",
        provider_subscription_id=charge_data.get("id", ""),
        status=SubscriptionStatus.active.value,
        current_period_start=datetime.now(timezone.utc),
        current_period_end=None,  # Lifetime = no end
        is_lifetime=True,
        provider_metadata=charge_data,
    )
    
    db.add(subscription)
    
    # Update user plan
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if user:
        user.plan = "elite"  # Lifetime = elite tier
    
    logger.info(f"Created Coinbase lifetime subscription for user {user_id}")

