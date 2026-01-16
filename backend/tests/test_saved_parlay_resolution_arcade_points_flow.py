from __future__ import annotations

from datetime import datetime, timedelta, timezone
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.arcade_points_totals import ArcadePointsTotals
from app.models.game import Game
from app.models.game_results import GameResult
from app.models.saved_parlay import SavedParlay
from app.models.user import User
from app.models.verification_record import VerificationRecord, VerificationStatus
from app.services.saved_parlay_tracker import SavedParlayTrackerService
from app.services.scheduler_jobs.arcade_points_award_job import ArcadePointsAwardJob


async def _register_and_profile(client: AsyncClient, *, email: str, display_name: str) -> str:
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
    return token


async def _get_user(db: AsyncSession, *, email: str) -> User:
    res = await db.execute(select(User).where(User.email == email).limit(1))
    return res.scalar_one()


@pytest.mark.asyncio
async def test_saved_custom_parlay_resolution_awards_arcade_points_and_updates_public_leaderboard(
    client: AsyncClient,
    db: AsyncSession,
):
    now = datetime.now(timezone.utc)

    game_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    game_start = now - timedelta(hours=6)
    db.add(
        Game(
            id=game_id,
            external_game_id="evt_arcade_integration_1",
            sport="NFL",
            home_team="Home Team",
            away_team="Away Team",
            start_time=game_start,
            status="final",
        )
    )
    db.add(
        GameResult(
            game_id=game_id,
            external_game_id="evt_arcade_integration_1",
            sport="NFL",
            home_team="Home Team",
            away_team="Away Team",
            game_date=game_start,
            home_score=24,
            away_score=17,
            winner="home",
            status="final",
            completed="true",
        )
    )
    await db.commit()

    email = "arcade-flow@test.com"
    display_name = "ArcadeFlow"
    token = await _register_and_profile(client, email=email, display_name=display_name)
    user = await _get_user(db, email=email)

    save = await client.post(
        "/api/parlays/custom/save",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Arcade integration test (5-leg)",
            "legs": [
                {"game_id": str(game_id), "pick": "home", "market_type": "h2h"},
                {"game_id": str(game_id), "pick": "home", "market_type": "h2h"},
                {"game_id": str(game_id), "pick": "home", "market_type": "h2h"},
                {"game_id": str(game_id), "pick": "home", "market_type": "h2h"},
                {"game_id": str(game_id), "pick": "home", "market_type": "h2h"},
            ],
        },
    )
    assert save.status_code == 200, save.text
    saved_parlay_id = uuid.UUID(save.json()["id"])

    res = await db.execute(select(SavedParlay).where(SavedParlay.id == saved_parlay_id).limit(1))
    saved = res.scalar_one()

    db.add(
        VerificationRecord(
            id=uuid.uuid4(),
            user_id=user.id,
            saved_parlay_id=saved.id,
            data_hash=str(saved.content_hash),
            status=VerificationStatus.confirmed.value,
            tx_digest="tx-arcade-flow",
            network="mainnet",
            quota_consumed=True,
            credits_consumed=False,
        )
    )
    await db.commit()

    resolved = await SavedParlayTrackerService(db).resolve_saved_parlay_if_needed(saved_parlay=saved)
    assert resolved is not None
    assert resolved.hit is True
    assert resolved.num_legs == 5
    assert isinstance(resolved.leg_results, list)
    assert all((lr or {}).get("status") == "hit" for lr in resolved.leg_results)

    awarded = await ArcadePointsAwardJob()._award_eligible_wins(db)
    assert awarded == 1

    totals_res = await db.execute(select(ArcadePointsTotals).where(ArcadePointsTotals.user_id == user.id).limit(1))
    totals = totals_res.scalar_one_or_none()
    assert totals is not None
    assert totals.total_points == 100

    lb = await client.get("/api/leaderboards/arcade-points?period=all_time&limit=10")
    assert lb.status_code == 200, lb.text
    leaderboard = lb.json().get("leaderboard") or []
    assert any(row.get("username") == display_name and row.get("total_points") == 100 for row in leaderboard)

