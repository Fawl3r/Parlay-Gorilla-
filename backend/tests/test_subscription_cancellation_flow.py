"""
Integration tests for subscription cancellation flow.

Covers:
- POST /api/subscription/cancel cancels at provider (mocked) and persists cancel_at_period_end
- User retains access until period end (billing/status + billing/access-status remain premium/active)
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.user import SubscriptionStatusEnum, User, UserPlan


async def _register_user(client: AsyncClient) -> tuple[str, str]:
    email = f"sub-cancel-{uuid.uuid4()}@example.com"
    r = await client.post("/api/auth/register", json={"email": email, "password": "testpass123"})
    assert r.status_code == 200
    data = r.json()
    return data["user"]["id"], data["access_token"]


@pytest.mark.asyncio
async def test_cancel_subscription_marks_period_end_cancel_and_keeps_access(
    client: AsyncClient, db: AsyncSession, monkeypatch
):
    user_id, token = await _register_user(client)
    user_uuid = uuid.UUID(user_id)

    # Ensure cancellation endpoint is enabled for tests (provider call is mocked).
    settings.lemonsqueezy_api_key = "test_ls_key"

    now = datetime.now(timezone.utc)
    period_end = now + timedelta(days=30)

    # Seed DB with an active subscription.
    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalar_one()
    user.plan = UserPlan.standard.value
    user.subscription_plan = "starter_monthly"
    user.subscription_status = SubscriptionStatusEnum.active.value
    user.subscription_renewal_date = period_end

    subscription = Subscription(
        id=uuid.uuid4(),
        user_id=user_uuid,
        plan="starter_monthly",
        provider="lemonsqueezy",
        provider_subscription_id="ls_sub_test_123",
        provider_customer_id="ls_cust_test_123",
        status=SubscriptionStatus.active.value,
        current_period_start=now,
        current_period_end=period_end,
        cancel_at_period_end=False,
        is_lifetime=False,
    )
    db.add(subscription)
    await db.commit()

    # Mock LemonSqueezy DELETE cancellation response.
    async def _mock_cancel(self, subscription_id: str) -> dict:
        assert subscription_id == "ls_sub_test_123"
        return {
            "data": {
                "attributes": {
                    "status": "cancelled",
                    "ends_at": period_end.isoformat().replace("+00:00", "Z"),
                }
            }
        }

    from app.services.lemonsqueezy_subscription_client import LemonSqueezySubscriptionClient

    monkeypatch.setattr(LemonSqueezySubscriptionClient, "cancel_subscription", _mock_cancel)

    # Cancel via API.
    r = await client.post("/api/subscription/cancel", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    body = r.json()
    assert body["cancel_at_period_end"] is True

    # Subscription record updated.
    # NOTE: API request uses a different DB session; refresh to avoid identity-map staleness.
    await db.refresh(subscription)
    assert subscription.cancel_at_period_end is True
    assert subscription.cancelled_at is not None
    assert subscription.status in (SubscriptionStatus.active.value, SubscriptionStatus.cancelled.value)

    # User access remains premium until period end.
    status_resp = await client.get("/api/billing/status", headers={"Authorization": f"Bearer {token}"})
    assert status_resp.status_code == 200
    assert status_resp.json()["tier"] == "premium"

    access_resp = await client.get("/api/billing/access-status", headers={"Authorization": f"Bearer {token}"})
    assert access_resp.status_code == 200
    assert access_resp.json()["subscription"]["active"] is True


