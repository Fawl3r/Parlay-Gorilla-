"""
LemonSqueezy recurring payment webhook handling.

Handles:
- subscription_payment_success (recurring charge succeeded)
- subscription_payment_failed (recurring charge failed)
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime, timezone
import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.webhooks.shared_handlers import _handle_affiliate_commission
from app.models.affiliate_commission import CommissionSaleType, CommissionSettlementProvider
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.user import User

logger = logging.getLogger(__name__)


@dataclass
class LemonSqueezyRecurringPaymentWebhookHandler:
    db: AsyncSession

    async def handle_payment_success(self, payload: dict) -> None:
        """Handle successful LemonSqueezy recurring payment."""
        data = payload.get("data", {})
        attributes = data.get("attributes", {}) or {}
        subscription_id = str(data.get("id", ""))

        # Get custom data
        custom_data = attributes.get("first_subscription_item", {}).get("custom_data", {}) or {}
        user_id = custom_data.get("user_id")
        plan_code = custom_data.get("plan_code")

        # Find subscription if user_id not in custom data
        if not user_id:
            result = await self.db.execute(select(Subscription).where(Subscription.provider_subscription_id == subscription_id))
            subscription = result.scalar_one_or_none()
            if subscription:
                user_id = str(subscription.user_id)
                plan_code = subscription.plan

        if not user_id:
            logger.warning("LemonSqueezy payment_success: Could not find user")
            return

        # Get payment amount
        price = Decimal(str(attributes.get("total", 0))) / 100
        if price <= 0:
            price_data = attributes.get("first_subscription_item", {}) or {}
            price = Decimal(str(price_data.get("price", 0))) / 100

        # Update user's last billed date
        result = await self.db.execute(select(User).where(User.id == uuid.UUID(user_id)))
        user = result.scalar_one_or_none()
        if user:
            user.subscription_last_billed_at = datetime.now(timezone.utc)

        # Handle affiliate commission for recurring payment
        if price > 0:
            await _handle_affiliate_commission(
                db=self.db,
                user_id=user_id,
                sale_type=CommissionSaleType.SUBSCRIPTION.value,
                sale_amount=price,
                sale_id=f"{subscription_id}_{datetime.now(timezone.utc).strftime('%Y%m%d')}",
                settlement_provider=CommissionSettlementProvider.LEMONSQUEEZY.value,
                is_first_subscription=False,
                subscription_plan=plan_code,
            )

        logger.info("LemonSqueezy recurring payment success for user %s", user_id)

    async def handle_payment_failed(self, payload: dict) -> None:
        """Handle failed LemonSqueezy payment."""
        data = payload.get("data", {})
        subscription_id = str(data.get("id", ""))

        result = await self.db.execute(select(Subscription).where(Subscription.provider_subscription_id == subscription_id))
        subscription = result.scalar_one_or_none()
        if subscription:
            subscription.status = SubscriptionStatus.past_due.value

        logger.warning("LemonSqueezy payment failed for subscription %s", subscription_id)


