"""
LemonSqueezy credit pack webhook handling.

Credit packs are fulfilled on order events and award credits to the user.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.webhooks.shared_handlers import _handle_credit_pack_purchase
from app.models.user import User

logger = logging.getLogger(__name__)


@dataclass
class LemonSqueezyCreditPackWebhookHandler:
    db: AsyncSession

    async def handle(self, payload: dict, user_id: str | None) -> None:
        """Handle LemonSqueezy credit pack purchase (order_created/order_completed)."""
        data = payload.get("data", {})
        attributes = data.get("attributes", {}) or {}

        # Find user if missing in custom_data (best-effort fallback).
        if not user_id:
            email = attributes.get("user_email") or attributes.get("customer_email") or attributes.get("email")
            if email:
                result = await self.db.execute(select(User).where(User.email == email))
                user = result.scalar_one_or_none()
                if user:
                    user_id = str(user.id)

        if not user_id:
            logger.warning("LemonSqueezy credit pack purchase: Could not find user")
            return

        # Get custom data (prefer subscription_item custom_data; fallback to meta.custom_data).
        custom_data = attributes.get("first_subscription_item", {}).get("custom_data", {}) or {}
        if not custom_data:
            meta = payload.get("meta", {}) or {}
            custom_data = meta.get("custom_data", {}) or {}

        credit_pack_id = custom_data.get("credit_pack_id")
        if not credit_pack_id:
            logger.warning("LemonSqueezy credit pack purchase: No credit_pack_id in payload")
            return

        sale_id = str(data.get("id", ""))
        await _handle_credit_pack_purchase(self.db, user_id, credit_pack_id, sale_id, "lemonsqueezy")


