"""Tests for arcade points leaderboard system."""

import pytest
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.models.saved_parlay import SavedParlay, SavedParlayType
from app.models.saved_parlay_results import SavedParlayResult
from app.models.user import User
from app.models.verification_record import VerificationRecord, VerificationStatus
from app.models.arcade_points_event import ArcadePointsEvent
from app.models.arcade_points_totals import ArcadePointsTotals
from app.services.leaderboards.arcade_points_calculator import ArcadePointsCalculator
from app.services.scheduler_jobs.arcade_points_award_job import ArcadePointsAwardJob


async def _register_and_profile(client: AsyncClient, *, email: str, display_name: str, visibility: str = "public") -> str:
    reg = await client.post("/api/auth/register", json={"email": email, "password": "Passw0rd!"})
    assert reg.status_code == 200, reg.text
    token = reg.json()["access_token"]

    prof = await client.post(
        "/api/profile/setup",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "display_name": display_name,
            "default_risk_profile": "balanced",
            "favorite_teams": [],
            "favorite_sports": [],
        },
    )
    assert prof.status_code == 200, prof.text

    # Profile setup does not accept leaderboard_visibility; update it separately when needed.
    if visibility and visibility != "public":
        upd = await client.put(
            "/api/profile/me",
            headers={"Authorization": f"Bearer {token}"},
            json={"leaderboard_visibility": visibility},
        )
        assert upd.status_code == 200, upd.text

    return token


async def _get_user_id(db: AsyncSession, *, email: str) -> str:
    res = await db.execute(select(User).where(User.email == email).limit(1))
    user = res.scalar_one()
    return str(user.id)


@pytest.mark.asyncio
async def test_arcade_points_calculator_tiered_scoring():
    """Test tiered points calculation."""
    assert ArcadePointsCalculator.calculate_points(4) == 0  # < 5 legs = 0
    assert ArcadePointsCalculator.calculate_points(5) == 100
    assert ArcadePointsCalculator.calculate_points(6) == 140
    assert ArcadePointsCalculator.calculate_points(7) == 200
    assert ArcadePointsCalculator.calculate_points(8) == 280
    assert ArcadePointsCalculator.calculate_points(9) == 400
    assert ArcadePointsCalculator.calculate_points(10) == 560

    # 11+ legs: 560 * 1.25 = 700
    assert ArcadePointsCalculator.calculate_points(11) == 700
    # 12 legs: 700 * 1.25 = 875
    assert ArcadePointsCalculator.calculate_points(12) == 875
    # 13 legs: 875 * 1.25 = 1093 (rounded)
    assert ArcadePointsCalculator.calculate_points(13) == 1093

    # Cap test
    points_20 = ArcadePointsCalculator.calculate_points(20)
    assert points_20 <= ArcadePointsCalculator.MAX_POINTS_PER_WIN


@pytest.mark.asyncio
async def test_arcade_points_award_eligibility(client: AsyncClient, db: AsyncSession):
    """Test that points are only awarded for eligible wins."""
    email = "arcade-test@test.com"
    token = await _register_and_profile(client, email=email, display_name="ArcadeTester")
    user_id = await _get_user_id(db, email=email)

    # Create a 5-leg custom parlay
    save_resp = await client.post(
        "/api/parlays/custom/save",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "5-leg winner",
            "legs": [
                {"game_id": "00000000-0000-0000-0000-000000000001", "pick": "home", "market_type": "spreads", "point": -3.5},
                {"game_id": "00000000-0000-0000-0000-000000000002", "pick": "away", "market_type": "spreads", "point": 3.5},
                {"game_id": "00000000-0000-0000-0000-000000000003", "pick": "home", "market_type": "totals", "point": 45.5},
                {"game_id": "00000000-0000-0000-0000-000000000004", "pick": "away", "market_type": "totals", "point": 50.5},
                {"game_id": "00000000-0000-0000-0000-000000000005", "pick": "home", "market_type": "spreads", "point": -1.5},
            ],
        },
    )
    assert save_resp.status_code == 200, save_resp.text
    saved_parlay_id = save_resp.json()["id"]

    # Get saved parlay to get content_hash
    saved_res = await db.execute(select(SavedParlay).where(SavedParlay.id == saved_parlay_id).limit(1))
    saved_parlay = saved_res.scalar_one()

    # Create verification record (confirmed, matching content_hash)
    verification = VerificationRecord(
        id=uuid.uuid4(),
        user_id=user_id,
        saved_parlay_id=saved_parlay_id,
        data_hash=str(saved_parlay.content_hash),
        status=VerificationStatus.confirmed.value,
        tx_digest="tx-test",
        network="mainnet",
        quota_consumed=True,
        credits_consumed=False,
    )
    db.add(verification)

    # Create winning result
    now = datetime.now(timezone.utc)
    result = SavedParlayResult(
        id=uuid.uuid4(),
        saved_parlay_id=saved_parlay_id,
        user_id=user_id,
        parlay_type=SavedParlayType.custom.value,
        num_legs=5,
        hit=True,
        legs_hit=5,
        legs_missed=0,
        leg_results=[{"status": "hit"} for _ in range(5)],
        resolved_at=now,
    )
    db.add(result)
    await db.commit()

    # Run award job
    job = ArcadePointsAwardJob()
    awarded = await job._award_eligible_wins(db)
    assert awarded == 1

    # Check event was created
    event_res = await db.execute(
        select(ArcadePointsEvent).where(ArcadePointsEvent.saved_parlay_result_id == result.id).limit(1)
    )
    event = event_res.scalar_one_or_none()
    assert event is not None
    assert event.points_awarded == 100
    assert event.num_legs == 5

    # Check totals were updated
    totals_res = await db.execute(select(ArcadePointsTotals).where(ArcadePointsTotals.user_id == user_id).limit(1))
    totals = totals_res.scalar_one_or_none()
    assert totals is not None
    assert totals.total_points == 100
    assert totals.total_qualifying_wins == 1


@pytest.mark.asyncio
async def test_arcade_points_not_awarded_for_4_legs(client: AsyncClient, db: AsyncSession):
    """Test that 4-leg wins don't earn points."""
    email = "arcade-4leg@test.com"
    token = await _register_and_profile(client, email=email, display_name="FourLeg")
    user_id = await _get_user_id(db, email=email)

    # Create a 4-leg custom parlay
    save_resp = await client.post(
        "/api/parlays/custom/save",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "4-leg winner (no points)",
            "legs": [
                {"game_id": "00000000-0000-0000-0000-000000000001", "pick": "home", "market_type": "spreads", "point": -3.5},
                {"game_id": "00000000-0000-0000-0000-000000000002", "pick": "away", "market_type": "spreads", "point": 3.5},
                {"game_id": "00000000-0000-0000-0000-000000000003", "pick": "home", "market_type": "totals", "point": 45.5},
                {"game_id": "00000000-0000-0000-0000-000000000004", "pick": "away", "market_type": "totals", "point": 50.5},
            ],
        },
    )
    assert save_resp.status_code == 200, save_resp.text
    saved_parlay_id = save_resp.json()["id"]

    saved_res = await db.execute(select(SavedParlay).where(SavedParlay.id == saved_parlay_id).limit(1))
    saved_parlay = saved_res.scalar_one()

    # Create verification record
    verification = VerificationRecord(
        id=uuid.uuid4(),
        user_id=user_id,
        saved_parlay_id=saved_parlay_id,
        data_hash=str(saved_parlay.content_hash),
        status=VerificationStatus.confirmed.value,
        tx_digest="tx-4leg",
        network="mainnet",
        quota_consumed=True,
        credits_consumed=False,
    )
    db.add(verification)

    # Create winning result (4 legs)
    now = datetime.now(timezone.utc)
    result = SavedParlayResult(
        id=uuid.uuid4(),
        saved_parlay_id=saved_parlay_id,
        user_id=user_id,
        parlay_type=SavedParlayType.custom.value,
        num_legs=4,
        hit=True,
        legs_hit=4,
        legs_missed=0,
        leg_results=[{"status": "hit"} for _ in range(4)],
        resolved_at=now,
    )
    db.add(result)
    await db.commit()

    # Run award job
    job = ArcadePointsAwardJob()
    awarded = await job._award_eligible_wins(db)
    assert awarded == 0  # 4 legs = no points

    # Check no event was created
    event_res = await db.execute(
        select(ArcadePointsEvent).where(ArcadePointsEvent.saved_parlay_result_id == result.id).limit(1)
    )
    event = event_res.scalar_one_or_none()
    assert event is None


@pytest.mark.asyncio
async def test_arcade_points_leaderboard_ordering(client: AsyncClient, db: AsyncSession):
    """Test leaderboard ordering by points."""
    # Create users with different point totals
    email_a = "arcade-a@test.com"
    email_b = "arcade-b@test.com"
    token_a = await _register_and_profile(client, email=email_a, display_name="HighScorer")
    token_b = await _register_and_profile(client, email=email_b, display_name="LowScorer")

    user_a_id = await _get_user_id(db, email=email_a)
    user_b_id = await _get_user_id(db, email=email_b)

    # Manually create totals (simulating awarded points)
    totals_a = ArcadePointsTotals(
        user_id=user_a_id,
        total_points=500,
        total_qualifying_wins=3,
        last_win_at=datetime.now(timezone.utc),
    )
    totals_b = ArcadePointsTotals(
        user_id=user_b_id,
        total_points=200,
        total_qualifying_wins=1,
        last_win_at=datetime.now(timezone.utc) - timedelta(days=1),
    )
    db.add(totals_a)
    db.add(totals_b)
    await db.commit()

    # Fetch leaderboard
    resp = await client.get("/api/leaderboards/arcade-points?period=all_time&limit=10")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert len(data["leaderboard"]) >= 2
    # HighScorer should rank first
    assert data["leaderboard"][0]["username"] == "HighScorer"
    assert data["leaderboard"][0]["total_points"] == 500
    assert data["leaderboard"][1]["username"] == "LowScorer"
    assert data["leaderboard"][1]["total_points"] == 200


@pytest.mark.asyncio
async def test_arcade_points_hidden_users_excluded(client: AsyncClient, db: AsyncSession):
    """Test that hidden users don't appear in leaderboard."""
    email_public = "arcade-public@test.com"
    email_hidden = "arcade-hidden@test.com"
    await _register_and_profile(client, email=email_public, display_name="PublicUser", visibility="public")
    await _register_and_profile(client, email=email_hidden, display_name="HiddenUser", visibility="hidden")

    user_public_id = await _get_user_id(db, email=email_public)
    user_hidden_id = await _get_user_id(db, email=email_hidden)

    # Create totals for both
    totals_public = ArcadePointsTotals(
        user_id=user_public_id,
        total_points=300,
        total_qualifying_wins=2,
        last_win_at=datetime.now(timezone.utc),
    )
    totals_hidden = ArcadePointsTotals(
        user_id=user_hidden_id,
        total_points=1000,  # Even with more points, hidden users are excluded
        total_qualifying_wins=5,
        last_win_at=datetime.now(timezone.utc),
    )
    db.add(totals_public)
    db.add(totals_hidden)
    await db.commit()

    # Fetch leaderboard
    resp = await client.get("/api/leaderboards/arcade-points?period=all_time&limit=10")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    # Only public user should appear
    usernames = [entry["username"] for entry in data["leaderboard"]]
    assert "PublicUser" in usernames
    assert "HiddenUser" not in usernames


@pytest.mark.asyncio
async def test_recent_wins_feed_ordering(client: AsyncClient, db: AsyncSession):
    """Test recent wins feed returns wins in correct order."""
    email = "arcade-feed@test.com"
    token = await _register_and_profile(client, email=email, display_name="FeedTester")
    user_id = await _get_user_id(db, email=email)

    # Create saved parlays + results + events with different timestamps
    now = datetime.now(timezone.utc)

    saved_ids: list[str] = []
    for idx in range(3):
        save_resp = await client.post(
            "/api/parlays/custom/save",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": f"Feed Ticket {idx}",
                "legs": [
                    {
                        "game_id": f"00000000-0000-0000-0000-00000000000{idx + 1}",
                        "pick": "home",
                        "market_type": "spreads",
                        "point": -3.5,
                    }
                ],
            },
        )
        assert save_resp.status_code == 200, save_resp.text
        saved_ids.append(save_resp.json()["id"])

    # Create matching saved_parlay_results (for FK integrity) + arcade_points_events
    result_ids: list[uuid.UUID] = [uuid.uuid4(), uuid.uuid4(), uuid.uuid4()]
    created_ats = [now - timedelta(hours=3), now - timedelta(hours=1), now]
    legs = [5, 6, 7]
    points = [100, 140, 200]

    for sid, rid, created_at, num_legs, pts in zip(saved_ids, result_ids, created_ats, legs, points):
        db.add(
            SavedParlayResult(
                id=rid,
                saved_parlay_id=sid,
                user_id=user_id,
                parlay_type=SavedParlayType.custom.value,
                num_legs=num_legs,
                hit=True,
                legs_hit=num_legs,
                legs_missed=0,
                leg_results=[{"status": "hit"} for _ in range(num_legs)],
                resolved_at=created_at,
            )
        )
        db.add(
            ArcadePointsEvent(
                id=uuid.uuid4(),
                user_id=user_id,
                saved_parlay_id=sid,
                saved_parlay_result_id=rid,
                num_legs=num_legs,
                points_awarded=pts,
                created_at=created_at,
            )
        )

    await db.commit()

    # Fetch feed
    resp = await client.get("/api/leaderboards/arcade-wins?limit=10")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert len(data["wins"]) >= 3
    # Should be ordered by most recent first
    assert data["wins"][0]["points_awarded"] == 200  # Most recent
    assert data["wins"][1]["points_awarded"] == 140
    assert data["wins"][2]["points_awarded"] == 100  # Oldest


@pytest.mark.asyncio
async def test_arcade_points_requires_verified_and_current_hash(client: AsyncClient, db: AsyncSession):
    """Test that points require confirmed verification with matching content_hash."""
    email = "arcade-verify@test.com"
    token = await _register_and_profile(client, email=email, display_name="VerifyTest")
    user_id = await _get_user_id(db, email=email)

    # Create a 5-leg custom parlay
    save_resp = await client.post(
        "/api/parlays/custom/save",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "5-leg winner",
            "legs": [
                {"game_id": "00000000-0000-0000-0000-000000000001", "pick": "home", "market_type": "spreads", "point": -3.5},
                {"game_id": "00000000-0000-0000-0000-000000000002", "pick": "away", "market_type": "spreads", "point": 3.5},
                {"game_id": "00000000-0000-0000-0000-000000000003", "pick": "home", "market_type": "totals", "point": 45.5},
                {"game_id": "00000000-0000-0000-0000-000000000004", "pick": "away", "market_type": "totals", "point": 50.5},
                {"game_id": "00000000-0000-0000-0000-000000000005", "pick": "home", "market_type": "spreads", "point": -1.5},
            ],
        },
    )
    assert save_resp.status_code == 200, save_resp.text
    saved_parlay_id = save_resp.json()["id"]

    saved_res = await db.execute(select(SavedParlay).where(SavedParlay.id == saved_parlay_id).limit(1))
    saved_parlay = saved_res.scalar_one()

    # Create verification record with WRONG hash (should not award)
    verification_wrong = VerificationRecord(
        id=uuid.uuid4(),
        user_id=user_id,
        saved_parlay_id=saved_parlay_id,
        data_hash="wrong_hash",
        status=VerificationStatus.confirmed.value,
        tx_digest="tx-wrong",
        network="mainnet",
        quota_consumed=True,
        credits_consumed=False,
    )
    db.add(verification_wrong)

    # Create winning result
    now = datetime.now(timezone.utc)
    result = SavedParlayResult(
        id=uuid.uuid4(),
        saved_parlay_id=saved_parlay_id,
        user_id=user_id,
        parlay_type=SavedParlayType.custom.value,
        num_legs=5,
        hit=True,
        legs_hit=5,
        legs_missed=0,
        leg_results=[{"status": "hit"} for _ in range(5)],
        resolved_at=now,
    )
    db.add(result)
    await db.commit()

    # Run award job - should not award (wrong hash)
    job = ArcadePointsAwardJob()
    awarded = await job._award_eligible_wins(db)
    assert awarded == 0

    # Now add correct verification
    verification_correct = VerificationRecord(
        id=uuid.uuid4(),
        user_id=user_id,
        saved_parlay_id=saved_parlay_id,
        data_hash=str(saved_parlay.content_hash),
        status=VerificationStatus.confirmed.value,
        tx_digest="tx-correct",
        network="mainnet",
        quota_consumed=True,
        credits_consumed=False,
    )
    db.add(verification_correct)
    await db.commit()

    # Run again - should award now
    awarded = await job._award_eligible_wins(db)
    assert awarded == 1

