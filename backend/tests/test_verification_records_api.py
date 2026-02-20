import pytest
import uuid
from datetime import datetime, timedelta, timezone

from httpx import AsyncClient
from sqlalchemy import select

from app.core.config import settings
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.user import User
from app.models.verification_record import VerificationRecord, VerificationStatus


@pytest.mark.asyncio
async def test_get_verification_record_is_user_scoped(client: AsyncClient, db, monkeypatch):
    # Stub out Redis enqueue.
    class FakeVerificationQueue:
        async def enqueue_verification_record(self, *, verification_record_id: str, saved_parlay_id: str) -> str:
            _ = (verification_record_id, saved_parlay_id)
            return "job-test-1"

    import app.services.verification_records.saved_parlay_verification_service as svc_mod

    monkeypatch.setattr(svc_mod, "VerificationQueue", lambda: FakeVerificationQueue())

    # User A (premium)
    reg_a = await client.post("/api/auth/register", json={"email": "vr-a@test.com", "password": "Passw0rd!"})
    token_a = reg_a.json()["access_token"]
    user_a_id = uuid.UUID(reg_a.json()["user"]["id"])

    now = datetime.now(timezone.utc)
    db.add(
        Subscription(
            id=uuid.uuid4(),
            user_id=user_a_id,
            plan="PG_PREMIUM_MONTHLY",
            provider="lemonsqueezy",
            provider_subscription_id="ls_sub_test_vr_a",
            provider_customer_id="ls_cust_test_vr_a",
            status=SubscriptionStatus.active.value,
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
            cancel_at_period_end=False,
            is_lifetime=False,
        )
    )
    await db.commit()

    save = await client.post(
        "/api/parlays/custom/save",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "title": "My Custom Ticket",
            "legs": [{"game_id": "00000000-0000-0000-0000-000000000001", "pick": "home", "market_type": "spreads", "point": -3.5}],
        },
    )
    assert save.status_code == 200
    saved_id = save.json()["id"]

    queued = await client.post(
        f"/api/parlays/{saved_id}/verification/queue",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert queued.status_code == 200, queued.text
    record_id = queued.json()["id"]

    # User A can fetch it.
    get_ok = await client.get(
        f"/api/verification-records/{record_id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert get_ok.status_code == 200
    assert get_ok.json()["id"] == record_id

    # User B cannot fetch it.
    reg_b = await client.post("/api/auth/register", json={"email": "vr-b@test.com", "password": "Passw0rd!"})
    token_b = reg_b.json()["access_token"]
    get_other = await client.get(
        f"/api/verification-records/{record_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert get_other.status_code == 404


@pytest.mark.asyncio
async def test_get_public_verification_record_does_not_require_auth(client: AsyncClient, db):
    reg = await client.post("/api/auth/register", json={"email": "vr-public@test.com", "password": "Passw0rd!"})
    assert reg.status_code == 200, reg.text
    user_uuid = uuid.UUID(reg.json()["user"]["id"])

    record_id = uuid.uuid4()
    record = VerificationRecord(
        id=record_id,
        user_id=user_uuid,
        saved_parlay_id=None,
        data_hash="0" * 64,
        status=VerificationStatus.queued.value,
        network=str(getattr(settings, "verification_network", "mainnet") or "mainnet"),
        error=None,
    )
    db.add(record)
    await db.commit()

    get_public = await client.get(f"/api/public/verification-records/{record_id}")
    assert get_public.status_code == 200, get_public.text
    payload = get_public.json()
    assert payload["id"] == str(record_id)
    assert str(payload.get("viewer_url", "")).startswith("/verification-records/")


@pytest.mark.asyncio
async def test_retry_does_not_double_charge_credits(client: AsyncClient, db, monkeypatch):
    # Stub out Redis enqueue.
    class FakeVerificationQueue:
        async def enqueue_verification_record(self, *, verification_record_id: str, saved_parlay_id: str) -> str:
            _ = (verification_record_id, saved_parlay_id)
            return "job-test-1"

    import app.services.verification_records.saved_parlay_verification_service as svc_mod

    monkeypatch.setattr(svc_mod, "VerificationQueue", lambda: FakeVerificationQueue())

    # Premium user with exhausted quota and some credits.
    reg = await client.post("/api/auth/register", json={"email": "vr-retry@test.com", "password": "Passw0rd!"})
    token = reg.json()["access_token"]
    user_uuid = uuid.UUID(reg.json()["user"]["id"])

    now = datetime.now(timezone.utc)
    db.add(
        Subscription(
            id=uuid.uuid4(),
            user_id=user_uuid,
            plan="PG_PREMIUM_MONTHLY",
            provider="lemonsqueezy",
            provider_subscription_id="ls_sub_test_vr_retry",
            provider_customer_id="ls_cust_test_vr_retry",
            status=SubscriptionStatus.active.value,
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
            cancel_at_period_end=False,
            is_lifetime=False,
        )
    )

    user_row = (await db.execute(select(User).where(User.id == user_uuid))).scalar_one()
    user_row.premium_inscriptions_period_start = now
    user_row.premium_inscriptions_used = int(settings.premium_inscriptions_per_month)
    user_row.credit_balance = 10
    await db.commit()

    save = await client.post(
        "/api/parlays/custom/save",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Retry Ticket",
            "legs": [{"game_id": "00000000-0000-0000-0000-000000000001", "pick": "home", "market_type": "spreads", "point": -3.5}],
        },
    )
    saved_id = save.json()["id"]
    saved_uuid = uuid.UUID(saved_id)

    # Insert a failed record that already consumed credits.
    failed = VerificationRecord(
        id=uuid.uuid4(),
        user_id=user_uuid,
        saved_parlay_id=saved_uuid,
        data_hash=str(save.json()["content_hash"]),
        status=VerificationStatus.failed.value,
        network=str(getattr(settings, "verification_network", "mainnet") or "mainnet"),
        error="worker failed",
        credits_consumed=True,
        quota_consumed=False,
    )
    db.add(failed)
    await db.commit()

    before = (await db.execute(select(User.credit_balance).where(User.id == user_uuid))).scalar_one()

    retry = await client.post(
        f"/api/parlays/{saved_id}/verification/retry",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert retry.status_code == 200, retry.text

    after = (await db.execute(select(User.credit_balance).where(User.id == user_uuid))).scalar_one()
    assert int(after) == int(before)


@pytest.mark.asyncio
async def test_queue_and_get_under_db_delivery(client: AsyncClient, db, monkeypatch):
    """With VERIFICATION_DELIVERY=db, queue endpoint succeeds without Redis; record is queued."""
    monkeypatch.setattr("app.core.config.settings.verification_delivery", "db")
    import app.services.verification_records.saved_parlay_verification_service as svc_mod

    class FailingQueue:
        def is_available(self):
            return False

        async def enqueue_verification_record(self, *, verification_record_id: str, saved_parlay_id: str) -> str:
            raise RuntimeError("Redis not configured")

    monkeypatch.setattr(svc_mod, "VerificationQueue", lambda: FailingQueue())

    reg = await client.post("/api/auth/register", json={"email": "vr-db-delivery@test.com", "password": "Passw0rd!"})
    assert reg.status_code == 200, reg.text
    token = reg.json()["access_token"]
    user_uuid = uuid.UUID(reg.json()["user"]["id"])

    now = datetime.now(timezone.utc)
    db.add(
        Subscription(
            id=uuid.uuid4(),
            user_id=user_uuid,
            plan="PG_PREMIUM_MONTHLY",
            provider="lemonsqueezy",
            provider_subscription_id="ls_sub_test_vr_db",
            provider_customer_id="ls_cust_test_vr_db",
            status=SubscriptionStatus.active.value,
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
            cancel_at_period_end=False,
            is_lifetime=False,
        )
    )
    await db.commit()

    save = await client.post(
        "/api/parlays/custom/save",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "DB Delivery Ticket",
            "legs": [{"game_id": "00000000-0000-0000-0000-000000000001", "pick": "home", "market_type": "spreads", "point": -3.5}],
        },
    )
    assert save.status_code == 200, save.text
    saved_id = save.json()["id"]

    queued = await client.post(
        f"/api/parlays/{saved_id}/verification/queue",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert queued.status_code == 200, queued.text
    payload = queued.json()
    assert payload["id"]
    assert payload["status"] == VerificationStatus.queued.value


