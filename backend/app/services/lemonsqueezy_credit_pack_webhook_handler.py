"""
LemonSqueezy credit pack webhook handling.

Credit packs are fulfilled on order events and award credits to the user.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import logging

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.webhooks.shared_handlers import _handle_credit_pack_purchase
from app.models.user import User
from app.services.auth import EmailNormalizer

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
                normalized_email = EmailNormalizer().normalize(str(email))
                user = None
                if normalized_email:
                    result = await self.db.execute(select(User).where(func.lower(User.email) == normalized_email))
                    user = result.scalar_one_or_none()
                if user:
                    user_id = str(user.id)

        if not user_id:
            logger.warning("LemonSqueezy credit pack purchase: Could not find user")
            return

        # Get custom data from multiple possible locations (orders vs subscriptions)
        # For one-time orders, custom_data is often in attributes.custom
        # For subscriptions, it's in first_subscription_item.custom_data
        custom_data = {}
        
        # Try order-level custom data first (for one-time purchases)
        if attributes.get("custom"):
            try:
                custom_data = json.loads(attributes["custom"]) if isinstance(attributes["custom"], str) else attributes["custom"]
            except (json.JSONDecodeError, TypeError):
                custom_data = attributes.get("custom", {}) or {}
        
        # Fallback to subscription item custom_data
        if not custom_data.get("credit_pack_id"):
            custom_data = attributes.get("first_subscription_item", {}).get("custom_data", {}) or {}
        
        # Fallback to order items custom_data
        if not custom_data.get("credit_pack_id"):
            order_items = attributes.get("order_items", {}).get("data", []) or []
            for item in order_items:
                item_attrs = item.get("attributes", {}) or {}
                item_custom = item_attrs.get("custom_data", {}) or {}
                if item_custom.get("credit_pack_id"):
                    custom_data = item_custom
                    break
        
        # Final fallback to meta.custom_data
        if not custom_data.get("credit_pack_id"):
            meta = payload.get("meta", {}) or {}
            custom_data = meta.get("custom_data", {}) or {}

        credit_pack_id = custom_data.get("credit_pack_id")
        if not credit_pack_id:
            event_name = payload.get("meta", {}).get("event_name", "unknown")
            order_id = data.get("id", "unknown")
            logger.error(
                f"LemonSqueezy credit pack purchase: No credit_pack_id in payload. "
                f"Event: {event_name}, Order ID: {order_id}, User ID: {user_id}. "
                f"Checked attributes.custom, first_subscription_item, order_items, and meta.custom_data. "
                f"Available keys in custom_data: {list(custom_data.keys()) if custom_data else 'none'}"
            )
            # Don't raise exception - let webhook route handle it, but log as error for visibility
            return

        sale_id = str(data.get("id", ""))
        if not sale_id:
            logger.error(f"LemonSqueezy credit pack purchase: Missing order ID in payload data")
            return
            
        try:
            await _handle_credit_pack_purchase(self.db, user_id, credit_pack_id, sale_id, "lemonsqueezy")
            logger.info(
                f"Successfully processed credit pack purchase: user_id={user_id}, "
                f"pack_id={credit_pack_id}, order_id={sale_id}"
            )
        except Exception as e:
            logger.error(
                f"Error processing credit pack purchase: user_id={user_id}, "
                f"pack_id={credit_pack_id}, order_id={sale_id}, error={e}",
                exc_info=True
            )
            raise  # Re-raise so webhook route can mark event as failed


