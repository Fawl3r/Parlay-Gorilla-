"""
Stripe Service for subscription and payment management.

Handles:
- Creating Stripe Checkout sessions for subscriptions and one-time payments
- Creating Stripe Customer Portal sessions
- Syncing subscription state from Stripe webhooks
"""

import logging
import uuid
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

import stripe
from app.core.config import settings
from app.models.user import User
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.subscription_plan import SubscriptionPlan

logger = logging.getLogger(__name__)

# Initialize Stripe with API key
if settings.stripe_secret_key:
    stripe.api_key = settings.stripe_secret_key


class StripeService:
    """Service for managing Stripe payments and subscriptions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_customer(self, user: User) -> str:
        """
        Get or create a Stripe Customer for the user.
        
        Returns the Stripe Customer ID.
        """
        if user.stripe_customer_id:
            try:
                # Verify customer still exists in Stripe
                stripe.Customer.retrieve(user.stripe_customer_id)
                return user.stripe_customer_id
            except stripe.error.StripeError:
                # Customer doesn't exist, create new one
                logger.warning(f"Stripe customer {user.stripe_customer_id} not found, creating new")
                user.stripe_customer_id = None

        # Create new Stripe customer
        try:
            customer = stripe.Customer.create(
                email=user.email,
                metadata={
                    "user_id": str(user.id),
                    "account_number": user.account_number or "",
                },
            )
            user.stripe_customer_id = customer.id
            await self.db.commit()
            await self.db.refresh(user)
            logger.info(f"Created Stripe customer {customer.id} for user {user.id}")
            return customer.id
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create Stripe customer for user {user.id}: {e}")
            raise

    async def create_checkout_session(
        self,
        user: User,
        plan: SubscriptionPlan,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None,
    ) -> str:
        """
        Create a Stripe Checkout session for subscription.
        
        Returns the checkout URL.
        """
        if not settings.stripe_secret_key:
            raise ValueError("Stripe not configured")

        # Get or create Stripe customer
        customer_id = await self.get_or_create_customer(user)

        # Get price ID from plan or fallback to config
        price_id = plan.provider_product_id or self._get_price_id_from_config(plan.code)
        if not price_id:
            raise ValueError(f"No Stripe price ID configured for plan {plan.code}")

        # Build URLs
        app_url = settings.app_url.rstrip("/")
        if not success_url:
            success_url = settings.stripe_success_url.format(app_url=app_url)
        if not cancel_url:
            cancel_url = settings.stripe_cancel_url.format(app_url=app_url)

        try:
            checkout_session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=["card"],
                line_items=[
                    {
                        "price": price_id,
                        "quantity": 1,
                    }
                ],
                mode="subscription",
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    "user_id": str(user.id),
                    "plan_code": plan.code,
                },
                subscription_data={
                    "metadata": {
                        "user_id": str(user.id),
                        "plan_code": plan.code,
                    }
                },
            )
            logger.info(f"Created Stripe checkout session {checkout_session.id} for user {user.id}, plan {plan.code}")
            return checkout_session.url
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create Stripe checkout session: {e}")
            raise

    async def create_portal_session(self, user: User, return_url: Optional[str] = None) -> str:
        """
        Create a Stripe Customer Portal session.
        
        Returns the portal URL.
        """
        if not settings.stripe_secret_key:
            raise ValueError("Stripe not configured")

        if not user.stripe_customer_id:
            raise ValueError("User has no Stripe customer ID")

        app_url = settings.app_url.rstrip("/")
        if not return_url:
            return_url = f"{app_url}/billing"

        try:
            portal_session = stripe.billing_portal.Session.create(
                customer=user.stripe_customer_id,
                return_url=return_url,
            )
            logger.info(f"Created Stripe portal session {portal_session.id} for user {user.id}")
            return portal_session.url
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create Stripe portal session: {e}")
            raise

    async def create_one_time_checkout_session(
        self,
        user: User,
        price_id: str,
        quantity: int = 1,
        metadata: Optional[Dict[str, Any]] = None,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None,
    ) -> str:
        """
        Create a Stripe Checkout session for one-time payment (credits, parlay purchases).
        
        Returns the checkout URL.
        """
        if not settings.stripe_secret_key:
            raise ValueError("Stripe not configured")

        customer_id = await self.get_or_create_customer(user)

        app_url = settings.app_url.rstrip("/")
        if not success_url:
            success_url = f"{app_url}/billing/success?provider=stripe"
        if not cancel_url:
            cancel_url = f"{app_url}/billing?canceled=true"

        try:
            checkout_session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=["card"],
                line_items=[
                    {
                        "price": price_id,
                        "quantity": quantity,
                    }
                ],
                mode="payment",
                success_url=success_url,
                cancel_url=cancel_url,
                metadata=metadata or {},
            )
            logger.info(f"Created Stripe one-time checkout session {checkout_session.id} for user {user.id}")
            return checkout_session.url
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create Stripe one-time checkout session: {e}")
            raise

    async def sync_subscription_from_webhook(self, event: Dict[str, Any]) -> None:
        """
        Sync subscription state from Stripe webhook event.
        
        Handles:
        - checkout.session.completed
        - customer.subscription.created
        - customer.subscription.updated
        - customer.subscription.deleted
        - invoice.paid (renewal)
        - invoice.payment_failed
        """
        event_type = event.get("type")
        data = event.get("data", {}).get("object", {})

        if event_type == "checkout.session.completed":
            await self._handle_checkout_completed(data)
        elif event_type == "customer.subscription.created":
            await self._handle_subscription_created(data)
        elif event_type == "customer.subscription.updated":
            await self._handle_subscription_updated(data)
        elif event_type == "customer.subscription.deleted":
            await self._handle_subscription_deleted(data)
        elif event_type == "invoice.paid":
            await self._handle_invoice_paid(data)
        elif event_type == "invoice.payment_failed":
            await self._handle_invoice_payment_failed(data)

    async def _handle_checkout_completed(self, session_data: Dict[str, Any]) -> None:
        """Handle checkout.session.completed event."""
        metadata = session_data.get("metadata", {})
        user_id = metadata.get("user_id")
        if not user_id:
            logger.warning("Checkout completed but no user_id in metadata")
            return

        subscription_id = session_data.get("subscription")
        if subscription_id:
            # Subscription checkout - will be handled by subscription.created event
            logger.info(f"Checkout completed for subscription {subscription_id}, user {user_id}")
        else:
            # One-time payment
            logger.info(f"One-time payment checkout completed for user {user_id}")

    async def _handle_subscription_created(self, subscription_data: Dict[str, Any]) -> None:
        """Handle customer.subscription.created event."""
        subscription_id = subscription_data.get("id")
        customer_id = subscription_data.get("customer")
        metadata = subscription_data.get("metadata", {})
        user_id = metadata.get("user_id")

        if not user_id:
            # Try to find user by customer_id
            result = await self.db.execute(
                select(User).where(User.stripe_customer_id == customer_id)
            )
            user = result.scalar_one_or_none()
            if user:
                user_id = str(user.id)
            else:
                logger.warning(f"Subscription created but no user_id found for customer {customer_id}")
                return

        plan_code = metadata.get("plan_code", "PG_PRO_MONTHLY")

        # Get subscription period
        current_period_start = datetime.fromtimestamp(
            subscription_data.get("current_period_start", 0), tz=timezone.utc
        )
        current_period_end = datetime.fromtimestamp(
            subscription_data.get("current_period_end", 0), tz=timezone.utc
        )

        # Determine status
        status = subscription_data.get("status", "active")
        stripe_status_map = {
            "active": SubscriptionStatus.active.value,
            "trialing": SubscriptionStatus.trialing.value,
            "past_due": SubscriptionStatus.past_due.value,
            "canceled": SubscriptionStatus.cancelled.value,
            "unpaid": SubscriptionStatus.expired.value,
        }
        subscription_status = stripe_status_map.get(status, SubscriptionStatus.active.value)

        # Create or update subscription record
        user_uuid = uuid.UUID(user_id)
        result = await self.db.execute(
            select(Subscription).where(
                and_(
                    Subscription.user_id == user_uuid,
                    Subscription.provider_subscription_id == subscription_id,
                )
            )
        )
        subscription = result.scalar_one_or_none()

        if subscription:
            subscription.status = subscription_status
            subscription.current_period_start = current_period_start
            subscription.current_period_end = current_period_end
            subscription.provider_metadata = subscription_data
        else:
            subscription = Subscription(
                user_id=user_uuid,
                plan=plan_code,
                provider="stripe",
                provider_subscription_id=subscription_id,
                provider_customer_id=customer_id,
                status=subscription_status,
                current_period_start=current_period_start,
                current_period_end=current_period_end,
                provider_metadata=subscription_data,
            )
            self.db.add(subscription)

        # Update user subscription fields
        result = await self.db.execute(select(User).where(User.id == user_uuid))
        user = result.scalar_one_or_none()
        if user:
            user.stripe_subscription_id = subscription_id
            user.subscription_plan = plan_code
            user.subscription_status = subscription_status
            user.subscription_renewal_date = current_period_end
            user.subscription_last_billed_at = current_period_start
            # Reset usage counters on new subscription
            user.premium_ai_parlays_used = 0
            user.premium_ai_parlays_period_start = current_period_start
            user.premium_custom_builder_used = 0
            user.premium_custom_builder_period_start = current_period_start

        await self.db.commit()
        logger.info(f"Created/updated subscription {subscription_id} for user {user_id}")

    async def _handle_subscription_updated(self, subscription_data: Dict[str, Any]) -> None:
        """Handle customer.subscription.updated event."""
        subscription_id = subscription_data.get("id")
        status = subscription_data.get("status", "active")

        stripe_status_map = {
            "active": SubscriptionStatus.active.value,
            "trialing": SubscriptionStatus.trialing.value,
            "past_due": SubscriptionStatus.past_due.value,
            "canceled": SubscriptionStatus.cancelled.value,
            "unpaid": SubscriptionStatus.expired.value,
        }
        subscription_status = stripe_status_map.get(status, SubscriptionStatus.active.value)

        # Update subscription record
        result = await self.db.execute(
            select(Subscription).where(Subscription.provider_subscription_id == subscription_id)
        )
        subscription = result.scalar_one_or_none()

        if subscription:
            subscription.status = subscription_status
            subscription.current_period_start = datetime.fromtimestamp(
                subscription_data.get("current_period_start", 0), tz=timezone.utc
            )
            subscription.current_period_end = datetime.fromtimestamp(
                subscription_data.get("current_period_end", 0), tz=timezone.utc
            )
            subscription.cancel_at_period_end = subscription_data.get("cancel_at_period_end", False)
            subscription.provider_metadata = subscription_data

            # Update user
            result = await self.db.execute(select(User).where(User.id == subscription.user_id))
            user = result.scalar_one_or_none()
            if user:
                user.subscription_status = subscription_status
                user.subscription_renewal_date = subscription.current_period_end

            await self.db.commit()
            logger.info(f"Updated subscription {subscription_id} to status {subscription_status}")

    async def _handle_subscription_deleted(self, subscription_data: Dict[str, Any]) -> None:
        """Handle customer.subscription.deleted event."""
        subscription_id = subscription_data.get("id")

        result = await self.db.execute(
            select(Subscription).where(Subscription.provider_subscription_id == subscription_id)
        )
        subscription = result.scalar_one_or_none()

        if subscription:
            subscription.status = SubscriptionStatus.cancelled.value
            subscription.cancelled_at = datetime.now(timezone.utc)
            subscription.cancel_at_period_end = False

            # Update user
            result = await self.db.execute(select(User).where(User.id == subscription.user_id))
            user = result.scalar_one_or_none()
            if user:
                user.subscription_status = SubscriptionStatus.cancelled.value

            await self.db.commit()
            logger.info(f"Deleted subscription {subscription_id}")

    async def _handle_invoice_paid(self, invoice_data: Dict[str, Any]) -> None:
        """Handle invoice.paid event (subscription renewal)."""
        subscription_id = invoice_data.get("subscription")
        if not subscription_id:
            return

        result = await self.db.execute(
            select(Subscription).where(Subscription.provider_subscription_id == subscription_id)
        )
        subscription = result.scalar_one_or_none()

        if subscription:
            # Reset usage counters on renewal
            result = await self.db.execute(select(User).where(User.id == subscription.user_id))
            user = result.scalar_one_or_none()
            if user:
                user.premium_ai_parlays_used = 0
                user.premium_ai_parlays_period_start = subscription.current_period_start
                user.premium_custom_builder_used = 0
                user.premium_custom_builder_period_start = subscription.current_period_start
                user.subscription_last_billed_at = datetime.now(timezone.utc)

            await self.db.commit()
            logger.info(f"Invoice paid for subscription {subscription_id}, reset usage counters")

    async def _handle_invoice_payment_failed(self, invoice_data: Dict[str, Any]) -> None:
        """Handle invoice.payment_failed event."""
        subscription_id = invoice_data.get("subscription")
        if not subscription_id:
            return

        result = await self.db.execute(
            select(Subscription).where(Subscription.provider_subscription_id == subscription_id)
        )
        subscription = result.scalar_one_or_none()

        if subscription:
            subscription.status = SubscriptionStatus.past_due.value

            result = await self.db.execute(select(User).where(User.id == subscription.user_id))
            user = result.scalar_one_or_none()
            if user:
                user.subscription_status = SubscriptionStatus.past_due.value

            await self.db.commit()
            logger.info(f"Payment failed for subscription {subscription_id}")

    def _get_price_id_from_config(self, plan_code: str) -> Optional[str]:
        """Get Stripe price ID from config based on plan code."""
        if plan_code == "PG_PRO_MONTHLY" or "monthly" in plan_code.lower():
            return settings.stripe_price_id_pro_monthly
        elif plan_code == "PG_PRO_ANNUAL" or "annual" in plan_code.lower():
            return settings.stripe_price_id_pro_annual
        return None

