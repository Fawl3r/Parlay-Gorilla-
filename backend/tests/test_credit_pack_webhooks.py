"""
Integration tests for credit pack purchase fulfillment via webhooks.

Covers:
- LemonSqueezy credit pack orders award credits exactly once (purchase-idempotent)
- Coinbase Commerce credit pack charges award credits exactly once (purchase-idempotent)
- Duplicate webhook event deliveries are safely ignored (event-idempotent)
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.credit_pack_purchase import CreditPackPurchase


async def _register_user(client: AsyncClient) -> tuple[str, str]:
    email = f"credits-{uuid.uuid4()}@example.com"
    r = await client.post("/api/auth/register", json={"email": email, "password": "testpass123"})
    assert r.status_code == 200
    data = r.json()
    return data["user"]["id"], data["access_token"]


async def _get_credit_balance(client: AsyncClient, token: str) -> int:
    r = await client.get("/api/billing/access-status", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    return int(r.json()["credits"]["balance"])


@pytest.mark.asyncio
async def test_lemonsqueezy_credit_pack_webhook_awards_credits_once_and_idempotent(
    client: AsyncClient, db: AsyncSession
):
    pytest.skip("LemonSqueezy webhooks are disabled - Stripe is now the only payment provider")
    user_id, token = await _register_user(client)

    initial_balance = await _get_credit_balance(client, token)

    order_id = f"ls_order_{uuid.uuid4()}"
    event_id_1 = f"ls_evt_{uuid.uuid4()}"
    event_id_2 = f"ls_evt_{uuid.uuid4()}"

    payload_1 = {
        "meta": {
            "event_name": "order_created",
            "webhook_id": event_id_1,
            "custom_data": {
                "user_id": user_id,
                "purchase_type": "credit_pack",
                "credit_pack_id": "credits_25",
            },
        },
        "data": {
            "id": order_id,
            "attributes": {
                "customer_id": "test_customer",
                "first_subscription_item": {
                    "custom_data": {
                        "user_id": user_id,
                        "purchase_type": "credit_pack",
                        "credit_pack_id": "credits_25",
                    }
                },
            },
        },
    }

    r1 = await client.post("/api/webhooks/lemonsqueezy", json=payload_1)
    assert r1.status_code == 200

    balance_after_first = await _get_credit_balance(client, token)
    assert balance_after_first == initial_balance + 25

    # Repeat with a different event_id but the same provider order id.
    payload_2 = {
        **payload_1,
        "meta": {**payload_1["meta"], "event_name": "order_completed", "webhook_id": event_id_2},
    }

    r2 = await client.post("/api/webhooks/lemonsqueezy", json=payload_2)
    assert r2.status_code == 200

    balance_after_second = await _get_credit_balance(client, token)
    assert balance_after_second == initial_balance + 25

    # Duplicate event delivery (same event_id) should be ignored.
    r3 = await client.post("/api/webhooks/lemonsqueezy", json=payload_1)
    assert r3.status_code == 200

    balance_after_third = await _get_credit_balance(client, token)
    assert balance_after_third == initial_balance + 25

    # Purchase record is created exactly once.
    result = await db.execute(
        select(CreditPackPurchase).where(
            (CreditPackPurchase.provider == "lemonsqueezy") & (CreditPackPurchase.provider_order_id == order_id)
        )
    )
    purchases = result.scalars().all()
    assert len(purchases) == 1
    assert purchases[0].credits_awarded == 25


@pytest.mark.asyncio
async def test_coinbase_credit_pack_webhook_awards_credits_once_and_idempotent(
    client: AsyncClient, db: AsyncSession
):
    pytest.skip("Coinbase Commerce is disabled for LemonSqueezy compliance")
    user_id, token = await _register_user(client)

    initial_balance = await _get_credit_balance(client, token)

    charge_id = f"cb_charge_{uuid.uuid4()}"
    event_id_1 = f"cb_evt_{uuid.uuid4()}"
    event_id_2 = f"cb_evt_{uuid.uuid4()}"

    payload_1 = {
        "id": event_id_1,
        "event": {
            "type": "charge:confirmed",
            "data": {
                "id": charge_id,
                "metadata": {
                    "user_id": user_id,
                    "purchase_type": "credit_pack",
                    "credit_pack_id": "credits_10",
                },
            },
        },
    }

    r1 = await client.post("/api/webhooks/coinbase", json=payload_1)
    assert r1.status_code == 200

    balance_after_first = await _get_credit_balance(client, token)
    assert balance_after_first == initial_balance + 10

    # Repeat with a new event_id but same provider order id (charge_id).
    payload_2 = {**payload_1, "id": event_id_2}
    r2 = await client.post("/api/webhooks/coinbase", json=payload_2)
    assert r2.status_code == 200

    balance_after_second = await _get_credit_balance(client, token)
    assert balance_after_second == initial_balance + 10

    # Duplicate event delivery (same event_id) should be ignored.
    r3 = await client.post("/api/webhooks/coinbase", json=payload_1)
    assert r3.status_code == 200

    balance_after_third = await _get_credit_balance(client, token)
    assert balance_after_third == initial_balance + 10

    result = await db.execute(
        select(CreditPackPurchase).where(
            (CreditPackPurchase.provider == "coinbase") & (CreditPackPurchase.provider_order_id == charge_id)
        )
    )
    purchases = result.scalars().all()
    assert len(purchases) == 1
    assert purchases[0].credits_awarded == 10


