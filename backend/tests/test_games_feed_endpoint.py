"""Integration tests for /api/games/feed window filters and unit tests for feed response builder."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.api.routes.games import build_feed_response
from app.models.game import Game


@pytest.mark.asyncio
async def test_games_feed_window_live_returns_only_live(client, db):
    now = datetime.now(timezone.utc)
    live_game = Game(
        id=uuid.uuid4(),
        external_game_id="test-feed-live-1",
        sport="NFL",
        home_team="Seahawks",
        away_team="Raiders",
        start_time=now,
        status="LIVE",
        home_score=21,
        away_score=17,
    )
    final_game = Game(
        id=uuid.uuid4(),
        external_game_id="test-feed-final-1",
        sport="NFL",
        home_team="Chiefs",
        away_team="Bills",
        start_time=now - timedelta(hours=2),
        status="FINAL",
        home_score=27,
        away_score=24,
    )
    db.add(live_game)
    db.add(final_game)
    await db.commit()

    resp = await client.get("/api/games/feed", params={"window": "live"})
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["status"] == "LIVE"
    assert data[0]["home_team"] == "Seahawks"
    assert data[0]["away_team"] == "Raiders"


@pytest.mark.asyncio
async def test_games_feed_window_upcoming_returns_only_future(client, db):
    now = datetime.now(timezone.utc)
    upcoming_game = Game(
        id=uuid.uuid4(),
        external_game_id="test-feed-upcoming-1",
        sport="NFL",
        home_team="Cowboys",
        away_team="Eagles",
        start_time=now + timedelta(days=2),
        status="scheduled",
    )
    db.add(upcoming_game)
    await db.commit()

    resp = await client.get("/api/games/feed", params={"window": "upcoming"})
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["home_team"] == "Cowboys"
    assert data[0]["away_team"] == "Eagles"


@pytest.mark.asyncio
async def test_games_feed_window_today_includes_final_and_live(client, db):
    now = datetime.now(timezone.utc)
    live_game = Game(
        id=uuid.uuid4(),
        external_game_id="test-feed-today-live",
        sport="NFL",
        home_team="Seahawks",
        away_team="Raiders",
        start_time=now,
        status="LIVE",
        home_score=14,
        away_score=10,
    )
    final_game = Game(
        id=uuid.uuid4(),
        external_game_id="test-feed-today-final",
        sport="NFL",
        home_team="Chiefs",
        away_team="Bills",
        start_time=now - timedelta(hours=3),
        status="FINAL",
        home_score=27,
        away_score=24,
    )
    upcoming_far = Game(
        id=uuid.uuid4(),
        external_game_id="test-feed-today-far",
        sport="NFL",
        home_team="Cowboys",
        away_team="Eagles",
        start_time=now + timedelta(days=3),
        status="scheduled",
    )
    db.add(live_game)
    db.add(final_game)
    db.add(upcoming_far)
    await db.commit()

    resp = await client.get("/api/games/feed", params={"window": "today"})
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    ids = {g["id"] for g in data}
    assert str(live_game.id) in ids
    assert str(final_game.id) in ids
    assert str(upcoming_far.id) not in ids

    statuses = {g["status"] for g in data}
    assert "LIVE" in statuses
    assert "FINAL" in statuses


def test_build_feed_response_skips_null_start_time():
    """Feed response builder skips games with NULL start_time (avoids 500s)."""
    now = datetime.now(timezone.utc)
    valid_game = Game(
        id=uuid.uuid4(),
        external_game_id="valid-1",
        sport="NFL",
        home_team="Seahawks",
        away_team="Raiders",
        start_time=now,
        status="LIVE",
        home_score=21,
        away_score=17,
    )
    # In-memory instance with start_time=None (e.g. bad row from DB)
    invalid_game = Game(
        id=uuid.uuid4(),
        external_game_id="invalid-1",
        sport="NFL",
        home_team="Chiefs",
        away_team="Bills",
        start_time=None,
        status="LIVE",
        home_score=0,
        away_score=0,
    )
    result = build_feed_response([valid_game, invalid_game])
    assert len(result) == 1
    assert result[0].id == str(valid_game.id)
    assert result[0].home_team == "Seahawks"
    assert result[0].start_time == now.isoformat()


@pytest.mark.asyncio
async def test_games_feed_never_returns_null_start_time(client, db):
    """Contract: feed endpoint never returns a game with null/missing start_time."""
    now = datetime.now(timezone.utc)
    game = Game(
        id=uuid.uuid4(),
        external_game_id="test-feed-contract-1",
        sport="NFL",
        home_team="Seahawks",
        away_team="Raiders",
        start_time=now,
        status="scheduled",
    )
    db.add(game)
    await db.commit()

    for window in ("live", "today", "upcoming", "all"):
        resp = await client.get("/api/games/feed", params={"window": window})
        assert resp.status_code == 200, f"window={window}"
        data = resp.json()
        assert isinstance(data, list)
        for item in data:
            assert "start_time" in item, f"window={window} item missing start_time"
            assert item["start_time"] is not None and item["start_time"] != "", f"window={window} null/empty start_time"
