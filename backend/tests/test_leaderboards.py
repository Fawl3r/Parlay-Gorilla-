import pytest
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.parlay import Parlay
from app.models.saved_parlay import InscriptionStatus, SavedParlay
from app.models.saved_parlay_results import SavedParlayResult
from app.models.user import User


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


async def _get_user_id(db: AsyncSession, *, email: str) -> str:
    res = await db.execute(select(User).where(User.email == email).limit(1))
    user = res.scalar_one()
    return str(user.id)


@pytest.mark.asyncio
async def test_verified_winners_leaderboard_qualification_and_sorting(client: AsyncClient, db: AsyncSession):
    # Create users
    email_a = "lb-a@test.com"
    email_b = "lb-b@test.com"
    token_a = await _register_and_profile(client, email=email_a, display_name="GorillaKing")
    token_b = await _register_and_profile(client, email=email_b, display_name="SharpApe")

    # Save custom parlays for each
    save_a_1 = await client.post(
        "/api/parlays/custom/save",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "title": "A1",
            "legs": [{"game_id": "00000000-0000-0000-0000-000000000001", "pick": "home", "market_type": "spreads", "point": -3.5}],
        },
    )
    assert save_a_1.status_code == 200, save_a_1.text
    a1_id = save_a_1.json()["id"]

    save_a_2 = await client.post(
        "/api/parlays/custom/save",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "title": "A2",
            "legs": [{"game_id": "00000000-0000-0000-0000-000000000002", "pick": "away", "market_type": "spreads", "point": 3.5}],
        },
    )
    assert save_a_2.status_code == 200, save_a_2.text
    a2_id = save_a_2.json()["id"]

    save_b_1 = await client.post(
        "/api/parlays/custom/save",
        headers={"Authorization": f"Bearer {token_b}"},
        json={
            "title": "B1",
            "legs": [{"game_id": "00000000-0000-0000-0000-000000000003", "pick": "home", "market_type": "spreads", "point": -1.5}],
        },
    )
    assert save_b_1.status_code == 200, save_b_1.text
    b1_id = save_b_1.json()["id"]

    save_b_2 = await client.post(
        "/api/parlays/custom/save",
        headers={"Authorization": f"Bearer {token_b}"},
        json={
            "title": "B2",
            "legs": [{"game_id": "00000000-0000-0000-0000-000000000004", "pick": "away", "market_type": "spreads", "point": 1.5}],
        },
    )
    assert save_b_2.status_code == 200, save_b_2.text
    b2_id = save_b_2.json()["id"]

    # Mark all as confirmed inscriptions (selective policy: only custom can be confirmed)
    for sid, tx in [(a1_id, "tx-a1"), (a2_id, "tx-a2"), (b1_id, "tx-b1"), (b2_id, "tx-b2-latest")]:
        res = await db.execute(select(SavedParlay).where(SavedParlay.id == sid).limit(1))
        saved = res.scalar_one()
        saved.inscription_status = InscriptionStatus.confirmed.value
        saved.inscription_tx = tx
        db.add(saved)
    await db.commit()

    # Insert results:
    # - A: 1 win + 1 loss => win_rate 0.5
    # - B: 2 wins => win_rate 1.0
    now = datetime.now(timezone.utc)

    user_a_id = await _get_user_id(db, email=email_a)
    user_b_id = await _get_user_id(db, email=email_b)

    results = [
        SavedParlayResult(
            id=None,
            saved_parlay_id=a1_id,
            user_id=user_a_id,
            parlay_type="custom",
            num_legs=1,
            hit=True,
            legs_hit=1,
            legs_missed=0,
            leg_results=[{"status": "hit"}],
            resolved_at=now - timedelta(days=2),
        ),
        SavedParlayResult(
            id=None,
            saved_parlay_id=a2_id,
            user_id=user_a_id,
            parlay_type="custom",
            num_legs=1,
            hit=False,
            legs_hit=0,
            legs_missed=1,
            leg_results=[{"status": "missed"}],
            resolved_at=now - timedelta(days=1),
        ),
        SavedParlayResult(
            id=None,
            saved_parlay_id=b1_id,
            user_id=user_b_id,
            parlay_type="custom",
            num_legs=1,
            hit=True,
            legs_hit=1,
            legs_missed=0,
            leg_results=[{"status": "hit"}],
            resolved_at=now - timedelta(days=3),
        ),
        SavedParlayResult(
            id=None,
            saved_parlay_id=b2_id,
            user_id=user_b_id,
            parlay_type="custom",
            num_legs=1,
            hit=True,
            legs_hit=1,
            legs_missed=0,
            leg_results=[{"status": "hit"}],
            resolved_at=now,
        ),
    ]

    for r in results:
        db.add(r)
    await db.commit()

    lb = await client.get("/api/leaderboards/custom?limit=10")
    assert lb.status_code == 200, lb.text
    data = lb.json()
    assert "leaderboard" in data
    assert len(data["leaderboard"]) >= 2

    # B should rank above A due to more wins.
    top = data["leaderboard"][0]
    second = data["leaderboard"][1]
    assert top["username"] == "SharpApe"
    assert top["verified_wins"] == 2
    assert top["inscription_id"] in ("tx-b2-latest", "tx-b1")

    assert second["username"] == "GorillaKing"
    assert second["verified_wins"] == 1
    assert 0.0 <= float(second["win_rate"]) <= 1.0


@pytest.mark.asyncio
async def test_ai_usage_leaderboard_counts_parlays_and_custom_saves(client: AsyncClient, db: AsyncSession):
    email_a = "usage-a@test.com"
    email_b = "usage-b@test.com"
    await _register_and_profile(client, email=email_a, display_name="UsageApe")
    await _register_and_profile(client, email=email_b, display_name="GrinderGorilla")

    # Fetch user IDs
    res = await db.execute(select(User).where(User.email.in_([email_a, email_b])))
    users = {u.email: u for u in res.scalars().all()}
    user_a = users[email_a]
    user_b = users[email_b]

    # Insert parlay generations
    for _ in range(7):
        db.add(
            Parlay(
                user_id=user_a.id,
                legs=[{"market_id": "m1", "outcome": "home"}],
                num_legs=1,
                parlay_hit_prob=0.5,
                risk_profile="balanced",
            )
        )
    for _ in range(10):
        db.add(
            Parlay(
                user_id=user_b.id,
                legs=[{"market_id": "m1", "outcome": "home"}],
                num_legs=1,
                parlay_hit_prob=0.5,
                risk_profile="balanced",
            )
        )
    await db.commit()

    # Add two custom saves for user A (counts toward baseline)
    save_a = await client.post(
        "/api/auth/login",
        json={"email": email_a, "password": "Passw0rd!"},
    )
    assert save_a.status_code == 200
    token_a = save_a.json()["access_token"]

    for idx in range(2):
        resp = await client.post(
            "/api/parlays/custom/save",
            headers={"Authorization": f"Bearer {token_a}"},
            json={
                "title": f"A-custom-{idx}",
                "legs": [{"game_id": "00000000-0000-0000-0000-000000000001", "pick": "home", "market_type": "spreads", "point": -3.5}],
            },
        )
        assert resp.status_code == 200

    lb = await client.get("/api/leaderboards/ai-usage?period=all_time&limit=10")
    assert lb.status_code == 200, lb.text
    data = lb.json()
    assert data["timeframe"] == "all_time"
    assert len(data["leaderboard"]) >= 2

    top = data["leaderboard"][0]
    assert top["username"] == "GrinderGorilla"
    assert top["ai_parlays_generated"] == 10

    # User A has 7 parlays + 2 custom saves
    second = data["leaderboard"][1]
    assert second["username"] == "UsageApe"
    assert second["ai_parlays_generated"] == 9


