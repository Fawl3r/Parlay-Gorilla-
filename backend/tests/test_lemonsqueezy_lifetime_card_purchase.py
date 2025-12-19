"""
Integration tests for LemonSqueezy lifetime card purchase (one-time order).

Ensures:
- order_created/order_completed with purchase_type=lifetime_access grants lifetime subscription
- idempotent across multiple order events for the same order id
"""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscription import Subscription
from app.models.user import User


async def _register_user(client: AsyncClient) -> tuple[str, str]:
    email = f"ls-life-{uuid.uuid4()}@example.com"
    r = await client.post("/api/auth/register", json={"email": email, "password": "testpass123"})
    assert r.status_code == 200
    data = r.json()
    return data["user"]["id"], data["access_token"]


@pytest.mark.asyncio
async def test_lemonsqueezy_lifetime_order_grants_lifetime_and_is_idempotent(
    client: AsyncClient, db: AsyncSession
):
    user_id, _token = await _register_user(client)

    order_id = f"ls_order_{uuid.uuid4()}"
    event_id_1 = f"ls_evt_{uuid.uuid4()}"
    event_id_2 = f"ls_evt_{uuid.uuid4()}"

    payload_1 = {
        "meta": {
            "event_name": "order_created",
            "webhook_id": event_id_1,
            "custom_data": {
                "user_id": user_id,
                "purchase_type": "lifetime_access",
                "plan_code": "PG_LIFETIME_CARD",
            },
        },
        "data": {
            "id": order_id,
            "attributes": {
                "customer_id": "test_customer",
                "total": 50000,
            },
        },
    }

    r1 = await client.post("/api/webhooks/lemonsqueezy", json=payload_1)
    assert r1.status_code == 200

    sub = (await db.execute(select(Subscription).where(Subscription.provider_subscription_id == order_id))).scalar_one()
    assert sub.provider == "lemonsqueezy"
    assert sub.is_lifetime is True
    assert sub.current_period_end is None
    assert sub.plan == "PG_LIFETIME_CARD"

    user = (await db.execute(select(User).where(User.id == uuid.UUID(user_id)))).scalar_one()
    assert user.subscription_status == "active"
    assert user.subscription_plan == "PG_LIFETIME_CARD"
    assert user.subscription_renewal_date is None

    # Second delivery (different webhook_id, same order id) should be ignored by subscription idempotency.
    payload_2 = {**payload_1, "meta": {**payload_1["meta"], "event_name": "order_completed", "webhook_id": event_id_2}}
    r2 = await client.post("/api/webhooks/lemonsqueezy", json=payload_2)
    assert r2.status_code == 200

    subs = (await db.execute(select(Subscription).where(Subscription.provider_subscription_id == order_id))).scalars().all()
    assert len(subs) == 1


