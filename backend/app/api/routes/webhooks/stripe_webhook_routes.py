"""
Stripe webhook routes.

Handles Stripe events for:
- Subscriptions (created, updated, deleted)
- Checkout sessions (completed)
- Invoices (paid, payment_failed)
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession

import stripe
from app.core.config import settings
from app.core.dependencies import get_db
from app.models.payment_event import PaymentEvent
from app.services.stripe_service import StripeService
from app.api.routes.webhooks.shared_handlers import (
    _handle_affiliate_commission,
    _handle_parlay_purchase_confirmed,
    _handle_credit_pack_purchase,
)
from app.models.subscription import SubscriptionStatus
from app.models.user import SubscriptionStatusEnum

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/webhooks/stripe")
async def handle_stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    stripe_signature: str = Header(None, alias="Stripe-Signature"),
):
    """
    Handle Stripe webhook events.

    Events handled:
    - checkout.session.completed: Checkout completed (subscription or one-time)
    - customer.subscription.created: New subscription activated
    - customer.subscription.updated: Subscription renewed or changed
    - customer.subscription.deleted: Subscription cancelled
    - invoice.paid: Recurring payment succeeded (renewal)
    - invoice.payment_failed: Recurring payment failed

    Security:
    - Verifies webhook signature using Stripe SDK
    - Logs all events to payment_events table
    """
    # Get raw body for signature verification
    body = await request.body()

    # Verify signature
    if not settings.stripe_webhook_secret:
        logger.warning("Stripe webhook secret not configured, skipping signature verification")
        # If no secret configured, parse event without verification (dev/test only)
        try:
            import json
            event = json.loads(body.decode("utf-8"))
        except Exception as e:
            logger.error(f"Failed to parse Stripe webhook payload: {e}")
            raise HTTPException(status_code=400, detail="Invalid JSON")
    else:
        if not stripe_signature:
            logger.warning("Stripe webhook missing signature")
            raise HTTPException(status_code=401, detail="Missing signature")

        try:
            event = stripe.Webhook.construct_event(
                body, stripe_signature, settings.stripe_webhook_secret
            )
        except ValueError as e:
            logger.error(f"Invalid payload in Stripe webhook: {e}")
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError as e:
            logger.warning(f"Stripe webhook signature mismatch: {e}")
            raise HTTPException(status_code=401, detail="Invalid signature")

    event_id = event.get("id")
    event_type = event.get("type")

    # Event-level idempotency: ignore duplicate webhook deliveries
    result = await db.execute(
        PaymentEvent.__table__.select().where(PaymentEvent.event_id == event_id)
    )
    existing_event = result.first()

    if existing_event:
        logger.info(f"Ignoring duplicate Stripe webhook event: {event_id}")
        return {"status": "ok", "message": "Duplicate event"}

    # Log event
    from datetime import datetime, timezone
    event_record = PaymentEvent(
        event_id=event_id,
        provider="stripe",
        event_type=event_type,
        raw_payload=event,
        occurred_at=datetime.fromtimestamp(event.get("created", 0), tz=timezone.utc) if event.get("created") else datetime.now(timezone.utc),
        processed="pending",
    )
    db.add(event_record)
    await db.commit()
    await db.refresh(event_record)

    # Process event
    try:
        stripe_service = StripeService(db)
        await stripe_service.sync_subscription_from_webhook(event)

        # Handle additional events that need special processing
        data = event.get("data", {}).get("object", {})

        if event_type == "checkout.session.completed":
            await _handle_stripe_checkout_completed(db, data, stripe_service)

        # Mark event as processed
        event_record.mark_processed()
        await db.commit()

        logger.info(f"Processed Stripe webhook event: {event_type} ({event_id})")
    except Exception as e:
        logger.error(f"Error processing Stripe webhook event {event_id}: {e}", exc_info=True)
        event_record.mark_failed(str(e))
        await db.commit()
        # Don't raise - return 200 to prevent Stripe retries for transient errors
        # Stripe will retry on 5xx errors, but we want to handle retries manually

    return {"status": "ok"}


async def _handle_stripe_checkout_completed(
    db: AsyncSession, session_data: dict, stripe_service: StripeService
) -> None:
    """Handle additional processing for checkout.session.completed events."""
    metadata = session_data.get("metadata", {})
    user_id = metadata.get("user_id")
    session_id = session_data.get("id")

    # Handle one-time payments (credits, parlay purchases)
    mode = session_data.get("mode")
    if mode == "payment":
        # One-time payment - check metadata for purchase type
        purchase_type = metadata.get("purchase_type")
        if purchase_type == "credit_pack":
            credit_pack_id = metadata.get("credit_pack_id")
            if user_id and credit_pack_id:
                await _handle_credit_pack_purchase(
                    db=db,
                    user_id=user_id,
                    credit_pack_id=credit_pack_id,
                    sale_id=session_id,
                    provider="stripe",
                )
        elif purchase_type == "parlay_one_time":
            parlay_type = metadata.get("parlay_type", "single")
            if user_id:
                await _handle_parlay_purchase_confirmed(
                    db=db,
                    user_id=user_id,
                    parlay_type=parlay_type,
                    provider="stripe",
                    payload=session_data,
                )

