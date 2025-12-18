import uuid
from datetime import datetime, timezone, timedelta

import pytest

from app.models.game import Game
from app.models.game_analysis import GameAnalysis
from app.services.analysis.analysis_orchestrator import _generate_slug


@pytest.mark.asyncio
async def test_refresh_regenerates_placeholder_analysis(client, db):
    """
    If a placeholder analysis was previously stored (e.g. generation timeout),
    `refresh=true` should regenerate full content (or a structured fallback),
    so the UI does not show blank ATS/O-U sections.
    """
    unique = uuid.uuid4().hex[:8]
    game = Game(
        external_game_id=f"test-{uuid.uuid4()}",
        sport="NFL",
        home_team=f"Test Home {unique}",
        away_team=f"Test Away {unique}",
        start_time=datetime(2025, 12, 19, 1, 15, 0, tzinfo=timezone.utc),
        status="scheduled",
    )
    db.add(game)
    await db.commit()
    await db.refresh(game)

    full_slug = _generate_slug(
        home_team=game.home_team,
        away_team=game.away_team,
        league=game.sport,
        game_time=game.start_time,
    )
    slug_param = full_slug.split("/", 1)[1]
    placeholder = {
        "opening_summary": f"Analysis is being prepared for {game.away_team} @ {game.home_team}. Please refresh in a moment.",
        "best_bets": [],
        "same_game_parlays": {},
        "full_article": "",
    }
    analysis = GameAnalysis(
        game_id=game.id,
        slug=full_slug,
        league="NFL",
        matchup=f"{game.away_team} @ {game.home_team}",
        analysis_content=placeholder,
        seo_metadata={"title": "Placeholder"},
        expires_at=game.start_time + timedelta(hours=2),
        version=1,
    )
    db.add(analysis)
    await db.commit()

    res = await client.get(f"/api/analysis/nfl/{slug_param}?refresh=true")
    assert res.status_code == 200
    payload = res.json()
    content = payload.get("analysis_content") or {}

    # Should no longer be the placeholder string.
    assert "analysis is being prepared" not in str(content.get("opening_summary") or "").lower()

    # Should have structured trend fields (may be fallback text in test env).
    assert isinstance(content.get("ats_trends"), dict)
    assert isinstance(content.get("totals_trends"), dict)
    assert str(content["ats_trends"].get("analysis") or "") != ""
    assert str(content["totals_trends"].get("analysis") or "") != ""


