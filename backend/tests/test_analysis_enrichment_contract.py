"""Contract tests: analysis detail response includes enrichment (nullable) and reason when missing."""

import uuid
from datetime import datetime, timezone

import pytest

from app.models.game import Game
from app.models.game_analysis import GameAnalysis


@pytest.mark.asyncio
async def test_analysis_detail_includes_enrichment_field(client, db):
    """Analysis detail response must include 'enrichment' (nullable) and optionally 'enrichment_unavailable_reason'."""
    game = Game(
        id=uuid.uuid4(),
        external_game_id=f"test-{uuid.uuid4()}",
        sport="NBA",
        home_team="Boston Celtics",
        away_team="Los Angeles Lakers",
        start_time=datetime(2025, 3, 1, 19, 0, 0, tzinfo=timezone.utc),
        status="scheduled",
    )
    db.add(game)
    await db.commit()
    await db.refresh(game)

    analysis = GameAnalysis(
        game_id=game.id,
        slug="nba/boston-celtics-vs-los-angeles-lakers",
        league="NBA",
        matchup="Los Angeles Lakers @ Boston Celtics",
        analysis_content={
            "opening_summary": "Test.",
            "best_bets": [],
            "same_game_parlays": {},
            "full_article": "",
        },
        seo_metadata={},
        expires_at=game.start_time,
    )
    db.add(analysis)
    await db.commit()

    res = await client.get("/api/analysis/nba/boston-celtics-vs-los-angeles-lakers")
    assert res.status_code == 200
    payload = res.json()
    assert "enrichment" in payload
    if payload.get("enrichment") is None:
        assert "enrichment_unavailable_reason" in payload
    else:
        e = payload["enrichment"]
        assert "sport" in e and "league" in e and "season" in e
        assert "home_team" in e and "away_team" in e
        assert "data_quality" in e
