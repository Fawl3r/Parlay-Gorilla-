"""
Stripe Service facade.

This module stays small (<500 LOC) and composes focused Stripe modules:
- Customer + checkout/portal session creation
- Subscription lifecycle sync from webhooks

External callers should continue importing `StripeService` from this path.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import stripe
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.subscription_plan import SubscriptionPlan
from app.models.user import User
from app.services.stripe.stripe_checkout_manager import StripeCheckoutManager
from app.services.stripe.stripe_subscription_sync import StripeSubscriptionSync

logger = logging.getLogger(__name__)


class StripeService:
    """Facade for Stripe billing operations."""

    def __init__(self, db: AsyncSession):
        self._db = db
        self._checkout = StripeCheckoutManager(db)
        self._sync = StripeSubscriptionSync(db)

        if settings.stripe_secret_key:
            stripe.api_key = settings.stripe_secret_key

    # ------------------------------------------------------------------
    # Customer / checkout / portal
    # ------------------------------------------------------------------

    async def get_or_create_customer(self, user: User) -> str:
        return await self._checkout.get_or_create_customer(user)

    async def create_checkout_session(
        self,
        user: User,
        plan: SubscriptionPlan,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None,
    ) -> str:
        return await self._checkout.create_checkout_session(
            user=user,
            plan=plan,
            success_url=success_url,
            cancel_url=cancel_url,
        )

    async def create_one_time_checkout_session(
        self,
        user: User,
        price_id: str,
        quantity: int = 1,
        metadata: Optional[Dict[str, Any]] = None,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None,
    ) -> str:
        return await self._checkout.create_one_time_checkout_session(
            user=user,
            price_id=price_id,
            quantity=quantity,
            metadata=metadata,
            success_url=success_url,
            cancel_url=cancel_url,
        )

    async def create_portal_session(self, user: User, return_url: Optional[str] = None) -> str:
        return await self._checkout.create_portal_session(user=user, return_url=return_url)

    async def cancel_subscription(self, subscription_id: str) -> Dict[str, Any]:
        if not settings.stripe_secret_key:
            raise ValueError("Stripe not configured")

        subscription_id = (subscription_id or "").strip()
        if not subscription_id:
            raise ValueError("subscription_id is required")

        try:
            subscription = stripe.Subscription.modify(subscription_id, cancel_at_period_end=True)
            logger.info("Cancelled Stripe subscription %s at period end", subscription_id)
            return dict(subscription or {})
        except stripe.error.StripeError as exc:
            logger.error("Failed to cancel Stripe subscription %s: %s", subscription_id, exc)
            raise

    # ------------------------------------------------------------------
    # Webhook sync
    # ------------------------------------------------------------------

    async def sync_subscription_from_webhook(self, event: Dict[str, Any]) -> None:
        await self._sync.sync_from_webhook(event)

    # The reconciliation flow uses these internal handlers directly.
    async def _handle_subscription_created(self, subscription_data: Dict[str, Any]) -> None:
        await self._sync.handle_subscription_created(subscription_data)

    async def _handle_subscription_updated(self, subscription_data: Dict[str, Any]) -> None:
        await self._sync.handle_subscription_updated(subscription_data)


