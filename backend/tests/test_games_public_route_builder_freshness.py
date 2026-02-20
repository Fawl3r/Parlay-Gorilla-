from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.schemas.game import GameResponse


def _game_response(*, game_id: str, external_id: str, sport: str, start_time: datetime) -> GameResponse:
    return GameResponse(
        id=game_id,
        external_game_id=external_id,
        sport=sport,
        home_team="Home",
        away_team="Away",
        start_time=start_time,
        status="scheduled",
        markets=[],
    )


@pytest.mark.asyncio
async def test_games_route_refresh_busts_local_cache_and_excludes_finished_for_builder(client, monkeypatch):
    """
    Regression guard for Gorilla Builder:
    - refresh=true should bypass only local in-memory list cache
    - route should request non-finished games (include_finished=False)
    """
    import app.api.routes.games_public_routes as routes

    now = datetime.now(timezone.utc)
    captured: dict[str, object] = {}

    async def _fake_get_sport_state(db, sport_code, now):
        _ = db, sport_code
        return {
            "sport_state": "IN_SEASON",
            "next_game_at": (now + timedelta(hours=2)).isoformat(),
            "days_to_next": 0,
            "preseason_enable_days": 14,
        }

    class _FakeFetcher:
        def __init__(self, db):
            _ = db

        async def get_or_fetch_games(
            self,
            sport_identifier: str,
            force_refresh: bool = False,
            include_premium_markets: bool = False,
            include_finished: bool = False,
            bypass_in_memory_cache: bool = False,
        ):
            captured["sport_identifier"] = sport_identifier
            captured["force_refresh"] = force_refresh
            captured["include_premium_markets"] = include_premium_markets
            captured["include_finished"] = include_finished
            captured["bypass_in_memory_cache"] = bypass_in_memory_cache
            return [
                _game_response(
                    game_id="1",
                    external_id="odds:nba:1",
                    sport="NBA",
                    start_time=now + timedelta(hours=1),
                )
            ]

    monkeypatch.setattr(routes, "get_sport_state", _fake_get_sport_state)
    monkeypatch.setattr(routes, "OddsFetcherService", _FakeFetcher)
    monkeypatch.setattr(routes.games_response_cache, "set", lambda *args, **kwargs: None)

    response = await client.get("/api/sports/nba/games?refresh=true")
    assert response.status_code == 200
    assert response.json()["games"]

    assert captured["sport_identifier"] == "nba"
    assert captured["force_refresh"] is False
    assert captured["include_finished"] is False
    assert captured["bypass_in_memory_cache"] is True


@pytest.mark.asyncio
async def test_games_route_filters_out_stale_games_older_than_sport_past_window(client, monkeypatch):
    """
    NBA has a short past listing window (hours, not days). Ensure stale prior-day games
    are excluded from /api/sports/{sport}/games responses.
    """
    import app.api.routes.games_public_routes as routes

    now = datetime.now(timezone.utc)
    stale_started = now - timedelta(hours=18)  # outside NBA past_hours (6h)
    upcoming = now + timedelta(hours=3)

    async def _fake_get_sport_state(db, sport_code, now):
        _ = db, sport_code
        return {
            "sport_state": "IN_SEASON",
            "next_game_at": (now + timedelta(hours=3)).isoformat(),
            "days_to_next": 0,
            "preseason_enable_days": 14,
        }

    class _FakeFetcher:
        def __init__(self, db):
            _ = db

        async def get_or_fetch_games(
            self,
            sport_identifier: str,
            force_refresh: bool = False,
            include_premium_markets: bool = False,
            include_finished: bool = False,
            bypass_in_memory_cache: bool = False,
        ):
            _ = sport_identifier, force_refresh, include_premium_markets, include_finished, bypass_in_memory_cache
            return [
                _game_response(
                    game_id="stale",
                    external_id="odds:nba:stale",
                    sport="NBA",
                    start_time=stale_started,
                ),
                _game_response(
                    game_id="upcoming",
                    external_id="odds:nba:upcoming",
                    sport="NBA",
                    start_time=upcoming,
                ),
            ]

    monkeypatch.setattr(routes, "get_sport_state", _fake_get_sport_state)
    monkeypatch.setattr(routes, "OddsFetcherService", _FakeFetcher)
    monkeypatch.setattr(routes.games_response_cache, "set", lambda *args, **kwargs: None)

    response = await client.get("/api/sports/nba/games?refresh=true")
    assert response.status_code == 200
    data = response.json()
    ids = [g["id"] for g in data["games"]]
    assert "stale" not in ids
    assert "upcoming" in ids

