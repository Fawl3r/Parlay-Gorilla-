"""
Stripe checkout management (customer + checkout/portal sessions).

Kept separate from webhook sync so each file stays <500 LOC.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import stripe
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.subscription_plan import SubscriptionPlan
from app.models.user import User

logger = logging.getLogger(__name__)


class StripeCheckoutManager:
    def __init__(self, db: AsyncSession):
        self._db = db
        if settings.stripe_secret_key:
            stripe.api_key = settings.stripe_secret_key

    async def get_or_create_customer(self, user: User) -> str:
        if user.stripe_customer_id:
            try:
                stripe.Customer.retrieve(user.stripe_customer_id)
                return user.stripe_customer_id
            except stripe.error.StripeError:
                logger.warning("Stripe customer %s not found, creating new", user.stripe_customer_id)
                user.stripe_customer_id = None

        try:
            customer = stripe.Customer.create(
                email=user.email,
                metadata={
                    "user_id": str(user.id),
                    "account_number": user.account_number or "",
                },
            )
            user.stripe_customer_id = customer.id
            await self._db.commit()
            await self._db.refresh(user)
            logger.info("Created Stripe customer %s for user %s", customer.id, user.id)
            return customer.id
        except stripe.error.StripeError as exc:
            logger.error("Failed to create Stripe customer for user %s: %s", user.id, exc)
            raise

    async def create_checkout_session(
        self,
        *,
        user: User,
        plan: SubscriptionPlan,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None,
    ) -> str:
        if not settings.stripe_secret_key:
            raise ValueError("Stripe not configured")

        customer_id = await self.get_or_create_customer(user)

        price_id = plan.provider_product_id or self._get_price_id_from_config(plan.code)
        if not price_id:
            raise ValueError(f"No Stripe price ID configured for plan {plan.code}")

        app_url = settings.app_url.rstrip("/")
        if not success_url:
            success_url = settings.stripe_success_url.format(app_url=app_url)
        success_url = self._with_checkout_session_id(success_url)
        if not cancel_url:
            cancel_url = settings.stripe_cancel_url.format(app_url=app_url)

        is_lifetime = plan.is_lifetime if hasattr(plan, "is_lifetime") else (
            plan.billing_cycle == "lifetime" if hasattr(plan, "billing_cycle") else False
        )
        checkout_mode = "payment" if is_lifetime else "subscription"

        metadata: Dict[str, Any] = {"user_id": str(user.id), "plan_code": plan.code}
        if is_lifetime:
            metadata["purchase_type"] = "lifetime_subscription"

        checkout_params: Dict[str, Any] = {
            "customer": customer_id,
            "payment_method_types": ["card"],
            "line_items": [{"price": price_id, "quantity": 1}],
            "mode": checkout_mode,
            "success_url": success_url,
            "cancel_url": cancel_url,
            "metadata": metadata,
        }

        if checkout_mode == "subscription":
            checkout_params["subscription_data"] = {
                "metadata": {"user_id": str(user.id), "plan_code": plan.code}
            }

        try:
            checkout_session = stripe.checkout.Session.create(**checkout_params)
            logger.info(
                "Created Stripe checkout session %s for user %s, plan %s",
                checkout_session.id,
                user.id,
                plan.code,
            )
            return checkout_session.url
        except stripe.error.StripeError as exc:
            logger.error("Failed to create Stripe checkout session: %s", exc)
            raise

    async def create_portal_session(self, *, user: User, return_url: Optional[str] = None) -> str:
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
            logger.info("Created Stripe portal session %s for user %s", portal_session.id, user.id)
            return portal_session.url
        except stripe.error.StripeError as exc:
            logger.error("Failed to create Stripe portal session: %s", exc)
            raise

    async def create_one_time_checkout_session(
        self,
        *,
        user: User,
        price_id: str,
        quantity: int = 1,
        metadata: Optional[Dict[str, Any]] = None,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None,
    ) -> str:
        if not settings.stripe_secret_key:
            raise ValueError("Stripe not configured")

        customer_id = await self.get_or_create_customer(user)

        app_url = settings.app_url.rstrip("/")
        if not success_url:
            success_url = f"{app_url}/billing/success?provider=stripe"
        success_url = self._with_checkout_session_id(success_url)
        if not cancel_url:
            cancel_url = f"{app_url}/billing?canceled=true"

        try:
            checkout_session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=["card"],
                line_items=[{"price": price_id, "quantity": quantity}],
                mode="payment",
                success_url=success_url,
                cancel_url=cancel_url,
                metadata=metadata or {},
            )
            logger.info("Created Stripe one-time checkout session %s for user %s", checkout_session.id, user.id)
            return checkout_session.url
        except stripe.error.StripeError as exc:
            logger.error("Failed to create Stripe one-time checkout session: %s", exc)
            raise

    def _get_price_id_from_config(self, plan_code: str) -> Optional[str]:
        if plan_code == "PG_PRO_MONTHLY" or "monthly" in plan_code.lower():
            return settings.stripe_price_id_pro_monthly
        if plan_code == "PG_PRO_ANNUAL" or "annual" in plan_code.lower():
            return settings.stripe_price_id_pro_annual
        if plan_code == "PG_LIFETIME_CARD" or "lifetime" in plan_code.lower():
            return settings.stripe_price_id_pro_lifetime
        return None

    @staticmethod
    def _with_checkout_session_id(success_url: str) -> str:
        url = (success_url or "").strip()
        if not url:
            return url
        if "{CHECKOUT_SESSION_ID}" in url:
            return url
        separator = "&" if "?" in url else "?"
        return f"{url}{separator}session_id={{CHECKOUT_SESSION_ID}}"


