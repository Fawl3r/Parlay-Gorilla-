"""
Integration tests for subscription_updated webhook syncing into `users` table.

Why: Billing UI + hybrid access model read subscription info from `users`,
so we must keep renewal/end dates in sync on renewals.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscription import Subscription
from app.models.user import User


async def _register_user(client: AsyncClient) -> tuple[str, str]:
    email = f"ls-update-{uuid.uuid4()}@example.com"
    r = await client.post("/api/auth/register", json={"email": email, "password": "testpass123"})
    assert r.status_code == 200
    data = r.json()
    return data["user"]["id"], data["access_token"]


@pytest.mark.asyncio
async def test_lemonsqueezy_subscription_updated_updates_user_renewal_date_and_access_status(
    client: AsyncClient, db: AsyncSession
):
    user_id, token = await _register_user(client)

    # Create subscription via webhook (seed record + user fields).
    sub_id = f"ls_sub_{uuid.uuid4()}"
    created_payload = {
        "meta": {
            "event_name": "subscription_created",
            "webhook_id": f"ls_evt_{uuid.uuid4()}",
            "custom_data": {"user_id": user_id, "plan_code": "elite_monthly"},
        },
        "data": {
            "id": sub_id,
            "attributes": {
                "customer_id": "test_customer",
                "first_subscription_item": {"custom_data": {"user_id": user_id, "plan_code": "elite_monthly"}},
                "renews_at": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat().replace("+00:00", "Z"),
                "status": "active",
                "total": 3999,
            },
        },
    }
    r1 = await client.post("/api/webhooks/lemonsqueezy", json=created_payload)
    assert r1.status_code == 200

    # Verify initial user renewal date exists.
    user_row = (await db.execute(select(User).where(User.id == uuid.UUID(user_id)))).scalar_one()
    assert user_row.subscription_renewal_date is not None

    # Send update webhook extending renews_at.
    new_renews_at = datetime.now(timezone.utc) + timedelta(days=60)
    updated_payload = {
        "meta": {
            "event_name": "subscription_updated",
            "webhook_id": f"ls_evt_{uuid.uuid4()}",
        },
        "data": {
            "id": sub_id,
            "attributes": {
                "renews_at": new_renews_at.isoformat().replace("+00:00", "Z"),
                "status": "active",
            },
        },
    }
    r2 = await client.post("/api/webhooks/lemonsqueezy", json=updated_payload)
    assert r2.status_code == 200

    # Ensure user renewal date updated.
    await db.refresh(user_row)
    assert user_row.subscription_renewal_date is not None
    assert abs(user_row.subscription_renewal_date.replace(tzinfo=timezone.utc) - new_renews_at) < timedelta(minutes=1)

    # Ensure billing access-status sees subscription active.
    access_resp = await client.get("/api/billing/access-status", headers={"Authorization": f"Bearer {token}"})
    assert access_resp.status_code == 200
    assert access_resp.json()["subscription"]["active"] is True

    # Ensure subscription record period end updated too.
    sub_row = (await db.execute(select(Subscription).where(Subscription.provider_subscription_id == sub_id))).scalar_one()
    assert sub_row.current_period_end is not None


