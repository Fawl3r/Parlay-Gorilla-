"""Tests for SeasonStateService (unified with get_sport_state)."""

from __future__ import annotations

from datetime import timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import SeasonState
from app.models.game import Game
from app.services.season_state_service import SeasonStateService
from app.services.sport_state_service import get_sport_state
from tests.ugie_fixtures import fixed_test_now


@pytest.fixture
def now():
    return fixed_test_now()


@pytest.mark.asyncio
async def test_season_state_unified_offseason_when_no_games(db: AsyncSession, now):
    """SeasonStateService returns OFF_SEASON when get_sport_state would be OFFSEASON (no games)."""
    svc = SeasonStateService(db)
    state = await svc.get_season_state("NBA", now_utc=now, use_cache=False)
    assert state == SeasonState.OFF_SEASON

    result = await get_sport_state(db, "NBA", now=now)
    assert result["sport_state"] == "OFFSEASON"


@pytest.mark.asyncio
async def test_season_state_unified_in_season_when_game_in_window(db: AsyncSession, now):
    """SeasonStateService returns IN_SEASON when get_sport_state has game in in-season window."""
    future = now + timedelta(days=3)
    game = Game(
        external_game_id="test-season-svc-1",
        sport="NBA",
        home_team="LAL",
        away_team="BOS",
        start_time=future,
        status="scheduled",
    )
    db.add(game)
    await db.commit()

    svc = SeasonStateService(db)
    state = await svc.get_season_state("NBA", now_utc=now, use_cache=False)
    assert state == SeasonState.IN_SEASON

    result = await get_sport_state(db, "NBA", now=now)
    assert result["sport_state"] == "IN_SEASON"


@pytest.mark.asyncio
async def test_season_state_in_break_maps_to_off_season(db: AsyncSession, now):
    """IN_BREAK from get_sport_state maps to OFF_SEASON for candidate window lookahead."""
    # Recent game but next game > in_season_window and <= break_max_next -> IN_BREAK
    past = now - timedelta(days=5)
    future = now + timedelta(days=25)
    for g, eid, t in [
        (past, "recent", "final"),
        (future, "next-far", "scheduled"),
    ]:
        db.add(
            Game(
                external_game_id=eid,
                sport="NBA",
                home_team="A",
                away_team="B",
                start_time=g,
                status=t,
            )
        )
    await db.commit()

    result = await get_sport_state(db, "NBA", now=now)
    assert result["sport_state"] == "IN_BREAK"

    svc = SeasonStateService(db)
    state = await svc.get_season_state("NBA", now_utc=now, use_cache=False)
    assert state == SeasonState.OFF_SEASON
