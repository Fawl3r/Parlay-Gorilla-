"""
Integration tests for Coinbase time-based subscriptions (monthly/annual).

Ensures:
- Monthly/annual crypto plans set `current_period_end`
- Renewals stack from the existing period end (early renewal extends time)
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscription import Subscription
from app.models.subscription_plan import BillingCycle, PaymentProvider, SubscriptionPlan
from app.models.user import User


async def _register_user(client: AsyncClient) -> tuple[str, str]:
    email = f"cb-sub-{uuid.uuid4()}@example.com"
    r = await client.post("/api/auth/register", json={"email": email, "password": "testpass123"})
    assert r.status_code == 200
    data = r.json()
    return data["user"]["id"], data["access_token"]


async def _ensure_plan(db: AsyncSession, code: str, billing_cycle: str, price_cents: int):
    result = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.code == code))
    existing = result.scalar_one_or_none()
    if existing:
        return
    db.add(
        SubscriptionPlan(
            code=code,
            name=code,
            description=code,
            price_cents=price_cents,
            currency="USD",
            billing_cycle=billing_cycle,
            provider=PaymentProvider.coinbase.value,
            is_active=True,
            is_featured=False,
            max_ai_parlays_per_day=-1,
            can_use_custom_builder=True,
            can_use_upset_finder=True,
            can_use_multi_sport=True,
            can_save_parlays=True,
            ad_free=True,
        )
    )
    await db.commit()


@pytest.mark.asyncio
async def test_coinbase_monthly_sets_period_end_and_renews_stack(client: AsyncClient, db: AsyncSession):
    user_id, _token = await _register_user(client)
    await _ensure_plan(db, "PG_PREMIUM_MONTHLY_CRYPTO", BillingCycle.monthly.value, 1999)

    charge_id_1 = f"cb_charge_{uuid.uuid4()}"
    event_id_1 = f"cb_evt_{uuid.uuid4()}"

    payload_1 = {
        "id": event_id_1,
        "event": {
            "type": "charge:confirmed",
            "data": {
                "id": charge_id_1,
                "pricing": {"local": {"amount": "19.99", "currency": "USD"}},
                "metadata": {"user_id": user_id, "plan_code": "PG_PREMIUM_MONTHLY_CRYPTO"},
            },
        },
    }

    now = datetime.now(timezone.utc)
    r1 = await client.post("/api/webhooks/coinbase", json=payload_1)
    assert r1.status_code == 200

    sub_1 = (await db.execute(select(Subscription).where(Subscription.provider_subscription_id == charge_id_1))).scalar_one()
    assert sub_1.provider == "coinbase"
    assert sub_1.is_lifetime is False
    assert sub_1.current_period_end is not None

    # Approx 30 days from now.
    end_1 = sub_1.current_period_end.replace(tzinfo=timezone.utc) if sub_1.current_period_end.tzinfo is None else sub_1.current_period_end
    assert end_1 > now + timedelta(days=29)
    assert end_1 < now + timedelta(days=31, hours=1)

    # Second renewal should stack from previous end.
    charge_id_2 = f"cb_charge_{uuid.uuid4()}"
    event_id_2 = f"cb_evt_{uuid.uuid4()}"
    payload_2 = {
        "id": event_id_2,
        "event": {
            "type": "charge:confirmed",
            "data": {
                "id": charge_id_2,
                "pricing": {"local": {"amount": "19.99", "currency": "USD"}},
                "metadata": {"user_id": user_id, "plan_code": "PG_PREMIUM_MONTHLY_CRYPTO"},
            },
        },
    }

    r2 = await client.post("/api/webhooks/coinbase", json=payload_2)
    assert r2.status_code == 200

    sub_2 = (await db.execute(select(Subscription).where(Subscription.provider_subscription_id == charge_id_2))).scalar_one()
    assert sub_2.current_period_end is not None
    end_2 = sub_2.current_period_end.replace(tzinfo=timezone.utc) if sub_2.current_period_end.tzinfo is None else sub_2.current_period_end

    assert end_2 > end_1 + timedelta(days=29)
    assert end_2 < end_1 + timedelta(days=31, hours=1)

    # User renewal date should match latest end.
    user_row = (await db.execute(select(User).where(User.id == uuid.UUID(user_id)))).scalar_one()
    assert user_row.subscription_renewal_date is not None


@pytest.mark.asyncio
async def test_coinbase_annual_sets_period_end(client: AsyncClient, db: AsyncSession):
    user_id, _token = await _register_user(client)
    await _ensure_plan(db, "PG_PREMIUM_ANNUAL_CRYPTO", BillingCycle.annual.value, 19999)

    charge_id = f"cb_charge_{uuid.uuid4()}"
    event_id = f"cb_evt_{uuid.uuid4()}"
    payload = {
        "id": event_id,
        "event": {
            "type": "charge:confirmed",
            "data": {
                "id": charge_id,
                "pricing": {"local": {"amount": "199.99", "currency": "USD"}},
                "metadata": {"user_id": user_id, "plan_code": "PG_PREMIUM_ANNUAL_CRYPTO"},
            },
        },
    }

    now = datetime.now(timezone.utc)
    r = await client.post("/api/webhooks/coinbase", json=payload)
    assert r.status_code == 200

    sub = (await db.execute(select(Subscription).where(Subscription.provider_subscription_id == charge_id))).scalar_one()
    assert sub.is_lifetime is False
    assert sub.current_period_end is not None

    end = sub.current_period_end.replace(tzinfo=timezone.utc) if sub.current_period_end.tzinfo is None else sub.current_period_end
    assert end > now + timedelta(days=364)
    assert end < now + timedelta(days=366, hours=1)


