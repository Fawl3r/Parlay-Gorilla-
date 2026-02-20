from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.models.verification_record import VerificationRecord, VerificationStatus
from app.schemas.parlay import CustomParlayLeg, CustomParlayLegAnalysis
from app.services.custom_parlay_verification.auto_verification_service import CustomParlayAutoVerificationService


class _UnavailableQueue:
    """Queue that is not available (e.g. Redis down). Used for db-delivery tests."""

    def is_available(self) -> bool:
        return False

    async def enqueue_verification_record(
        self, *, verification_record_id: str, saved_parlay_id: str, job_name: str = "verify_saved_parlay"
    ) -> str:
        raise RuntimeError("Redis not configured")


class _StubQueue:
    def __init__(self):
        self.enqueued: list[dict] = []

    def is_available(self) -> bool:
        return True

    async def enqueue_verification_record(self, *, verification_record_id: str, saved_parlay_id: str, job_name: str = "verify_saved_parlay") -> str:
        self.enqueued.append(
            {
                "verification_record_id": verification_record_id,
                "saved_parlay_id": saved_parlay_id,
                "job_name": job_name,
            }
        )
        return "job-1"


def _analysis_leg(game_id: str, market_type: str, pick: str, odds: str) -> CustomParlayLegAnalysis:
    return CustomParlayLegAnalysis(
        game_id=game_id,
        game="Away @ Home",
        home_team="Home",
        away_team="Away",
        sport="NFL",
        market_type=market_type,
        pick=pick,
        pick_display=f"{pick} {market_type}",
        odds=odds,
        decimal_odds=1.91,
        implied_probability=52.3,
        ai_probability=53.1,
        confidence=55.0,
        edge=0.8,
        recommendation="moderate",
    )


@pytest.mark.asyncio
async def test_auto_verification_is_idempotent_for_same_fingerprint(db):
    user = User(id=uuid.uuid4(), email="fp-idempotent@example.com")
    db.add(user)
    await db.commit()
    await db.refresh(user)

    req_legs = [
        CustomParlayLeg(game_id="00000000-0000-0000-0000-000000000001", market_type="h2h", pick="home", odds="-110"),
        CustomParlayLeg(game_id="00000000-0000-0000-0000-000000000002", market_type="totals", pick="over", point=44.5, odds="-105"),
    ]
    analysis_legs = [
        _analysis_leg(req_legs[0].game_id, "h2h", "home", "-110"),
        _analysis_leg(req_legs[1].game_id, "totals", "over", "-105"),
    ]

    now = datetime(2026, 1, 8, 12, 0, 1, tzinfo=timezone.utc)
    queue = _StubQueue()
    svc = CustomParlayAutoVerificationService(db, queue=queue)

    r1 = await svc.ensure_verification_record(user=user, request_legs=req_legs, analysis_legs=analysis_legs, now_utc=now)
    assert r1 is not None
    assert r1.parlay_fingerprint
    assert r1.data_hash == r1.parlay_fingerprint
    assert len(queue.enqueued) == 1

    r2 = await svc.ensure_verification_record(user=user, request_legs=req_legs, analysis_legs=analysis_legs, now_utc=now)
    assert r2 is not None
    assert str(r2.id) == str(r1.id)
    # Should not enqueue a second time for already queued record
    assert len(queue.enqueued) == 1


@pytest.mark.asyncio
async def test_db_uniqueness_enforces_one_record_per_fingerprint(db):
    user = User(id=uuid.uuid4(), email="fp-unique@example.com")
    db.add(user)
    await db.commit()
    await db.refresh(user)

    queue = _StubQueue()
    svc = CustomParlayAutoVerificationService(db, queue=queue)

    req_legs = [
        CustomParlayLeg(game_id="00000000-0000-0000-0000-000000000003", market_type="h2h", pick="away", odds="+120"),
    ]
    analysis_legs = [_analysis_leg(req_legs[0].game_id, "h2h", "away", "+120")]
    now = datetime(2026, 1, 8, 12, 0, 1, tzinfo=timezone.utc)

    rec = await svc.ensure_verification_record(user=user, request_legs=req_legs, analysis_legs=analysis_legs, now_utc=now)
    assert rec is not None

    # Attempt to insert a second row with the same fingerprint should fail.
    dup = VerificationRecord(
        id=uuid.uuid4(),
        user_id=user.id,
        saved_parlay_id=None,
        parlay_fingerprint=rec.parlay_fingerprint,
        data_hash=rec.parlay_fingerprint,
        status="queued",
        network="mainnet",
        error=None,
        tx_digest=None,
        object_id=None,
        quota_consumed=False,
        credits_consumed=False,
    )
    db.add(dup)
    with pytest.raises(IntegrityError):
        await db.commit()


@pytest.mark.asyncio
async def test_db_delivery_creates_queued_record_without_redis(db, monkeypatch):
    """When VERIFICATION_DELIVERY=db, a queued record is created and no enqueue is attempted."""
    monkeypatch.setattr("app.services.custom_parlay_verification.auto_verification_service.settings.verification_delivery", "db")

    user = User(id=uuid.uuid4(), email="fp-db-delivery@example.com")
    db.add(user)
    await db.commit()
    await db.refresh(user)

    queue = _UnavailableQueue()
    svc = CustomParlayAutoVerificationService(db, queue=queue)

    req_legs = [
        CustomParlayLeg(game_id="00000000-0000-0000-0000-000000000004", market_type="h2h", pick="home", odds="-110"),
    ]
    analysis_legs = [_analysis_leg(req_legs[0].game_id, "h2h", "home", "-110")]
    now = datetime(2026, 1, 8, 12, 0, 1, tzinfo=timezone.utc)

    rec = await svc.ensure_verification_record(user=user, request_legs=req_legs, analysis_legs=analysis_legs, now_utc=now)
    assert rec is not None
    assert rec.status == VerificationStatus.queued.value
    assert rec.parlay_fingerprint
    assert rec.error is None
    # Queue was never used (db delivery skips enqueue).
    assert not hasattr(queue, "enqueued") or getattr(queue, "enqueued", []) == []


@pytest.mark.asyncio
async def test_db_delivery_requeues_existing_failed_record(db, monkeypatch):
    """When VERIFICATION_DELIVERY=db and existing record is failed, status is set back to queued."""
    monkeypatch.setattr("app.services.custom_parlay_verification.auto_verification_service.settings.verification_delivery", "db")

    user = User(id=uuid.uuid4(), email="fp-db-requeue@example.com")
    db.add(user)
    await db.commit()
    await db.refresh(user)

    queue = _UnavailableQueue()
    svc = CustomParlayAutoVerificationService(db, queue=queue)

    req_legs = [
        CustomParlayLeg(game_id="00000000-0000-0000-0000-000000000005", market_type="h2h", pick="away", odds="+100"),
    ]
    analysis_legs = [_analysis_leg(req_legs[0].game_id, "h2h", "away", "+100")]
    now = datetime(2026, 1, 8, 12, 0, 1, tzinfo=timezone.utc)

    r1 = await svc.ensure_verification_record(user=user, request_legs=req_legs, analysis_legs=analysis_legs, now_utc=now)
    assert r1 is not None
    assert r1.status == VerificationStatus.queued.value

    # Simulate verifier having marked it failed (e.g. transient error).
    r1.status = VerificationStatus.failed.value
    r1.error = "Enqueue failed: ResponseError"
    db.add(r1)
    await db.commit()
    await db.refresh(r1)

    # Same fingerprint again: service should set status back to queued (retry path in db mode).
    r2 = await svc.ensure_verification_record(user=user, request_legs=req_legs, analysis_legs=analysis_legs, now_utc=now)
    assert r2 is not None
    assert str(r2.id) == str(r1.id)
    assert r2.status == VerificationStatus.queued.value
    assert r2.error is None


