import uuid
from datetime import datetime, timezone

import pytest

from app.models.game import Game
from app.models.game_analysis import GameAnalysis


@pytest.mark.asyncio
async def test_analysis_detail_resolves_nfl_week_slug_when_game_exists(client, db):
    """
    Regression: analysis detail must not 404 for canonical NFL week slugs when the
    underlying game exists, even if the stored analysis slug is legacy/mismatched.
    """
    game = Game(
        external_game_id=f"test-{uuid.uuid4()}",
        sport="NFL",
        home_team="Seattle Seahawks",
        away_team="Los Angeles Rams",
        start_time=datetime(2025, 12, 21, 20, 0, 0, tzinfo=timezone.utc),  # Week 16 (2025 season)
        status="scheduled",
    )
    db.add(game)
    await db.commit()
    await db.refresh(game)

    legacy_analysis = GameAnalysis(
        game_id=game.id,
        slug="nfl/legacy-slug-does-not-match-request",
        league="NFL",
        matchup="Los Angeles Rams @ Seattle Seahawks",
        analysis_content={
            "opening_summary": "Legacy analysis content for test.",
            "best_bets": [],
            "same_game_parlays": {},
            "full_article": "",
        },
        seo_metadata={"title": "Legacy"},
        expires_at=game.start_time,
    )
    db.add(legacy_analysis)
    await db.commit()

    res = await client.get("/api/analysis/nfl/los-angeles-rams-vs-seattle-seahawks-week-16-2025")
    assert res.status_code == 200
    payload = res.json()
    assert payload.get("game_id") == str(game.id)


