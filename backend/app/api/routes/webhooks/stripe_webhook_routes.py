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
from app.models.subscription import SubscriptionStatus, Subscription
from app.models.user import SubscriptionStatusEnum, User
from sqlalchemy import select
from datetime import datetime, timezone
import uuid

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
        logger.info(f"Processing Stripe webhook event: {event_type} ({event_id})")
        stripe_service = StripeService(db)
        await stripe_service.sync_subscription_from_webhook(event)

        # Handle additional events that need special processing
        data = event.get("data", {}).get("object", {})

        if event_type == "checkout.session.completed":
            logger.info(f"Handling checkout.session.completed for session {data.get('id')}")
            await _handle_stripe_checkout_completed(db, data, stripe_service)

        # Mark event as processed
        event_record.mark_processed()
        await db.commit()

        logger.info(f"✅ Successfully processed Stripe webhook event: {event_type} ({event_id})")
    except Exception as e:
        error_msg = str(e)
        logger.error(
            f"❌ Error processing Stripe webhook event {event_id} ({event_type}): {error_msg}",
            exc_info=True
        )
        event_record.mark_failed(error_msg)
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
    payment_status = session_data.get("payment_status")

    # Only process if payment was successful
    if payment_status != "paid":
        logger.warning(
            f"Checkout session {session_id} completed but payment_status is '{payment_status}', skipping fulfillment"
        )
        return

    # Handle one-time payments (credits, parlay purchases)
    mode = session_data.get("mode")
    if mode == "payment":
        # One-time payment - check metadata for purchase type
        purchase_type = metadata.get("purchase_type")
        if purchase_type == "credit_pack":
            credit_pack_id = metadata.get("credit_pack_id")
            if user_id and credit_pack_id:
                try:
                    await _handle_credit_pack_purchase(
                        db=db,
                        user_id=user_id,
                        credit_pack_id=credit_pack_id,
                        sale_id=session_id,
                        provider="stripe",
                    )
                    logger.info(
                        f"Successfully processed credit pack purchase: user={user_id}, "
                        f"pack={credit_pack_id}, session={session_id}"
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to process credit pack purchase: user={user_id}, "
                        f"pack={credit_pack_id}, session={session_id}, error={e}",
                        exc_info=True
                    )
                    # Re-raise to mark event as failed
                    raise
            else:
                logger.warning(
                    f"Credit pack purchase missing required metadata: user_id={user_id}, "
                    f"credit_pack_id={credit_pack_id}, session={session_id}"
                )
        elif purchase_type == "parlay_one_time":
            parlay_type = metadata.get("parlay_type", "single")
            if user_id:
                try:
                    await _handle_parlay_purchase_confirmed(
                        db=db,
                        user_id=user_id,
                        parlay_type=parlay_type,
                        provider="stripe",
                        payload=session_data,
                    )
                    logger.info(
                        f"Successfully processed parlay purchase: user={user_id}, "
                        f"type={parlay_type}, session={session_id}"
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to process parlay purchase: user={user_id}, "
                        f"type={parlay_type}, session={session_id}, error={e}",
                        exc_info=True
                    )
                    # Re-raise to mark event as failed
                    raise
            else:
                logger.warning(
                    f"Parlay purchase missing user_id: session={session_id}, metadata={metadata}"
                )
        elif purchase_type == "lifetime_subscription" or metadata.get("plan_code", "").endswith("_LIFETIME_CARD"):
            # Lifetime subscription purchase - create lifetime subscription record
            plan_code = metadata.get("plan_code", "PG_LIFETIME_CARD")
            if user_id:
                try:
                    await _handle_lifetime_subscription_purchase(
                        db=db,
                        user_id=user_id,
                        plan_code=plan_code,
                        session_id=session_id,
                        stripe_service=stripe_service,
                    )
                    logger.info(
                        f"Successfully processed lifetime subscription purchase: user={user_id}, "
                        f"plan={plan_code}, session={session_id}"
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to process lifetime subscription: user={user_id}, "
                        f"plan={plan_code}, session={session_id}, error={e}",
                        exc_info=True
                    )
                    raise
            else:
                logger.warning(
                    f"Lifetime subscription missing user_id: session={session_id}, metadata={metadata}"
                )
    elif mode == "subscription":
        # Subscription checkout - activation happens in customer.subscription.created event
        subscription_id = session_data.get("subscription")
        logger.info(
            f"Subscription checkout completed: user={user_id}, "
            f"subscription={subscription_id}, session={session_id}. "
            "Subscription will be activated by customer.subscription.created event."
        )


async def _handle_lifetime_subscription_purchase(
    db: AsyncSession,
    user_id: str,
    plan_code: str,
    session_id: str,
    stripe_service: StripeService,
) -> None:
    """Handle lifetime subscription purchase from one-time payment."""
    user_uuid = uuid.UUID(user_id)
    
    # Check if user already has a lifetime subscription
    result = await db.execute(
        select(Subscription).where(
            Subscription.user_id == user_uuid,
            Subscription.is_lifetime == True,
        )
    )
    existing_lifetime = result.scalar_one_or_none()
    
    if existing_lifetime:
        logger.warning(
            f"User {user_id} already has lifetime subscription, skipping duplicate purchase"
        )
        return
    
    # Get user
    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalar_one_or_none()
    if not user:
        logger.error(f"User {user_id} not found for lifetime subscription")
        raise ValueError(f"User {user_id} not found")
    
    # Create lifetime subscription record
    subscription = Subscription(
        id=uuid.uuid4(),
        user_id=user_uuid,
        plan=plan_code,
        provider="stripe",
        provider_subscription_id=f"lifetime_{session_id}",
        provider_customer_id=user.stripe_customer_id,
        status=SubscriptionStatus.active.value,
        current_period_start=datetime.now(timezone.utc),
        current_period_end=None,  # Lifetime has no end date
        is_lifetime=True,
        provider_metadata={"checkout_session_id": session_id},
    )
    db.add(subscription)
    
    # Update user subscription fields
    user.subscription_plan = plan_code
    user.subscription_status = SubscriptionStatusEnum.active.value
    user.subscription_renewal_date = None  # Lifetime has no renewal
    user.subscription_last_billed_at = datetime.now(timezone.utc)
    # Reset usage counters
    user.premium_ai_parlays_used = 0
    user.premium_ai_parlays_period_start = datetime.now(timezone.utc)
    user.premium_custom_builder_used = 0
    user.premium_custom_builder_period_start = datetime.now(timezone.utc)
    
    await db.commit()
    logger.info(
        f"✅ Lifetime subscription ACTIVATED: user={user_id}, plan={plan_code}, session={session_id}"
    )

