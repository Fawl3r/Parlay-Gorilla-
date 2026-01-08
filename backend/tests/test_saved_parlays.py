import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta, timezone
import uuid

from sqlalchemy import select

from app.models.verification_record import VerificationRecord


@pytest.mark.asyncio
async def test_save_custom_parlay_does_not_auto_create_verification_record(client: AsyncClient, db):
    """
    Selective policy: saving does NOT auto-create a verification record.
    """
    # Register user
    r = await client.post("/api/auth/register", json={"email": "saved-custom@test.com", "password": "Passw0rd!"})
    token = r.json()["access_token"]

    resp = await client.post(
        "/api/parlays/custom/save",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "My Custom Ticket",
            "legs": [
                {
                    "game_id": "00000000-0000-0000-0000-000000000001",
                    "pick": "home",
                    "market_type": "spreads",
                    "point": -3.5,
                }
            ],
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["parlay_type"] == "custom"
    saved_id = data["id"]

    # No verification records are created unless the user explicitly opts in.
    res = await db.execute(
        select(VerificationRecord.id).where(VerificationRecord.saved_parlay_id == uuid.UUID(saved_id)).limit(1)
    )
    assert res.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_save_ai_parlay_never_creates_verification_record(client: AsyncClient, db):
    r = await client.post("/api/auth/register", json={"email": "saved-ai@test.com", "password": "Passw0rd!"})
    token = r.json()["access_token"]

    resp = await client.post(
        "/api/parlays/ai/save",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "AI Ticket",
            "legs": [
                {
                    "market_id": "m1",
                    "outcome": "home",
                    "game": "A @ B",
                    "market_type": "h2h",
                    "odds": "-110",
                    "probability": 0.55,
                    "confidence": 60,
                }
            ],
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["parlay_type"] == "ai_generated"
    saved_id = data["id"]

    res = await db.execute(
        select(VerificationRecord.id).where(VerificationRecord.saved_parlay_id == uuid.UUID(saved_id)).limit(1)
    )
    assert res.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_retry_only_works_for_failed_custom(client: AsyncClient):
    r = await client.post("/api/auth/register", json={"email": "retry@test.com", "password": "Passw0rd!"})
    token = r.json()["access_token"]

    # Save AI parlay
    ai = await client.post(
        "/api/parlays/ai/save",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "AI Ticket",
            "legs": [
                {
                    "market_id": "m1",
                    "outcome": "home",
                    "game": "A @ B",
                    "market_type": "h2h",
                    "odds": "-110",
                    "probability": 0.55,
                    "confidence": 60,
                }
            ],
        },
    )
    ai_id = ai.json()["id"]
    retry_ai = await client.post(
        f"/api/parlays/{ai_id}/verification/retry",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert retry_ai.status_code == 400


@pytest.mark.asyncio
async def test_queue_verification_rejects_ai_saved_parlay(client: AsyncClient):
    r = await client.post("/api/auth/register", json={"email": "queue-ai@test.com", "password": "Passw0rd!"})
    token = r.json()["access_token"]

    resp = await client.post(
        "/api/parlays/ai/save",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "AI Ticket",
            "legs": [
                {
                    "market_id": "m1",
                    "outcome": "home",
                    "game": "A @ B",
                    "market_type": "h2h",
                    "odds": "-110",
                    "probability": 0.55,
                    "confidence": 60,
                }
            ],
        },
    )
    assert resp.status_code == 200
    saved_id = resp.json()["id"]

    queued = await client.post(
        f"/api/parlays/{saved_id}/verification/queue",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert queued.status_code == 400


@pytest.mark.asyncio
async def test_queue_verification_requires_premium_for_custom_saved_parlay(client: AsyncClient):
    r = await client.post("/api/auth/register", json={"email": "queue-custom@test.com", "password": "Passw0rd!"})
    token = r.json()["access_token"]

    resp = await client.post(
        "/api/parlays/custom/save",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "My Custom Ticket",
            "legs": [
                {
                    "game_id": "00000000-0000-0000-0000-000000000001",
                    "pick": "home",
                    "market_type": "spreads",
                    "point": -3.5,
                }
            ],
        },
    )
    assert resp.status_code == 200
    saved_id = resp.json()["id"]

    queued = await client.post(
        f"/api/parlays/{saved_id}/verification/queue",
        headers={"Authorization": f"Bearer {token}"},
    )
    # Not premium by default.
    assert queued.status_code == 402


@pytest.mark.asyncio
async def test_queue_verification_uses_credits_when_premium_quota_exhausted(client: AsyncClient, db, monkeypatch):
    """
    Premium users get an included verification quota. After it's exhausted, the API should
    allow queueing by charging credits (instead of hard-blocking).
    """
    from app.core.config import settings
    from app.models.subscription import Subscription, SubscriptionStatus
    from app.models.user import User

    # Stub out Redis enqueue so the test stays offline.
    class FakeVerificationQueue:
        async def enqueue_verification_record(self, *, verification_record_id: str, saved_parlay_id: str) -> str:
            _ = (verification_record_id, saved_parlay_id)
            return "job-test-1"

    import app.services.verification_records.saved_parlay_verification_service as svc_mod

    monkeypatch.setattr(svc_mod, "VerificationQueue", lambda: FakeVerificationQueue())

    # Register user + save a custom parlay.
    r = await client.post("/api/auth/register", json={"email": "queue-credit@test.com", "password": "Passw0rd!"})
    token = r.json()["access_token"]
    user_id = r.json()["user"]["id"]
    user_uuid = uuid.UUID(user_id)

    save = await client.post(
        "/api/parlays/custom/save",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "My Custom Ticket",
            "legs": [
                {
                    "game_id": "00000000-0000-0000-0000-000000000001",
                    "pick": "home",
                    "market_type": "spreads",
                    "point": -3.5,
                }
            ],
        },
    )
    assert save.status_code == 200
    saved_id = save.json()["id"]

    # Make user premium by seeding an active subscription.
    now = datetime.now(timezone.utc)
    sub = Subscription(
        id=uuid.uuid4(),
        user_id=user_uuid,
        plan="PG_PREMIUM_MONTHLY",
        provider="lemonsqueezy",
        provider_subscription_id="ls_sub_test_credits",
        provider_customer_id="ls_cust_test_credits",
        status=SubscriptionStatus.active.value,
        current_period_start=now,
        current_period_end=now + timedelta(days=30),
        cancel_at_period_end=False,
        is_lifetime=False,
    )
    db.add(sub)

    # Exhaust included inscription quota and fund credits for overage.
    user_row = (await db.execute(select(User).where(User.id == user_uuid))).scalar_one()
    user_row.premium_inscriptions_period_start = now
    user_row.premium_inscriptions_used = int(settings.premium_inscriptions_per_month)
    user_row.credit_balance = 10
    await db.commit()

    queued = await client.post(
        f"/api/parlays/{saved_id}/verification/queue",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert queued.status_code == 200, queued.text
    body = queued.json()
    assert body["status"] == "queued"
    assert body["saved_parlay_id"] == saved_id

    await db.refresh(user_row)
    assert user_row.credit_balance == 10 - int(getattr(settings, "credits_cost_inscription", 1) or 1)


@pytest.mark.asyncio
async def test_queue_verification_over_quota_requires_credits(client: AsyncClient, db, monkeypatch):
    """
    When premium included quota is exhausted and the user lacks credits, the API should
    return a paywall error with a clear message.
    """
    from app.core.config import settings
    from app.models.subscription import Subscription, SubscriptionStatus
    from app.models.user import User

    # Stub out Redis enqueue (should not be called in this test).
    class FakeVerificationQueue:
        async def enqueue_verification_record(self, *, verification_record_id: str, saved_parlay_id: str) -> str:
            raise AssertionError("enqueue should not be called when user lacks credits")

    import app.services.verification_records.saved_parlay_verification_service as svc_mod

    monkeypatch.setattr(svc_mod, "VerificationQueue", lambda: FakeVerificationQueue())

    r = await client.post("/api/auth/register", json={"email": "queue-nocredits@test.com", "password": "Passw0rd!"})
    token = r.json()["access_token"]
    user_id = r.json()["user"]["id"]
    user_uuid = uuid.UUID(user_id)

    save = await client.post(
        "/api/parlays/custom/save",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "My Custom Ticket",
            "legs": [
                {
                    "game_id": "00000000-0000-0000-0000-000000000001",
                    "pick": "home",
                    "market_type": "spreads",
                    "point": -3.5,
                }
            ],
        },
    )
    saved_id = save.json()["id"]

    now = datetime.now(timezone.utc)
    sub = Subscription(
        id=uuid.uuid4(),
        user_id=user_uuid,
        plan="PG_PREMIUM_MONTHLY",
        provider="lemonsqueezy",
        provider_subscription_id="ls_sub_test_nocredits",
        provider_customer_id="ls_cust_test_nocredits",
        status=SubscriptionStatus.active.value,
        current_period_start=now,
        current_period_end=now + timedelta(days=30),
        cancel_at_period_end=False,
        is_lifetime=False,
    )
    db.add(sub)

    user_row = (await db.execute(select(User).where(User.id == user_uuid))).scalar_one()
    user_row.premium_inscriptions_period_start = now
    user_row.premium_inscriptions_used = int(settings.premium_inscriptions_per_month)
    user_row.credit_balance = 0
    await db.commit()

    queued = await client.post(
        f"/api/parlays/{saved_id}/verification/queue",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert queued.status_code == 402
    detail = queued.json().get("detail") or {}
    msg = detail.get("message") if isinstance(detail, dict) else str(detail)
    assert "credit" in str(msg or "").lower()

