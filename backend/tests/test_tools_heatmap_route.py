"""Contract tests for GET /api/tools/odds-heatmap-probabilities.
Ensures 200 always (no 500s), valid JSON list, empty list when no games.
"""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_heatmap_probabilities_returns_200_and_empty_list_when_no_games(client):
    """No games in DB must return 200 and [] (never 500)."""
    resp = await client.get("/api/tools/odds-heatmap-probabilities?sport=nfl")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert data == []


@pytest.mark.asyncio
async def test_heatmap_probabilities_invalid_sport_returns_400(client):
    """Unknown sport returns 400, not 500."""
    resp = await client.get("/api/tools/odds-heatmap-probabilities?sport=invalid_sport_xyz")
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_heatmap_probabilities_valid_schema_when_non_empty(client, db):
    """When games exist, response is a list of objects with required heatmap fields."""
    import uuid
    from app.models.game import Game
    from datetime import datetime, timedelta, timezone

    game_id = uuid.uuid4()
    game = Game(
        id=game_id,
        external_game_id=f"heatmap-test-{game_id}",
        sport="NFL",
        home_team="Team A",
        away_team="Team B",
        start_time=datetime.now(timezone.utc) + timedelta(days=1),
    )
    db.add(game)
    await db.commit()

    resp = await client.get("/api/tools/odds-heatmap-probabilities?sport=nfl")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    if data:
        item = data[0]
        assert "game_id" in item
        assert "home_win_prob" in item
        assert "away_win_prob" in item
        assert "has_cached_analysis" in item
        assert isinstance(item["home_win_prob"], (int, float))
        assert isinstance(item["away_win_prob"], (int, float))
        assert isinstance(item["has_cached_analysis"], bool)
