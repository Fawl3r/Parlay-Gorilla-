"""Tests for sport state inference (windowed + sanity, per-sport policy, POSTSEASON)."""

from __future__ import annotations

from datetime import timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.game import Game
from app.services.sport_state_policy import SportStatePolicy, get_policy_for_sport
from app.services.sport_state_service import SportState, get_sport_state
from tests.ugie_fixtures import fixed_test_now

# Explicit thresholds for tests (match cadence defaults)
IN_SEASON_DAYS = 10
PRESEASON_DAYS = 60
RECENT_DAYS = 10
MAX_FUTURE_SANITY = 330
MAX_PAST_SANITY = 365
BREAK_MAX_NEXT_DAYS = 60


@pytest.fixture
def now():
    return fixed_test_now()


def _cadence_policy() -> SportStatePolicy:
    return SportStatePolicy(
        mode="cadence",
        in_season_window_days=IN_SEASON_DAYS,
        preseason_window_days=PRESEASON_DAYS,
        recent_window_days=RECENT_DAYS,
        preseason_enable_days=14,
        max_future_sanity_days=MAX_FUTURE_SANITY,
        max_past_sanity_days=MAX_PAST_SANITY,
        break_max_next_days=BREAK_MAX_NEXT_DAYS,
        listing_in_season_days=10,
        listing_preseason_days=60,
    )


@pytest.mark.asyncio
async def test_sport_state_offseason_when_no_games(db: AsyncSession, now):
    """When there are no games in DB for sport, state is OFFSEASON. NBA has fallback return date."""
    result = await get_sport_state(db, "NBA", now=now, policy=_cadence_policy())
    assert result["sport_state"] == SportState.OFFSEASON.value
    assert result["is_enabled"] is False
    # NBA has configured offseason fallback so UI can show "Returns <date>"
    assert result["next_game_at"] is not None
    assert "2026" in result["next_game_at"]
    assert result["days_to_next"] is not None


@pytest.mark.asyncio
async def test_sport_state_in_season_when_upcoming_soon(db: AsyncSession, now):
    """When there are games within in-season window (e.g. 3 days), state is IN_SEASON."""
    future = now + timedelta(days=3)
    game = Game(
        external_game_id="test-upcoming-1",
        sport="NBA",
        home_team="LAL",
        away_team="BOS",
        start_time=future,
        status="scheduled",
    )
    db.add(game)
    await db.commit()

    result = await get_sport_state(db, "NBA", now=now, policy=_cadence_policy())
    assert result["sport_state"] == SportState.IN_SEASON.value
    assert result["is_enabled"] is True
    assert result["upcoming_soon_count"] >= 1
    assert result["next_game_at"] is not None


@pytest.mark.asyncio
async def test_sport_state_postseason_when_postseason_game_in_window(db: AsyncSession, now):
    """Postseason game in 3 days with season_phase=postseason -> state POSTSEASON, is_enabled True."""
    future = now + timedelta(days=3)
    game = Game(
        external_game_id="test-postseason-1",
        sport="NFL",
        home_team="KC",
        away_team="BUF",
        start_time=future,
        status="scheduled",
        season_phase="postseason",
        stage="Playoffs",
    )
    db.add(game)
    await db.commit()

    result = await get_sport_state(db, "NFL", now=now, policy=_cadence_policy())
    assert result["sport_state"] == SportState.POSTSEASON.value
    assert result["is_enabled"] is True
    assert result["state_reason"] == "postseason_games_upcoming"
    assert result.get("season_phase_hint") == "postseason"


@pytest.mark.asyncio
async def test_sport_state_regular_game_in_window_stays_in_season(db: AsyncSession, now):
    """Regular game in 3 days with season_phase=regular -> state IN_SEASON (not POSTSEASON)."""
    future = now + timedelta(days=3)
    game = Game(
        external_game_id="test-regular-1",
        sport="NFL",
        home_team="KC",
        away_team="BUF",
        start_time=future,
        status="scheduled",
        season_phase="regular",
    )
    db.add(game)
    await db.commit()

    result = await get_sport_state(db, "NFL", now=now, policy=_cadence_policy())
    assert result["sport_state"] == SportState.IN_SEASON.value
    assert result["is_enabled"] is True


@pytest.mark.asyncio
async def test_sport_state_preseason_next_game_30_days_away(db: AsyncSession, now):
    """Next game 30 days away (within preseason window, no games soon) -> PRESEASON."""
    future = now + timedelta(days=30)
    game = Game(
        external_game_id="test-preseason-1",
        sport="NFL",
        home_team="KC",
        away_team="BUF",
        start_time=future,
        status="scheduled",
    )
    db.add(game)
    await db.commit()

    result = await get_sport_state(db, "NFL", now=now, policy=_cadence_policy())
    assert result["sport_state"] == SportState.PRESEASON.value
    assert result["is_enabled"] is False  # 30 > preseason_enable_days (14)
    assert result["state_reason"] == "preseason_not_yet_enabled"
    assert result["next_game_at"] is not None
    assert result.get("days_to_next") == 30
    assert result.get("preseason_enable_days") == 14


@pytest.mark.asyncio
async def test_sport_state_preseason_enabled_when_days_to_next_le_14(db: AsyncSession, now):
    """When next game is 12 days away (outside in-season window, within preseason), PRESEASON and is_enabled True."""
    future = now + timedelta(days=12)  # > in_season_days (10), <= preseason_enable_days (14)
    game = Game(
        external_game_id="test-preseason-enable-1",
        sport="NFL",
        home_team="KC",
        away_team="BUF",
        start_time=future,
        status="scheduled",
    )
    db.add(game)
    await db.commit()

    result = await get_sport_state(db, "NFL", now=now, policy=_cadence_policy())
    assert result["sport_state"] == SportState.PRESEASON.value
    assert result["is_enabled"] is True
    assert result["state_reason"] == "preseason_approaching_enabled"
    assert result.get("days_to_next") == 12


@pytest.mark.asyncio
async def test_sport_state_offseason_next_game_180_days_away(db: AsyncSession, now):
    """Next game 180 days away (beyond preseason window) -> OFFSEASON."""
    future = now + timedelta(days=180)
    game = Game(
        external_game_id="test-offseason-1",
        sport="NFL",
        home_team="KC",
        away_team="BUF",
        start_time=future,
        status="scheduled",
    )
    db.add(game)
    await db.commit()

    result = await get_sport_state(db, "NFL", now=now, policy=_cadence_policy())
    assert result["sport_state"] == SportState.OFFSEASON.value
    assert result["is_enabled"] is False
    assert result["next_game_at"] is not None  # still within sanity window


@pytest.mark.asyncio
async def test_sport_state_in_break_recent_and_next_14_days(db: AsyncSession, now):
    """Recent game within 10 days + next game 14 days away -> IN_BREAK."""
    past = now - timedelta(days=3)
    future = now + timedelta(days=14)
    db.add(
        Game(
            external_game_id="test-break-past",
            sport="NBA",
            home_team="LAL",
            away_team="BOS",
            start_time=past,
            status="final",
        )
    )
    db.add(
        Game(
            external_game_id="test-break-future",
            sport="NBA",
            home_team="MIA",
            away_team="BOS",
            start_time=future,
            status="scheduled",
        )
    )
    await db.commit()

    result = await get_sport_state(db, "NBA", now=now, policy=_cadence_policy())
    assert result["sport_state"] == SportState.IN_BREAK.value
    assert result["is_enabled"] is False
    assert result["state_reason"] == "recent_games_but_no_upcoming_soon"
    assert result["recent_count"] >= 1
    assert result["upcoming_soon_count"] == 0


@pytest.mark.asyncio
async def test_sport_state_break_vs_offseason_boundary_next_45_days(db: AsyncSession, now):
    """Recent game + next game 45 days -> IN_BREAK (within break_max_next_days 60)."""
    past = now - timedelta(days=5)
    future = now + timedelta(days=45)
    db.add(
        Game(
            external_game_id="test-break-45-past",
            sport="NBA",
            home_team="LAL",
            away_team="BOS",
            start_time=past,
            status="final",
        )
    )
    db.add(
        Game(
            external_game_id="test-break-45-future",
            sport="NBA",
            home_team="MIA",
            away_team="BOS",
            start_time=future,
            status="scheduled",
        )
    )
    await db.commit()

    result = await get_sport_state(db, "NBA", now=now, policy=_cadence_policy())
    assert result["sport_state"] == SportState.IN_BREAK.value
    assert result["is_enabled"] is False


@pytest.mark.asyncio
async def test_sport_state_break_vs_offseason_boundary_next_120_days(db: AsyncSession, now):
    """Recent game + next game 120 days -> OFFSEASON (beyond break_max_next_days and preseason)."""
    past = now - timedelta(days=5)
    future = now + timedelta(days=120)
    db.add(
        Game(
            external_game_id="test-off-120-past",
            sport="NBA",
            home_team="LAL",
            away_team="BOS",
            start_time=past,
            status="final",
        )
    )
    db.add(
        Game(
            external_game_id="test-off-120-future",
            sport="NBA",
            home_team="MIA",
            away_team="BOS",
            start_time=future,
            status="scheduled",
        )
    )
    await db.commit()

    result = await get_sport_state(db, "NBA", now=now, policy=_cadence_policy())
    assert result["sport_state"] == SportState.OFFSEASON.value
    assert result["is_enabled"] is False


@pytest.mark.asyncio
async def test_sport_state_sanity_only_game_400_days_away_offseason(db: AsyncSession, now):
    """Only game 400 days away is ignored (beyond MAX_FUTURE_SANITY_DAYS) -> OFFSEASON."""
    future = now + timedelta(days=400)
    game = Game(
        external_game_id="test-sanity-far",
        sport="NCAAF",
        home_team="ALA",
        away_team="OSU",
        start_time=future,
        status="scheduled",
    )
    db.add(game)
    await db.commit()

    result = await get_sport_state(db, "NCAAF", now=now, policy=_cadence_policy())
    assert result["sport_state"] == SportState.OFFSEASON.value
    assert result["is_enabled"] is False
    # Autonomous: extended lookahead (500d) finds game at 400d -> DB-derived return date
    assert result["next_game_at"] is not None
    assert result["state_reason"] in ("no_games_soon", "no_games_in_db", "offseason_return_from_db_extended")


@pytest.mark.asyncio
async def test_sport_state_offseason_ufc_no_fallback_return_date(db: AsyncSession, now):
    """Offseason sport with no fallback config (e.g. UFC) keeps next_game_at None."""
    policy = get_policy_for_sport("UFC")
    result = await get_sport_state(db, "UFC", now=now, policy=policy)
    assert result["sport_state"] == SportState.OFFSEASON.value
    assert result["is_enabled"] is False
    assert result["next_game_at"] is None


@pytest.mark.asyncio
async def test_sport_state_event_based_policy_next_25_days_in_season(db: AsyncSession, now):
    """Event-based sport with next event 25 days -> IN_SEASON (within event_based in_season_window 30)."""
    future = now + timedelta(days=25)
    game = Game(
        external_game_id="test-ufc-25",
        sport="UFC",
        home_team="Fighter A",
        away_team="Fighter B",
        start_time=future,
        status="scheduled",
    )
    db.add(game)
    await db.commit()

    policy = get_policy_for_sport("UFC")
    assert policy.mode == "event_based"
    result = await get_sport_state(db, "UFC", now=now, policy=policy)
    # 25 days within in_season_window_days=30 -> IN_SEASON
    assert result["sport_state"] == SportState.IN_SEASON.value
    assert result.get("policy_mode") == "event_based"


@pytest.mark.asyncio
async def test_sport_state_event_based_policy_next_40_days_preseason(db: AsyncSession, now):
    """Event-based sport with next event 40 days -> PRESEASON (outside 30-day window, within 90)."""
    future = now + timedelta(days=40)
    game = Game(
        external_game_id="test-ufc-40",
        sport="UFC",
        home_team="Fighter A",
        away_team="Fighter B",
        start_time=future,
        status="scheduled",
    )
    db.add(game)
    await db.commit()

    policy = get_policy_for_sport("UFC")
    result = await get_sport_state(db, "UFC", now=now, policy=policy)
    assert result["sport_state"] == SportState.PRESEASON.value
    assert result.get("policy_mode") == "event_based"


@pytest.mark.asyncio
async def test_sport_state_offseason_extended_lookahead_uses_db_return_date(db: AsyncSession, now):
    """When only game is beyond normal sanity window (e.g. 400d), extended lookahead uses DB for return date."""
    future = now + timedelta(days=400)
    game = Game(
        external_game_id="test-extended-return",
        sport="NBA",
        home_team="LAL",
        away_team="BOS",
        start_time=future,
        status="scheduled",
    )
    db.add(game)
    await db.commit()

    result = await get_sport_state(db, "NBA", now=now, policy=_cadence_policy())
    assert result["sport_state"] == SportState.OFFSEASON.value
    assert result["next_game_at"] is not None
    assert result["state_reason"] == "offseason_return_from_db_extended"


@pytest.mark.asyncio
async def test_sport_state_offseason_static_fallback_logs_watchdog(db: AsyncSession, now, caplog):
    """When no games in DB at all, static fallback is used and WARNING is logged for watchdog."""
    # No games for NBA in DB
    with caplog.at_level("WARNING"):
        result = await get_sport_state(db, "NBA", now=now, policy=_cadence_policy())
    assert result["sport_state"] == SportState.OFFSEASON.value
    assert result["next_game_at"] is not None
    assert any("offseason_return_using_static_fallback" in rec.message for rec in caplog.records)
    assert any("sport=NBA" in rec.message for rec in caplog.records)


@pytest.mark.asyncio
async def test_sport_state_return_payload_keys(db: AsyncSession, now):
    """Return payload includes required keys for API and debugging."""
    result = await get_sport_state(db, "NBA", now=now, policy=_cadence_policy())
    assert "sport_state" in result
    assert "is_enabled" in result
    assert "next_game_at" in result
    assert "last_game_at" in result
    assert "state_reason" in result
    assert "upcoming_soon_count" in result
    assert "recent_count" in result
    assert "preseason_window_days" in result
    assert "days_to_next" in result
    assert "preseason_enable_days" in result
    assert "policy_mode" in result
    assert "in_season_window_days" in result
