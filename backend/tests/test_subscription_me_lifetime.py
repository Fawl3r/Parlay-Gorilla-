import uuid
from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscription import Subscription, SubscriptionStatus
from app.models.user import User
from app.services.auth_service import create_access_token, get_password_hash


@pytest.mark.asyncio
async def test_subscription_me_returns_lifetime_when_active_lifetime_subscription_exists(
    client: AsyncClient,
    db: AsyncSession,
):
    user_id = uuid.uuid4()
    email = f"lifetime-{uuid.uuid4()}@example.com"

    user = User(
        id=user_id,
        email=email,
        password_hash=get_password_hash("testpass123"),
        email_verified=True,
    )
    db.add(user)
    await db.commit()

    db.add(
        Subscription(
            id=uuid.uuid4(),
            user_id=user_id,
            plan="PG_LIFETIME_CARD",
            provider="stripe",
            provider_subscription_id=f"lifetime_{uuid.uuid4()}",
            status=SubscriptionStatus.active.value,
            current_period_start=datetime.now(timezone.utc),
            current_period_end=None,
            is_lifetime=True,
            cancel_at_period_end=False,
        )
    )
    await db.commit()

    token = create_access_token({"sub": str(user_id), "email": email})
    resp = await client.get("/api/subscription/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()

    assert data["has_subscription"] is True
    assert data["is_lifetime"] is True
    assert data["status"] == "active"
    assert data["plan_id"] == "PG_LIFETIME_CARD"


@pytest.mark.asyncio
async def test_subscription_me_returns_lifetime_when_lifetime_subscription_is_cancelled_without_period_end(
    client: AsyncClient,
    db: AsyncSession,
):
    """
    Regression guard:
    some lifetime rows can end up with status=cancelled but no current_period_end.
    Our API should still report lifetime access (active) to match billing/status.
    """

    user_id = uuid.uuid4()
    email = f"lifetime-cancelled-{uuid.uuid4()}@example.com"

    user = User(
        id=user_id,
        email=email,
        password_hash=get_password_hash("testpass123"),
        email_verified=True,
    )
    db.add(user)
    await db.commit()

    db.add(
        Subscription(
            id=uuid.uuid4(),
            user_id=user_id,
            plan="PG_LIFETIME_CARD",
            provider="stripe",
            provider_subscription_id=f"lifetime_{uuid.uuid4()}",
            status=SubscriptionStatus.cancelled.value,
            current_period_start=datetime.now(timezone.utc),
            current_period_end=None,
            is_lifetime=True,
            cancel_at_period_end=True,
        )
    )
    await db.commit()

    token = create_access_token({"sub": str(user_id), "email": email})
    resp = await client.get("/api/subscription/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()

    assert data["has_subscription"] is True
    assert data["is_lifetime"] is True
    assert data["status"] == "active"
    assert data["plan_id"] == "PG_LIFETIME_CARD"


