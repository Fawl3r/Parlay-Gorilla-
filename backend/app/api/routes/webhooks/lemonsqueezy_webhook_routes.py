"""
LemonSqueezy webhook routes.

Handles LemonSqueezy events needed by the hybrid billing + affiliate system:
- subscription_created
- subscription_updated
- order_created / order_completed (lifetime access + credit packs)

This route is intentionally defensive:
- Signature verification is enforced only when LEMONSQUEEZY_WEBHOOK_SECRET is set.
- Webhooks are idempotent via PaymentEvent.event_id (prefers meta.webhook_id).
- Returns 200 on processing errors to avoid provider retry storms; failures are recorded in PaymentEvent.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.webhooks.shared_handlers import _handle_affiliate_commission
from app.api.routes.webhooks.webhook_security import WebhookHmacSha256Signature
from app.core.config import settings
from app.core.dependencies import get_db
from app.models.affiliate_commission import CommissionSaleType, CommissionSettlementProvider
from app.models.payment_event import PaymentEvent
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.user import SubscriptionStatusEnum, User, UserPlan
from app.services.lemonsqueezy_credit_pack_webhook_handler import LemonSqueezyCreditPackWebhookHandler
from app.services.lemonsqueezy_lifetime_access_webhook_handler import LemonSqueezyLifetimeAccessWebhookHandler
from app.services.lemonsqueezy_webhook_payload import LemonSqueezyWebhookPayload

logger = logging.getLogger(__name__)
router = APIRouter()


def _parse_iso8601(value: object) -> Optional[datetime]:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


@dataclass(frozen=True)
class _LsSubscriptionFields:
    user_id: Optional[str]
    plan_code: Optional[str]
    renews_at: Optional[datetime]
    created_at: Optional[datetime]
    status: str
    total_cents: int
    customer_id: str


class _LemonSqueezySubscriptionExtractor:
    def extract(self, payload: LemonSqueezyWebhookPayload) -> _LsSubscriptionFields:
        attrs = payload.attributes()
        custom = payload.custom_data()

        user_id = str(custom.get("user_id") or "").strip() or None
        plan_code = str(custom.get("plan_code") or "").strip() or None

        renews_at = _parse_iso8601(attrs.get("renews_at"))
        created_at = _parse_iso8601(attrs.get("created_at"))

        status = str(attrs.get("status") or "active").strip().lower()
        customer_id = str(attrs.get("customer_id") or "").strip()

        total_raw = attrs.get("total")
        try:
            total_cents = int(total_raw or 0)
        except Exception:
            total_cents = 0

        return _LsSubscriptionFields(
            user_id=user_id,
            plan_code=plan_code,
            renews_at=renews_at,
            created_at=created_at,
            status=status,
            total_cents=total_cents,
            customer_id=customer_id,
        )


class _LemonSqueezySubscriptionUpserter:
    def __init__(self, *, db: AsyncSession) -> None:
        self._db = db

    async def upsert(self, *, provider_subscription_id: str, fields: _LsSubscriptionFields, provider_attrs: dict[str, Any]) -> None:
        if not provider_subscription_id:
            logger.warning("LemonSqueezy subscription webhook missing data.id; skipping")
            return

        existing = await self._db.execute(
            select(Subscription).where(
                Subscription.provider == "lemonsqueezy",
                Subscription.provider_subscription_id == provider_subscription_id,
            )
        )
        sub = existing.scalar_one_or_none()
        user_uuid = None
        if fields.user_id:
            try:
                import uuid

                user_uuid = uuid.UUID(fields.user_id)
            except Exception:
                logger.warning("Invalid user_id in LemonSqueezy webhook: %s", fields.user_id)
                return
        elif sub is not None:
            user_uuid = sub.user_id

        if not sub:
            if user_uuid is None:
                logger.warning("LemonSqueezy subscription webhook missing user_id and no existing subscription; skipping")
                return
            sub = Subscription(
                user_id=user_uuid,
                plan=str(fields.plan_code or "premium"),
                provider="lemonsqueezy",
                provider_subscription_id=provider_subscription_id,
                provider_customer_id=fields.customer_id or None,
                status=SubscriptionStatus.active.value,
            )
            self._db.add(sub)

        if fields.plan_code:
            sub.plan = str(fields.plan_code)
        if fields.customer_id:
            sub.provider_customer_id = fields.customer_id
        if fields.created_at:
            sub.current_period_start = fields.created_at
        if fields.renews_at:
            sub.current_period_end = fields.renews_at

        sub.cancel_at_period_end = bool(sub.cancel_at_period_end or False)
        sub.provider_metadata = provider_attrs

        sub.status = self._map_status(fields.status, existing=sub.status)

        # Sync user table (billing UI reads this).
        if user_uuid is None:
            return
        user_row = (await self._db.execute(select(User).where(User.id == user_uuid))).scalar_one_or_none()
        if user_row:
            user_row.subscription_plan = str(fields.plan_code or user_row.subscription_plan or "")
            user_row.subscription_status = SubscriptionStatusEnum.active.value
            if fields.renews_at:
                user_row.subscription_renewal_date = fields.renews_at
            # Treat all paid subscriptions as at least standard.
            if user_row.plan == UserPlan.free.value:
                user_row.plan = UserPlan.standard.value

    @staticmethod
    def _map_status(status_value: str, *, existing: str) -> str:
        s = (status_value or "").strip().lower()
        if not s:
            return existing
        mapping = {
            "active": SubscriptionStatus.active.value,
            "cancelled": SubscriptionStatus.cancelled.value,
            "canceled": SubscriptionStatus.cancelled.value,
            "past_due": SubscriptionStatus.past_due.value,
            "expired": SubscriptionStatus.expired.value,
            "paused": SubscriptionStatus.paused.value,
            "trialing": SubscriptionStatus.trialing.value,
            "on_trial": SubscriptionStatus.trialing.value,
        }
        return mapping.get(s, existing)


@router.post("/webhooks/lemonsqueezy")
async def handle_lemonsqueezy_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    signature: str = Header(None, alias="X-Signature"),
):
    body = await request.body()

    # Signature verification (only when configured).
    secret = (settings.lemonsqueezy_webhook_secret or "").strip()
    if secret:
        if not signature:
            raise HTTPException(status_code=401, detail="Missing signature")
        if not WebhookHmacSha256Signature(secret=secret).matches(body=body, provided_signature=signature):
            raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        payload_dict = json.loads(body.decode("utf-8"))
        if not isinstance(payload_dict, dict):
            raise ValueError("payload not a JSON object")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    payload = LemonSqueezyWebhookPayload(raw_body=body, payload=payload_dict)
    event_type = payload.event_name()
    meta = payload_dict.get("meta", {}) or {}
    event_id = str(meta.get("webhook_id") or payload.idempotency_key()).strip()

    # Event idempotency
    if event_id:
        existing = await db.execute(select(PaymentEvent.id).where(PaymentEvent.event_id == event_id))
        if existing.scalar_one_or_none():
            return {"status": "ok", "message": "Duplicate event"}

    event_record = PaymentEvent(
        provider="lemonsqueezy",
        event_type=event_type,
        event_id=event_id or None,
        raw_payload=payload_dict,
        processed="pending",
    )
    db.add(event_record)
    try:
        await db.commit()
        await db.refresh(event_record)
    except Exception as exc:
        # Most commonly: duplicate event_id unique constraint (race).
        await db.rollback()
        logger.warning("Failed to insert PaymentEvent for LemonSqueezy webhook: %s", exc)

    try:
        await _dispatch_lemonsqueezy(db=db, payload=payload)
        try:
            event_record.mark_processed()
            await db.commit()
        except Exception:
            await db.rollback()
    except Exception as exc:
        logger.error("Error processing LemonSqueezy webhook event=%s: %s", event_type, exc, exc_info=True)
        try:
            event_record.mark_failed(str(exc))
            await db.commit()
        except Exception:
            await db.rollback()

    return {"status": "ok"}


async def _dispatch_lemonsqueezy(*, db: AsyncSession, payload: LemonSqueezyWebhookPayload) -> None:
    event = payload.event_name()
    data_id = payload.data_id()

    # Subscription lifecycle
    if event in {"subscription_created", "subscription_updated"}:
        fields = _LemonSqueezySubscriptionExtractor().extract(payload)
        await _LemonSqueezySubscriptionUpserter(db=db).upsert(
            provider_subscription_id=data_id,
            fields=fields,
            provider_attrs=payload.attributes(),
        )

        # Affiliate commission on initial subscription creation only.
        if event == "subscription_created" and fields.user_id and fields.total_cents > 0:
            await _handle_affiliate_commission(
                db=db,
                user_id=fields.user_id,
                sale_type=CommissionSaleType.SUBSCRIPTION.value,
                sale_amount=Decimal(fields.total_cents) / Decimal("100"),
                sale_id=data_id,
                settlement_provider=CommissionSettlementProvider.LEMONSQUEEZY.value,
                is_first_subscription=True,
                subscription_plan=fields.plan_code,
            )

        await db.commit()
        return

    # One-time orders (lifetime access + credit packs)
    if event in {"order_created", "order_completed"}:
        custom = payload.custom_data()
        user_id = str(custom.get("user_id") or "").strip() or None
        purchase_type = str(custom.get("purchase_type") or "").strip().lower()

        if purchase_type == "lifetime_access":
            await LemonSqueezyLifetimeAccessWebhookHandler(db=db).handle(payload.payload, user_id=user_id)
            await db.commit()
            return

        # Credit packs (if you re-enable)
        if purchase_type == "credit_pack":
            await LemonSqueezyCreditPackWebhookHandler(db=db).handle(payload.payload, user_id=user_id)
            await db.commit()
            return

    # Recurring payment events are handled elsewhere for now (optional)
    return


