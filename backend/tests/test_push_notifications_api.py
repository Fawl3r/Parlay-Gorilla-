from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_web_push_vapid_key_disabled_by_default(client):
    res = await client.get("/api/notifications/push/vapid-public-key")
    assert res.status_code == 200
    data = res.json()
    assert data["enabled"] is False
    assert data["public_key"] == ""


@pytest.mark.asyncio
async def test_web_push_subscribe_requires_enabled(client, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "web_push_enabled", False)
    res = await client.post(
        "/api/notifications/push/subscribe",
        json={
            "endpoint": "https://example.com/push/endpoint-1",
            "keys": {"p256dh": "p256dh", "auth": "auth"},
        },
    )
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_web_push_subscribe_upserts_and_unsubscribe_deletes(client, db, monkeypatch):
    from sqlalchemy import select, func

    from app.core.config import settings
    from app.models.push_subscription import PushSubscription

    monkeypatch.setattr(settings, "web_push_enabled", True)
    monkeypatch.setattr(settings, "web_push_vapid_public_key", "test_public")
    monkeypatch.setattr(settings, "web_push_vapid_private_key", "test_private")
    monkeypatch.setattr(settings, "web_push_subject", "mailto:test@example.com")

    endpoint = "https://example.com/push/endpoint-1"

    res1 = await client.post(
        "/api/notifications/push/subscribe",
        json={
            "endpoint": endpoint,
            "keys": {"p256dh": "p256dh_1", "auth": "auth_1"},
        },
    )
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["success"] is True
    assert data1["subscription_id"]

    count1 = await db.execute(select(func.count()).select_from(PushSubscription))
    assert int(count1.scalar_one() or 0) == 1

    res2 = await client.post(
        "/api/notifications/push/subscribe",
        json={
            "endpoint": endpoint,
            "keys": {"p256dh": "p256dh_2", "auth": "auth_2"},
            "expirationTime": 1_700_000_000_000,  # ms epoch
        },
    )
    assert res2.status_code == 200

    count2 = await db.execute(select(func.count()).select_from(PushSubscription))
    assert int(count2.scalar_one() or 0) == 1

    row = (await db.execute(select(PushSubscription))).scalars().first()
    assert row is not None
    assert row.endpoint == endpoint
    assert row.p256dh == "p256dh_2"
    assert row.auth == "auth_2"

    res3 = await client.post(
        "/api/notifications/push/unsubscribe",
        json={"endpoint": endpoint},
    )
    assert res3.status_code == 200
    assert res3.json()["deleted"] == 1

    res4 = await client.post(
        "/api/notifications/push/unsubscribe",
        json={"endpoint": endpoint},
    )
    assert res4.status_code == 200
    assert res4.json()["deleted"] == 0


