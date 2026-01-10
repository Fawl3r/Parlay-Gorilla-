"""
Stripe subscription sync from webhook payloads.

Contains the DB upsert/update logic for Stripe subscription lifecycle events.
Separated from checkout creation to keep files <500 LOC.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscription import Subscription, SubscriptionStatus
from app.models.subscription_plan import SubscriptionPlan
from app.models.user import SubscriptionStatusEnum, User

logger = logging.getLogger(__name__)


def _ts_to_dt(value: object) -> Optional[datetime]:
    try:
        ts = int(value or 0)
    except Exception:
        ts = 0
    if ts <= 0:
        return None
    return datetime.fromtimestamp(ts, tz=timezone.utc)


class StripeSubscriptionSync:
    def __init__(self, db: AsyncSession):
        self._db = db

    @staticmethod
    def _extract_primary_price_id(subscription_data: Dict[str, Any]) -> Optional[str]:
        """
        Best-effort extraction of the active price ID from a Stripe subscription payload.

        Notes:
        - Stripe includes subscription items under `items.data[].price.id` (modern) or `items.data[].plan.id` (legacy).
        - For our plans we expect a single primary item; we return the first price id we can find.
        """
        items_obj = subscription_data.get("items") or {}
        items = items_obj.get("data") if isinstance(items_obj, dict) else None
        if not isinstance(items, list):
            return None

        for item in items:
            if not isinstance(item, dict):
                continue
            price = item.get("price") or {}
            if isinstance(price, dict):
                pid = price.get("id")
                if pid:
                    return str(pid).strip()

            plan = item.get("plan") or {}
            if isinstance(plan, dict):
                pid = plan.get("id")
                if pid:
                    return str(pid).strip()

        return None

    async def _resolve_plan_code(self, *, subscription_data: Dict[str, Any], fallback: str) -> str:
        """
        Resolve our internal plan code for a Stripe subscription payload.

        We prefer looking up the Stripe price id in `subscription_plans` to support portal plan changes,
        and fall back to the provided plan code when the lookup fails.
        """
        price_id = self._extract_primary_price_id(subscription_data)
        if not price_id:
            return fallback

        result = await self._db.execute(
            select(SubscriptionPlan).where(
                and_(
                    SubscriptionPlan.provider == "stripe",
                    SubscriptionPlan.is_active == True,
                    or_(
                        SubscriptionPlan.provider_price_id == price_id,
                        SubscriptionPlan.provider_product_id == price_id,
                    ),
                )
            )
        )
        plan = result.scalar_one_or_none()
        return str(plan.code) if plan else fallback

    @staticmethod
    def _normalize_user_status(*, subscription_status: str, existing: Optional[str] = None) -> str:
        """
        Normalize provider-level subscription status into `User.subscription_status` values.

        The user table uses a simplified status set (active/canceled/expired/none). For access
        purposes we treat trialing/past_due as active.
        """
        s = (subscription_status or "").strip().lower()
        if not s:
            return existing or SubscriptionStatusEnum.none.value

        if s in {SubscriptionStatus.active.value, SubscriptionStatus.trialing.value, SubscriptionStatus.past_due.value}:
            return SubscriptionStatusEnum.active.value

        if s in {SubscriptionStatus.cancelled.value, "canceled", "cancelled"}:
            return SubscriptionStatusEnum.canceled.value

        if s in {SubscriptionStatus.expired.value, SubscriptionStatus.paused.value, "expired"}:
            return SubscriptionStatusEnum.expired.value

        return existing or SubscriptionStatusEnum.none.value

    async def sync_from_webhook(self, event: Dict[str, Any]) -> None:
        event_type = event.get("type")
        data = event.get("data", {}).get("object", {})

        if event_type == "checkout.session.completed":
            await self.handle_checkout_completed(data)
        elif event_type == "customer.subscription.created":
            await self.handle_subscription_created(data)
        elif event_type == "customer.subscription.updated":
            await self.handle_subscription_updated(data)
        elif event_type == "customer.subscription.deleted":
            await self.handle_subscription_deleted(data)
        elif event_type == "invoice.paid":
            await self.handle_invoice_paid(data)
        elif event_type == "invoice.payment_failed":
            await self.handle_invoice_payment_failed(data)

    async def handle_checkout_completed(self, session_data: Dict[str, Any]) -> None:
        metadata = session_data.get("metadata", {})
        user_id = metadata.get("user_id")
        if not user_id:
            logger.warning("Checkout completed but no user_id in metadata")
            return

        subscription_id = session_data.get("subscription")
        if subscription_id:
            logger.info("Checkout completed for subscription %s, user %s", subscription_id, user_id)
        else:
            logger.info("One-time payment checkout completed for user %s", user_id)

    async def handle_subscription_created(self, subscription_data: Dict[str, Any]) -> None:
        subscription_id = subscription_data.get("id")
        customer_id = subscription_data.get("customer")
        metadata = subscription_data.get("metadata", {})
        user_id = metadata.get("user_id")
        status = (subscription_data.get("status") or "active").strip().lower()

        logger.info(
            "Processing subscription.created: subscription_id=%s customer_id=%s user_id=%s status=%s",
            subscription_id,
            customer_id,
            user_id,
            status,
        )

        if not user_id:
            result = await self._db.execute(select(User).where(User.stripe_customer_id == customer_id))
            user = result.scalar_one_or_none()
            if user:
                user_id = str(user.id)
                logger.info("Found user %s by customer_id %s", user_id, customer_id)
            else:
                logger.warning("Subscription created but no user_id found for customer %s. metadata=%s", customer_id, metadata)
                return

        if status not in {"active", "trialing"}:
            if status == "incomplete":
                logger.info(
                    "Subscription %s created as incomplete for user %s (payment processing). Waiting for activation.",
                    subscription_id,
                    user_id,
                )
            else:
                logger.warning(
                    "Subscription %s created with status '%s' for user %s; not activating until active/trialing.",
                    subscription_id,
                    status,
                    user_id,
                )
            return

        plan_code_fallback = str(metadata.get("plan_code") or "PG_PRO_MONTHLY").strip()
        plan_code = await self._resolve_plan_code(subscription_data=subscription_data, fallback=plan_code_fallback)
        current_period_start = _ts_to_dt(subscription_data.get("current_period_start"))
        current_period_end = _ts_to_dt(subscription_data.get("current_period_end"))

        subscription_status = self._map_status(status, existing=SubscriptionStatus.active.value)

        user_uuid = uuid.UUID(user_id)
        result = await self._db.execute(
            select(Subscription).where(
                and_(
                    Subscription.user_id == user_uuid,
                    Subscription.provider_subscription_id == subscription_id,
                )
            )
        )
        sub = result.scalar_one_or_none()

        if sub:
            sub.status = subscription_status
            sub.plan = plan_code
            sub.current_period_start = current_period_start
            sub.current_period_end = current_period_end
            sub.provider_metadata = subscription_data
        else:
            sub = Subscription(
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
            self._db.add(sub)

        user_row = (await self._db.execute(select(User).where(User.id == user_uuid))).scalar_one_or_none()
        if user_row:
            user_row.stripe_subscription_id = subscription_id
            user_row.subscription_plan = plan_code
            user_row.subscription_status = self._normalize_user_status(subscription_status=subscription_status, existing=user_row.subscription_status)
            user_row.subscription_renewal_date = current_period_end
            user_row.subscription_last_billed_at = current_period_start
            user_row.premium_ai_parlays_used = 0
            user_row.premium_ai_parlays_period_start = current_period_start
            user_row.premium_custom_builder_used = 0
            user_row.premium_custom_builder_period_start = current_period_start

        await self._db.commit()
        logger.info(
            "✅ Subscription ACTIVATED: subscription=%s user=%s plan=%s status=%s",
            subscription_id,
            user_id,
            plan_code,
            subscription_status,
        )

    async def handle_subscription_updated(self, subscription_data: Dict[str, Any]) -> None:
        subscription_id = subscription_data.get("id")
        customer_id = subscription_data.get("customer")
        metadata = subscription_data.get("metadata", {}) or {}
        user_id = metadata.get("user_id")
        status = (subscription_data.get("status") or "active").strip().lower()

        logger.info(
            "Processing subscription.updated: subscription_id=%s status=%s user_id=%s",
            subscription_id,
            status,
            user_id,
        )

        mapped_status = self._map_status(status, existing=None)

        result = await self._db.execute(select(Subscription).where(Subscription.provider_subscription_id == subscription_id))
        sub = result.scalar_one_or_none()

        if sub:
            subscription_status = mapped_status or sub.status
            sub.status = subscription_status
            sub.current_period_start = _ts_to_dt(subscription_data.get("current_period_start")) or sub.current_period_start
            sub.current_period_end = _ts_to_dt(subscription_data.get("current_period_end")) or sub.current_period_end
            sub.cancel_at_period_end = bool(subscription_data.get("cancel_at_period_end", False))
            sub.provider_metadata = subscription_data

            plan_code_fallback = str(metadata.get("plan_code") or sub.plan or "PG_PRO_MONTHLY").strip()
            resolved_plan_code = await self._resolve_plan_code(subscription_data=subscription_data, fallback=plan_code_fallback)
            if resolved_plan_code:
                sub.plan = resolved_plan_code

            user_row = (await self._db.execute(select(User).where(User.id == sub.user_id))).scalar_one_or_none()
            if user_row:
                user_row.subscription_status = self._normalize_user_status(subscription_status=subscription_status, existing=user_row.subscription_status)
                user_row.subscription_renewal_date = sub.current_period_end

                if resolved_plan_code:
                    user_row.subscription_plan = resolved_plan_code

                # Avoid creating a second Stripe subscription. If a status update indicates the user
                # still has access (active/trialing/past_due), keep the subscription fields fresh.
                if status in {"active", "trialing", "past_due", "incomplete"}:
                    user_row.stripe_subscription_id = subscription_id
                    if sub.current_period_start:
                        user_row.premium_ai_parlays_used = 0
                        user_row.premium_ai_parlays_period_start = sub.current_period_start
                        user_row.premium_custom_builder_used = 0
                        user_row.premium_custom_builder_period_start = sub.current_period_start

            await self._db.commit()
            logger.info("Updated subscription %s to status %s", subscription_id, subscription_status)
            return

        # If we don't have a subscription row yet, attempt to create when it becomes active/trialing.
        if not user_id and customer_id:
            user_row = (await self._db.execute(select(User).where(User.stripe_customer_id == customer_id))).scalar_one_or_none()
            if user_row:
                user_id = str(user_row.id)

        if not user_id or status not in {"active", "trialing"}:
            return

        plan_code = metadata.get("plan_code", "PG_PRO_MONTHLY")
        user_uuid = uuid.UUID(user_id)
        subscription_status = mapped_status or SubscriptionStatus.active.value

        sub = Subscription(
            user_id=user_uuid,
            plan=plan_code,
            provider="stripe",
            provider_subscription_id=subscription_id,
            provider_customer_id=customer_id,
            status=subscription_status,
            current_period_start=_ts_to_dt(subscription_data.get("current_period_start")),
            current_period_end=_ts_to_dt(subscription_data.get("current_period_end")),
            provider_metadata=subscription_data,
        )
        self._db.add(sub)

        user_row = (await self._db.execute(select(User).where(User.id == user_uuid))).scalar_one_or_none()
        if user_row:
            user_row.stripe_subscription_id = subscription_id
            user_row.subscription_plan = plan_code
            user_row.subscription_status = self._normalize_user_status(subscription_status=subscription_status, existing=user_row.subscription_status)
            user_row.subscription_renewal_date = sub.current_period_end
            user_row.subscription_last_billed_at = sub.current_period_start
            user_row.premium_ai_parlays_used = 0
            user_row.premium_ai_parlays_period_start = sub.current_period_start
            user_row.premium_custom_builder_used = 0
            user_row.premium_custom_builder_period_start = sub.current_period_start

        await self._db.commit()
        logger.info(
            "✅ Subscription CREATED & ACTIVATED via update: subscription=%s user=%s plan=%s status=%s",
            subscription_id,
            user_id,
            plan_code,
            subscription_status,
        )

    async def handle_subscription_deleted(self, subscription_data: Dict[str, Any]) -> None:
        subscription_id = subscription_data.get("id")

        result = await self._db.execute(select(Subscription).where(Subscription.provider_subscription_id == subscription_id))
        sub = result.scalar_one_or_none()
        if not sub:
            return

        sub.status = SubscriptionStatus.cancelled.value
        sub.cancelled_at = datetime.now(timezone.utc)
        sub.cancel_at_period_end = False

        user_row = (await self._db.execute(select(User).where(User.id == sub.user_id))).scalar_one_or_none()
        if user_row:
            user_row.subscription_status = SubscriptionStatusEnum.canceled.value

        await self._db.commit()
        logger.info("Deleted subscription %s", subscription_id)

    async def handle_invoice_paid(self, invoice_data: Dict[str, Any]) -> None:
        subscription_id = invoice_data.get("subscription")
        if not subscription_id:
            return

        sub = (await self._db.execute(select(Subscription).where(Subscription.provider_subscription_id == subscription_id))).scalar_one_or_none()
        if not sub:
            return

        user_row = (await self._db.execute(select(User).where(User.id == sub.user_id))).scalar_one_or_none()
        if user_row:
            user_row.premium_ai_parlays_used = 0
            user_row.premium_ai_parlays_period_start = sub.current_period_start
            user_row.premium_custom_builder_used = 0
            user_row.premium_custom_builder_period_start = sub.current_period_start
            user_row.subscription_last_billed_at = datetime.now(timezone.utc)

        await self._db.commit()
        logger.info("Invoice paid for subscription %s, reset usage counters", subscription_id)

    async def handle_invoice_payment_failed(self, invoice_data: Dict[str, Any]) -> None:
        subscription_id = invoice_data.get("subscription")
        if not subscription_id:
            return

        sub = (await self._db.execute(select(Subscription).where(Subscription.provider_subscription_id == subscription_id))).scalar_one_or_none()
        if not sub:
            return

        sub.status = SubscriptionStatus.past_due.value

        user_row = (await self._db.execute(select(User).where(User.id == sub.user_id))).scalar_one_or_none()
        if user_row:
            # Keep access during billing issues; the UI can reflect past_due based on the Subscription row.
            user_row.subscription_status = SubscriptionStatusEnum.active.value

        await self._db.commit()
        logger.info("Payment failed for subscription %s", subscription_id)

    @staticmethod
    def _map_status(status_value: str, *, existing: Optional[str]) -> Optional[str]:
        s = (status_value or "").strip().lower()
        if not s:
            return existing
        mapping = {
            "active": SubscriptionStatus.active.value,
            "trialing": SubscriptionStatus.trialing.value,
            "past_due": SubscriptionStatus.past_due.value,
            "paused": SubscriptionStatus.paused.value,
            "canceled": SubscriptionStatus.cancelled.value,
            "cancelled": SubscriptionStatus.cancelled.value,
            "unpaid": SubscriptionStatus.expired.value,
            "expired": SubscriptionStatus.expired.value,
            # Stripe initial states.
            # - For brand new subscriptions we don't create DB rows until active/trialing (see created handler).
            # - For existing subscriptions (e.g., portal plan changes), treat `incomplete` as past_due so users
            #   don't appear "free" while a payment method update / proration invoice is processing.
            "incomplete": SubscriptionStatus.past_due.value,
            "incomplete_expired": SubscriptionStatus.expired.value,
        }
        return mapping.get(s, existing)


