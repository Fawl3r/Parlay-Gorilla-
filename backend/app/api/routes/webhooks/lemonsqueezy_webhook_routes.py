"""
LemonSqueezy webhook routes.

Handles LemonSqueezy events for:
- Subscriptions
- One-time parlay purchases (pay-per-use)

Credit pack fulfillment is wired separately (see shared + fulfillment services).
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import hmac
import json
import logging
import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import and_, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_db
from app.models.affiliate_commission import CommissionSaleType, CommissionSettlementProvider
from app.models.payment_event import PaymentEvent
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.user import SubscriptionStatusEnum, User
from app.api.routes.webhooks.shared_handlers import (
    _handle_affiliate_commission,
    _handle_parlay_purchase_confirmed,
)
from app.services.lemonsqueezy_credit_pack_webhook_handler import (
    LemonSqueezyCreditPackWebhookHandler,
)
from app.services.lemonsqueezy_lifetime_access_webhook_handler import (
    LemonSqueezyLifetimeAccessWebhookHandler,
)
from app.services.lemonsqueezy_recurring_payment_webhook_handler import (
    LemonSqueezyRecurringPaymentWebhookHandler,
)
from app.services.auth import EmailNormalizer
from app.utils.datetime_utils import coerce_utc, now_utc

logger = logging.getLogger(__name__)
router = APIRouter()


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

    # Event-level idempotency: ignore duplicate webhook deliveries
    if event_id:
        existing = await db.execute(select(PaymentEvent.id).where(PaymentEvent.event_id == event_id))
        if existing.scalar_one_or_none():
            logger.info(f"Duplicate LemonSqueezy webhook event_id={event_id}; skipping")
            return {"status": "ok"}

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

    # Check if this is a one-time parlay purchase
    purchase_type = custom_data.get("purchase_type")
    parlay_type = custom_data.get("parlay_type")

    # Handle specific events
    try:
        # Check for one-time parlay purchase first
        if purchase_type == "parlay_one_time" and event_name in (
            "order_created",
            "subscription_payment_success",
            "order_completed",
        ):
            await _handle_parlay_purchase_confirmed(db, user_id, parlay_type, "lemonsqueezy", payload)
        elif purchase_type == "credit_pack":
            # Only fulfill credit packs on final-ish order events
            if event_name in ("order_created", "order_completed"):
                await LemonSqueezyCreditPackWebhookHandler(db).handle(payload, user_id)
            else:
                event.mark_skipped(f"Ignoring non-final credit pack event: {event_name}")
        elif purchase_type == "lifetime_access":
            # Lifetime card purchase is a one-time order (not a recurring subscription).
            if event_name in ("order_created", "order_completed"):
                await LemonSqueezyLifetimeAccessWebhookHandler(db).handle(payload, user_id)
            else:
                event.mark_skipped(f"Ignoring non-final lifetime order event: {event_name}")
        elif event_name == "subscription_created":
            await _handle_ls_subscription_created(db, payload, user_id)
        elif event_name == "subscription_updated":
            await _handle_ls_subscription_updated(db, payload)
        elif event_name in ("subscription_cancelled", "subscription_expired"):
            await _handle_ls_subscription_cancelled(db, payload)
        elif event_name == "subscription_payment_success":
            await LemonSqueezyRecurringPaymentWebhookHandler(db).handle_payment_success(payload)
        elif event_name == "subscription_payment_failed":
            await LemonSqueezyRecurringPaymentWebhookHandler(db).handle_payment_failed(payload)
        else:
            logger.info(f"Unhandled LemonSqueezy event: {event_name}")
            event.mark_skipped(f"Unhandled event type: {event_name}")

        if event.processed == "pending":
            event.mark_processed()
    except Exception as e:
        logger.error(f"Error processing LemonSqueezy webhook: {e}")
        event.mark_failed(str(e))

    try:
        await db.commit()
    except IntegrityError as e:
        # Most commonly: duplicate payment_events.event_id unique constraint (race condition).
        await db.rollback()
        msg = str(getattr(e, "orig", e))
        if "payment_events" in msg and "event_id" in msg:
            logger.info(f"Duplicate LemonSqueezy PaymentEvent insert (event_id={event_id}); skipping")
            return {"status": "ok"}
        raise
    return {"status": "ok"}


async def _handle_ls_subscription_created(db: AsyncSession, payload: dict, user_id: str = None):
    """Handle new LemonSqueezy subscription."""
    data = payload.get("data", {})
    attributes = data.get("attributes", {})

    # Find user
    if not user_id:
        email = attributes.get("user_email")
        if email:
            normalized_email = EmailNormalizer().normalize(str(email))
            user = None
            if normalized_email:
                result = await db.execute(select(User).where(func.lower(User.email) == normalized_email))
                user = result.scalar_one_or_none()
            if user:
                user_id = str(user.id)

    if not user_id:
        logger.warning("LemonSqueezy subscription_created: Could not find user")
        return

    # Get plan code from custom data or variant
    custom_data = attributes.get("first_subscription_item", {}).get("custom_data", {})
    plan_code = custom_data.get("plan_code", "starter_monthly")

    # Calculate period dates
    created_at = datetime.now(timezone.utc)
    period_end = created_at + timedelta(days=30)  # Default 30 days

    if attributes.get("renews_at"):
        try:
            period_end = datetime.fromisoformat(attributes["renews_at"].replace("Z", "+00:00"))
        except Exception:
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

    # Update user's subscription fields
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if user:
        # Determine plan level from plan_code
        if "elite" in plan_code.lower():
            user.plan = "elite"
        else:
            user.plan = "standard"

        # Update subscription fields on user
        user.subscription_plan = plan_code
        user.subscription_status = SubscriptionStatusEnum.active.value
        user.subscription_renewal_date = period_end
        user.subscription_last_billed_at = created_at

        # Reset daily counter
        user.daily_parlays_used = 0

    # Get price from attributes for commission calculation
    price = Decimal(str(attributes.get("total", 0))) / 100  # Convert cents to dollars
    if price <= 0:
        # Try alternative price fields
        price_data = attributes.get("first_subscription_item", {})
        price = Decimal(str(price_data.get("price", 0))) / 100

    # Handle affiliate commission (first subscription payment)
    if price > 0:
        await _handle_affiliate_commission(
            db=db,
            user_id=user_id,
            sale_type=CommissionSaleType.SUBSCRIPTION.value,
            sale_amount=price,
            sale_id=str(data.get("id", "")),
            settlement_provider=CommissionSettlementProvider.LEMONSQUEEZY.value,
            is_first_subscription=True,
            subscription_plan=plan_code,
        )

    logger.info(f"Created LemonSqueezy subscription for user {user_id}, plan: {plan_code}")


async def _handle_ls_subscription_updated(db: AsyncSession, payload: dict):
    """Handle LemonSqueezy subscription update (renewal)."""
    data = payload.get("data", {})
    attributes = data.get("attributes", {})
    subscription_id = str(data.get("id", ""))

    # Find existing subscription
    result = await db.execute(select(Subscription).where(Subscription.provider_subscription_id == subscription_id))
    subscription = result.scalar_one_or_none()

    if not subscription:
        logger.warning(f"LemonSqueezy subscription_updated: Subscription not found: {subscription_id}")
        return

    # Update period dates
    if attributes.get("renews_at"):
        try:
            subscription.current_period_end = datetime.fromisoformat(attributes["renews_at"].replace("Z", "+00:00"))
        except Exception:
            pass

    # Update status
    status_value = attributes.get("status", "active")
    status_map = {
        "active": SubscriptionStatus.active.value,
        "past_due": SubscriptionStatus.past_due.value,
        "cancelled": SubscriptionStatus.cancelled.value,
        "expired": SubscriptionStatus.expired.value,
        "on_trial": SubscriptionStatus.trialing.value,
        "paused": SubscriptionStatus.paused.value,
    }
    subscription.status = status_map.get(status_value, SubscriptionStatus.active.value)

    # Keep user table in sync (billing UI + hybrid access model relies on these fields).
    user_result = await db.execute(select(User).where(User.id == subscription.user_id))
    user = user_result.scalar_one_or_none()
    if user:
        # Update renewal/end date (if present).
        if subscription.current_period_end:
            user.subscription_renewal_date = subscription.current_period_end

        # Mirror status to user subscription_status.
        if subscription.status in (SubscriptionStatus.active.value, SubscriptionStatus.trialing.value):
            user.subscription_status = SubscriptionStatusEnum.active.value
        elif subscription.status == SubscriptionStatus.past_due.value:
            # Treat past_due as active for access (grace period).
            user.subscription_status = SubscriptionStatusEnum.active.value
        elif subscription.status == SubscriptionStatus.cancelled.value:
            user.subscription_status = SubscriptionStatusEnum.canceled.value
        elif subscription.status == SubscriptionStatus.expired.value:
            user.subscription_status = SubscriptionStatusEnum.expired.value
            user.plan = "free"
            user.subscription_plan = None
        else:
            # Default: keep as-is.
            pass

        # Ensure user.plan + subscription_plan are set while subscription grants access.
        if user.subscription_status in (SubscriptionStatusEnum.active.value, SubscriptionStatusEnum.canceled.value):
            user.subscription_plan = subscription.plan
            if "elite" in (subscription.plan or "").lower():
                user.plan = "elite"
            else:
                user.plan = "standard"

    logger.info(f"Updated LemonSqueezy subscription {subscription_id}")



async def _handle_ls_subscription_cancelled(db: AsyncSession, payload: dict):
    """Handle LemonSqueezy subscription cancellation."""
    data = payload.get("data", {})
    attributes = data.get("attributes", {})
    subscription_id = str(data.get("id", ""))

    # Find existing subscription
    result = await db.execute(select(Subscription).where(Subscription.provider_subscription_id == subscription_id))
    subscription = result.scalar_one_or_none()

    if not subscription:
        logger.warning(f"LemonSqueezy subscription_cancelled: Subscription not found: {subscription_id}")
        return

    # Best-effort: update period end from provider payload (ends_at is set for cancelled/expired).
    ends_at = attributes.get("ends_at") or attributes.get("renews_at")
    if ends_at:
        try:
            subscription.current_period_end = datetime.fromisoformat(str(ends_at).replace("Z", "+00:00"))
        except Exception:
            pass

    # Mark as cancelled
    subscription.status = SubscriptionStatus.cancelled.value
    subscription.cancelled_at = datetime.now(timezone.utc)
    subscription.cancel_at_period_end = True

    # Update user subscription status
    result = await db.execute(select(User).where(User.id == subscription.user_id))
    user = result.scalar_one_or_none()
    if user:
        user.subscription_status = SubscriptionStatusEnum.canceled.value
        if subscription.current_period_end:
            user.subscription_renewal_date = subscription.current_period_end

        # Downgrade to free if past period end
        if subscription.current_period_end and coerce_utc(subscription.current_period_end) < now_utc():
            user.plan = "free"
            user.subscription_plan = None
            user.subscription_status = SubscriptionStatusEnum.expired.value

    logger.info(f"Cancelled LemonSqueezy subscription {subscription_id}")


