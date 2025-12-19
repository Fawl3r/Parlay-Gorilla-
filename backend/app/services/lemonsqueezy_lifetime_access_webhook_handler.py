"""
LemonSqueezy lifetime access (card) webhook handling.

Lifetime card purchases are one-time orders (order_created/order_completed) and
must be converted into a lifetime Subscription record in our DB.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from datetime import timezone
import logging
import uuid

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.webhooks.shared_handlers import _handle_affiliate_commission
from app.models.affiliate_commission import CommissionSaleType, CommissionSettlementProvider
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.user import SubscriptionStatusEnum, User
from app.utils.datetime_utils import now_utc

logger = logging.getLogger(__name__)


@dataclass
class LemonSqueezyLifetimeAccessWebhookHandler:
    db: AsyncSession

    async def handle(self, payload: dict, user_id: str | None = None) -> None:
        """
        Grant lifetime access for a one-time LemonSqueezy order.

        Idempotent by order id (data.id).
        """
        data = payload.get("data", {})
        attributes = data.get("attributes", {}) or {}
        order_id = str(data.get("id", "")).strip()

        if not order_id:
            logger.warning("LemonSqueezy lifetime order missing data.id")
            return

        # Idempotency: a single order can produce multiple webhook events.
        existing = await self.db.execute(
            select(Subscription.id).where(
                and_(
                    Subscription.provider == "lemonsqueezy",
                    Subscription.provider_subscription_id == order_id,
                )
            )
        )
        if existing.scalar_one_or_none():
            logger.info("LemonSqueezy lifetime order already processed: %s", order_id)
            return

        # Find user if not provided.
        if not user_id:
            email = attributes.get("user_email") or attributes.get("customer_email") or attributes.get("email")
            if email:
                result = await self.db.execute(select(User).where(User.email == email))
                user = result.scalar_one_or_none()
                if user:
                    user_id = str(user.id)

        if not user_id:
            logger.warning("LemonSqueezy lifetime order: Could not find user")
            return

        # Extract plan_code from custom data (preferred) or fallback.
        meta = payload.get("meta", {}) or {}
        custom_data = meta.get("custom_data", {}) or {}
        plan_code = custom_data.get("plan_code") or "PG_LIFETIME_CARD"

        now = now_utc()

        subscription = Subscription(
            id=uuid.uuid4(),
            user_id=uuid.UUID(user_id),
            plan=plan_code,
            provider="lemonsqueezy",
            provider_subscription_id=order_id,
            provider_customer_id=str(attributes.get("customer_id") or ""),
            status=SubscriptionStatus.active.value,
            current_period_start=now,
            current_period_end=None,  # Lifetime = no end
            is_lifetime=True,
            provider_metadata=attributes,
        )
        self.db.add(subscription)

        # Update user subscription fields.
        result = await self.db.execute(select(User).where(User.id == uuid.UUID(user_id)))
        user = result.scalar_one_or_none()
        if user:
            user.plan = "elite"  # Lifetime = elite tier
            user.subscription_plan = plan_code
            user.subscription_status = SubscriptionStatusEnum.active.value
            user.subscription_renewal_date = None
            user.subscription_last_billed_at = now
            user.daily_parlays_used = 0

        # Affiliate commission (treat as a subscription sale).
        try:
            price = Decimal(str(attributes.get("total", 0))) / 100  # cents → dollars
        except Exception:
            price = Decimal("0")
        if price > 0:
            await _handle_affiliate_commission(
                db=self.db,
                user_id=user_id,
                sale_type=CommissionSaleType.SUBSCRIPTION.value,
                sale_amount=price,
                sale_id=order_id,
                settlement_provider=CommissionSettlementProvider.LEMONSQUEEZY.value,
                is_first_subscription=True,
                subscription_plan=plan_code,
            )

        logger.info("Granted lifetime access via LemonSqueezy order %s for user %s", order_id, user_id)


