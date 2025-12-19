"""
Coinbase Commerce webhook routes.
"""

from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import hmac
import json
import logging
import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import and_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_db
from app.models.affiliate_commission import CommissionSaleType
from app.models.payment_event import PaymentEvent
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.user import SubscriptionStatusEnum, User
from app.services.coinbase_subscription_fulfillment_service import CoinbaseSubscriptionFulfillmentService
from app.api.routes.webhooks.shared_handlers import (
    _handle_affiliate_commission,
    _handle_credit_pack_purchase,
    _handle_parlay_purchase_confirmed,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/webhooks/coinbase")
async def handle_coinbase_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_cc_webhook_signature: str = Header(None, alias="X-CC-Webhook-Signature"),
):
    """
    Handle Coinbase Commerce webhook events.

    Events handled:
    - charge:confirmed: Payment confirmed, activate lifetime subscription (or fulfill a credit pack)
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

    # Event-level idempotency: ignore duplicate webhook deliveries
    if event_id:
        existing = await db.execute(select(PaymentEvent.id).where(PaymentEvent.event_id == event_id))
        if existing.scalar_one_or_none():
            logger.info(f"Duplicate Coinbase webhook event_id={event_id}; skipping")
            return {"status": "ok"}

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

    # Check if this is a one-time parlay purchase
    purchase_type = metadata.get("purchase_type")
    parlay_type = metadata.get("parlay_type")

    # Handle specific events
    try:
        if event_type == "charge:confirmed":
            # Check for one-time parlay purchase first
            if purchase_type == "parlay_one_time":
                await _handle_parlay_purchase_confirmed(db, user_id, parlay_type, "coinbase", payload)
            else:
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

        if event.processed == "pending":
            event.mark_processed()
    except Exception as e:
        logger.error(f"Error processing Coinbase webhook: {e}")
        event.mark_failed(str(e))

    try:
        await db.commit()
    except IntegrityError as e:
        # Most commonly: duplicate payment_events.event_id unique constraint (race condition).
        await db.rollback()
        msg = str(getattr(e, "orig", e))
        if "payment_events" in msg and "event_id" in msg:
            logger.info(f"Duplicate Coinbase PaymentEvent insert (event_id={event_id}); skipping")
            return {"status": "ok"}
        raise
    return {"status": "ok"}


async def _handle_coinbase_charge_confirmed(
    db: AsyncSession,
    payload: dict,
    user_id: str,
    metadata: dict,
):
    """Handle confirmed Coinbase charge - could be subscription or credit pack."""
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

    # Check if this is a credit pack purchase
    credit_pack_id = metadata.get("credit_pack_id")
    if credit_pack_id:
        await _handle_credit_pack_purchase(db, user_id, credit_pack_id, charge_data.get("id", ""), "coinbase")
        return

    # Otherwise, handle as subscription (monthly/annual crypto or lifetime).
    plan_code = metadata.get("plan_code", "PG_LIFETIME")
    charge_id = str(charge_data.get("id", "")).strip()

    # Get price for commission
    pricing = charge_data.get("pricing", {})
    local_price = pricing.get("local", {})
    price = Decimal(str(local_price.get("amount", "0")))

    # Determine whether this is the user's first purchase for this plan (affiliate logic).
    prior = await db.execute(
        select(Subscription.id).where(
            and_(
                Subscription.user_id == uuid.UUID(user_id),
                Subscription.provider == "coinbase",
                Subscription.plan == plan_code,
            )
        )
    )
    is_first_for_plan = prior.scalar_one_or_none() is None

    # Create subscription record (time-based for monthly/annual; lifetime for lifetime).
    fulfillment = CoinbaseSubscriptionFulfillmentService(db)
    subscription = await fulfillment.fulfill_from_confirmed_charge(
        user_id=user_id,
        plan_code=plan_code,
        charge_id=charge_id,
        charge_data=charge_data,
    )
    if subscription is None:
        # Already processed for this charge id.
        return

    # Handle affiliate commission
    if price > 0:
        await _handle_affiliate_commission(
            db=db,
            user_id=user_id,
            sale_type=CommissionSaleType.SUBSCRIPTION.value,
            sale_amount=price,
            sale_id=charge_id,
            is_first_subscription=is_first_for_plan,
            subscription_plan=plan_code,
        )

    logger.info(f"Created Coinbase subscription for user {user_id}, plan={plan_code}")


