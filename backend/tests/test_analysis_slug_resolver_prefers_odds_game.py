import uuid
from datetime import datetime, timezone, timedelta

import pytest

from app.models.game import Game
from app.services.analysis.analysis_orchestrator import _generate_slug
from app.services.analysis_slug_resolver import AnalysisSlugResolver


@pytest.mark.asyncio
async def test_slug_resolver_prefers_non_espn_game_when_duplicates_exist(db):
    """
    If multiple Game rows match the same analysis slug (e.g., Odds API + ESPN fallback),
    the resolver should prefer the non-ESPN row so analyses align with the odds-backed game.
    """

    start_time = datetime(2026, 1, 17, 21, 30, 0, tzinfo=timezone.utc)

    # ESPN fallback row (lower quality for betting content).
    espn_game = Game(
        external_game_id=f"espn:{uuid.uuid4()}",
        sport="NFL",
        home_team="Denver Broncos",
        away_team="Buffalo Bills",
        start_time=start_time,
        status="scheduled",
    )

    # Odds API row (preferred). Slightly later start_time to ensure deterministic ordering
    # by `start_time` so older resolver logic would pick ESPN first.
    odds_game = Game(
        external_game_id=f"odds:{uuid.uuid4()}",
        sport="NFL",
        home_team="Denver Broncos",
        away_team="Buffalo Bills",
        start_time=start_time + timedelta(minutes=1),
        status="scheduled",
    )

    db.add(espn_game)
    db.add(odds_game)
    await db.commit()
    await db.refresh(espn_game)
    await db.refresh(odds_game)

    full_slug = _generate_slug(
        home_team="Denver Broncos",
        away_team="Buffalo Bills",
        league="NFL",
        game_time=start_time,
    )
    slug_param = full_slug.split("/", 1)[1]

    resolver = AnalysisSlugResolver(db)
    resolved = await resolver.find_game(sport_identifier="nfl", slug=slug_param)

    assert resolved is not None
    assert str(resolved.id) == str(odds_game.id)
