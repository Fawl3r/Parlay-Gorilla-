import pytest
import uuid
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.parlay import Parlay
from app.models.saved_parlay import InscriptionStatus, SavedParlay
from app.models.saved_parlay_results import SavedParlayResult
from app.models.user import User


async def _register_and_setup_profile(client: AsyncClient, *, email: str, display_name: str) -> str:
    reg = await client.post("/api/auth/register", json={"email": email, "password": "Passw0rd!"})
    assert reg.status_code == 200, reg.text
    token = reg.json()["access_token"]

    setup = await client.post(
        "/api/profile/setup",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "display_name": display_name,
            "default_risk_profile": "balanced",
            "favorite_teams": [],
            "favorite_sports": [],
        },
    )
    assert setup.status_code == 200, setup.text
    return token


async def _get_user(db: AsyncSession, *, email: str) -> User:
    res = await db.execute(select(User).where(User.email == email).limit(1))
    return res.scalar_one()


@pytest.mark.asyncio
async def test_users_me_stats_returns_shape_and_counts(client: AsyncClient, db: AsyncSession):
    email = "stats@test.com"
    token = await _register_and_setup_profile(client, email=email, display_name="StatsGorilla")
    user = await _get_user(db, email=email)

    now = datetime.now(timezone.utc)

    # Insert 3 AI parlay generations (2 on the same day) to make `most_active_day` deterministic.
    day_a = now - timedelta(days=1)
    day_b = now - timedelta(days=2)
    for idx in range(3):
        created_at = day_a if idx < 2 else day_b
        db.add(
            Parlay(
                user_id=user.id,
                legs=[{"market_id": "m1", "outcome": "home"}],
                num_legs=1,
                parlay_hit_prob=0.5,
                risk_profile="balanced",
                created_at=created_at,
            )
        )
    await db.commit()

    # Save 2 custom parlays
    saved_ids: list[str] = []
    for idx in range(2):
        resp = await client.post(
            "/api/parlays/custom/save",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": f"Custom {idx}",
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
        assert resp.status_code == 200, resp.text
        saved_ids.append(resp.json()["id"])

    # Mark the first custom parlay as confirmed + quota consumed and a verified WIN result.
    res = await db.execute(select(SavedParlay).where(SavedParlay.id == uuid.UUID(saved_ids[0])).limit(1))
    saved = res.scalar_one()
    saved.inscription_status = InscriptionStatus.confirmed.value
    saved.inscription_tx = "tx-stats-1"
    saved.inscription_quota_consumed = True
    saved.inscription_credits_consumed = True  # Track credits spent
    db.add(saved)
    await db.commit()

    db.add(
        SavedParlayResult(
            saved_parlay_id=saved.id,
            user_id=user.id,
            parlay_type="custom",
            num_legs=1,
            hit=True,
            legs_hit=1,
            legs_missed=0,
            leg_results=[{"status": "hit"}],
            resolved_at=datetime.now(timezone.utc),
        )
    )
    await db.commit()

    stats = await client.get("/api/users/me/stats", headers={"Authorization": f"Bearer {token}"})
    assert stats.status_code == 200, stats.text
    data = stats.json()

    for key in ["ai_parlays", "usage_breakdown", "custom_ai_parlays", "inscriptions", "verified_wins", "leaderboards"]:
        assert key in data

    assert data["ai_parlays"]["lifetime"] == 3
    assert data["ai_parlays"]["last_30_days"] == 3

    assert data["custom_ai_parlays"]["saved_lifetime"] == 2

    assert data["verified_wins"]["lifetime"] == 1
    assert data["verified_wins"]["last_30_days"] == 1

    assert data["inscriptions"]["consumed_lifetime"] == 1
    assert data["inscriptions"]["inscription_cost_credits"] == 1
    assert data["inscriptions"]["credits_spent_lifetime"] == 1

    assert data["leaderboards"]["verified_winners"]["rank"] == 1
    assert data["leaderboards"]["ai_usage_30d"]["rank"] == 1
    assert data["leaderboards"]["ai_usage_all_time"]["rank"] == 1

    assert data["usage_breakdown"]["weekly_activity"]["ai_parlays_this_week"] == 3
    assert data["usage_breakdown"]["weekly_activity"]["most_active_day"] == day_a.strftime("%A")
    assert data["usage_breakdown"]["custom_ai_behavior"]["custom_ai_share_percent"] == 0
    assert data["usage_breakdown"]["custom_ai_behavior"]["verified_on_chain_this_period"] == 0


@pytest.mark.asyncio
async def test_users_me_stats_hidden_visibility_has_no_ranks(client: AsyncClient, db: AsyncSession):
    email = "stats-hidden@test.com"
    token = await _register_and_setup_profile(client, email=email, display_name="HiddenGorilla")

    # Opt out of leaderboards
    update = await client.put(
        "/api/profile/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"leaderboard_visibility": "hidden"},
    )
    assert update.status_code == 200, update.text
    assert update.json()["leaderboard_visibility"] == "hidden"

    user = await _get_user(db, email=email)
    db.add(
        Parlay(
            user_id=user.id,
            legs=[{"market_id": "m1", "outcome": "home"}],
            num_legs=1,
            parlay_hit_prob=0.5,
            risk_profile="balanced",
        )
    )
    await db.commit()

    stats = await client.get("/api/users/me/stats", headers={"Authorization": f"Bearer {token}"})
    assert stats.status_code == 200, stats.text
    data = stats.json()

    assert data["leaderboards"]["verified_winners"]["rank"] is None
    assert data["leaderboards"]["ai_usage_30d"]["rank"] is None
    assert data["leaderboards"]["ai_usage_all_time"]["rank"] is None


@pytest.mark.asyncio
async def test_users_me_stats_usage_breakdown_for_premium_counts_period_behavior(client: AsyncClient, db: AsyncSession):
    from sqlalchemy import select

    from app.core.config import settings
    from app.models.subscription import Subscription, SubscriptionStatus

    email = "stats-premium@test.com"
    reg = await client.post("/api/auth/register", json={"email": email, "password": "Passw0rd!"})
    assert reg.status_code == 200, reg.text
    token = reg.json()["access_token"]
    user_id = reg.json()["user"]["id"]
    user_uuid = uuid.UUID(user_id)

    # Make user premium by seeding an active subscription.
    now = datetime.now(timezone.utc)
    sub = Subscription(
        id=uuid.uuid4(),
        user_id=user_uuid,
        plan="PG_PREMIUM_MONTHLY",
        provider="lemonsqueezy",
        provider_subscription_id="ls_sub_test_stats",
        provider_customer_id="ls_cust_test_stats",
        status=SubscriptionStatus.active.value,
        current_period_start=now,
        current_period_end=now + timedelta(days=30),
        cancel_at_period_end=False,
        is_lifetime=False,
    )
    db.add(sub)

    # Seed rolling-period counters to make share/verification deterministic.
    user_row = (await db.execute(select(User).where(User.id == user_uuid))).scalar_one()
    user_row.premium_ai_parlays_period_start = now
    user_row.premium_ai_parlays_used = 42
    user_row.premium_custom_builder_period_start = now
    user_row.premium_custom_builder_used = 4
    user_row.premium_inscriptions_period_start = now
    user_row.premium_inscriptions_used = 2
    await db.commit()

    # Insert some AI parlay generations this week so weekly analytics are non-empty.
    day_a = now - timedelta(days=1)
    day_b = now - timedelta(days=2)
    for idx in range(3):
        created_at = day_a if idx < 2 else day_b
        db.add(
            Parlay(
                user_id=user_uuid,
                legs=[{"market_id": "m1", "outcome": "home"}],
                num_legs=1,
                parlay_hit_prob=0.5,
                risk_profile="balanced",
                created_at=created_at,
            )
        )
    await db.commit()

    stats = await client.get("/api/users/me/stats", headers={"Authorization": f"Bearer {token}"})
    assert stats.status_code == 200, stats.text
    data = stats.json()

    assert data["ai_parlays"]["period_used"] == 42
    assert data["ai_parlays"]["period_limit"] == int(settings.premium_ai_parlays_per_month)
    assert data["ai_parlays"]["period_remaining"] == int(settings.premium_ai_parlays_per_month) - 42

    assert data["custom_ai_parlays"]["period_used"] == 4
    assert data["custom_ai_parlays"]["period_limit"] == int(settings.premium_custom_builder_per_month)
    assert data["custom_ai_parlays"]["period_remaining"] == int(settings.premium_custom_builder_per_month) - 4

    assert data["usage_breakdown"]["weekly_activity"]["ai_parlays_this_week"] == 3
    assert data["usage_breakdown"]["weekly_activity"]["most_active_day"] == day_a.strftime("%A")

    # Share percent is computed over period AI + Custom usage.
    expected_share = int(round((4 / (42 + 4)) * 100))
    assert data["usage_breakdown"]["custom_ai_behavior"]["custom_ai_share_percent"] == expected_share
    assert data["usage_breakdown"]["custom_ai_behavior"]["verified_on_chain_this_period"] == 2


