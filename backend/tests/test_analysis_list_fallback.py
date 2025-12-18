from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.api.routes.analysis import _generate_slug
from app.api.routes.analysis_list_routes import _analysis_list_cache, _fetch_analyses_list
from app.services.analysis_slug_resolver import AnalysisSlugResolver


@pytest.mark.asyncio
async def test_analysis_upcoming_returns_games_when_no_analyses_exist():
    """
    The analysis list endpoint should not be "empty" just because pre-generated
    GameAnalysis rows don't exist yet. It must still surface upcoming games with
    computed slugs.
    """
    _analysis_list_cache.clear()

    now = datetime.utcnow()
    game = MagicMock()
    game.id = uuid.uuid4()
    game.sport = "NFL"
    game.home_team = "Home Team"
    game.away_team = "Away Team"
    game.start_time = now + timedelta(hours=3)

    expected_slug = _generate_slug(
        home_team=game.home_team,
        away_team=game.away_team,
        league=game.sport,
        game_time=game.start_time,
    )

    fake_result = MagicMock()
    fake_result.all.return_value = [(game, None)]

    db = AsyncMock()
    db.execute = AsyncMock(return_value=fake_result)

    items = await _fetch_analyses_list("nfl", 1, db, "nfl:1")
    assert len(items) == 1
    assert items[0].id == str(game.id)
    assert items[0].slug == expected_slug
    assert items[0].league == "NFL"
    assert items[0].matchup == "Away Team @ Home Team"


@pytest.mark.asyncio
async def test_slug_resolver_finds_game_for_canonical_slug(db):
    """
    The slug resolver should locate a game when given the canonical slug
    (week-based for NFL, date-based for others).
    """
    from app.models.game import Game

    now = datetime.utcnow()
    game = Game(
        external_game_id=f"test-{uuid.uuid4()}",
        sport="NFL",
        home_team="Green Bay Packers",
        away_team="Chicago Bears",
        start_time=now + timedelta(hours=6),
        status="scheduled",
    )
    db.add(game)
    await db.commit()
    await db.refresh(game)

    expected_full_slug = _generate_slug(
        home_team=game.home_team,
        away_team=game.away_team,
        league=game.sport,
        game_time=game.start_time,
    )
    slug_part = expected_full_slug.split("/", 1)[1]

    resolved = await AnalysisSlugResolver(db).find_game(sport_identifier="nfl", slug=slug_part)
    assert resolved is not None
    assert resolved.id == game.id


