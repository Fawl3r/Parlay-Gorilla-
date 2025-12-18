from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.models.game import Game
from app.models.game_analysis import GameAnalysis


def _core_ready_content() -> dict:
    return {
        "opening_summary": "Solid matchup preview.",
        "ats_trends": {
            "analysis": "ATS trends look normal.",
            "home_team_trend": "Home 1-0 ATS (50%).",
            "away_team_trend": "Away 1-0 ATS (50%).",
        },
        "totals_trends": {
            "analysis": "Totals trends look normal.",
            "home_team_trend": "Over hit 1 times (50%).",
            "away_team_trend": "Under hit 1 times (50%).",
        },
        "ai_spread_pick": {"pick": "Home -2.5"},
        "ai_total_pick": {"pick": "Over 44.5"},
        "best_bets": [{"market": "spread", "pick": "Home -2.5"}],
        "model_win_probability": {"home_win_prob": 0.56, "away_win_prob": 0.44, "ai_confidence": 55},
        "generation": {"core_status": "ready", "full_article_status": "disabled", "updated_at": "now"},
    }


@pytest.mark.asyncio
async def test_analysis_refresh_true_is_noop_for_anonymous(db, client):
    now = datetime.now(tz=timezone.utc)
    game = Game(
        external_game_id="test:game:1",
        sport="NFL",
        home_team="Home Team",
        away_team="Away Team",
        start_time=now,
        status="scheduled",
    )
    db.add(game)
    await db.flush()

    analysis = GameAnalysis(
        game_id=game.id,
        slug="nfl/test-game",
        league="NFL",
        matchup="Away Team @ Home Team",
        analysis_content=_core_ready_content(),
        seo_metadata={"title": "Test"},
        version=1,
        expires_at=now,
    )
    db.add(analysis)
    await db.commit()

    # Anonymous caller attempts refresh; backend should ignore and return stable version
    res = await client.get("/api/analysis/nfl/test-game?refresh=true")
    assert res.status_code == 200
    payload = res.json()
    assert payload.get("version") == 1
    assert payload.get("analysis_content", {}).get("opening_summary") == "Solid matchup preview."



