"""Tests for API-Sports dataset telemetry: cache hit/miss, call_made, call_blocked_budget."""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.game import Game
from app.services.analysis_enrichment_service import BUDGET_RESERVE, build_enrichment_for_game
from app.services.apisports.telemetry_helpers import (
    inc_cache_hit,
    inc_cache_miss,
    inc_call_made,
    inc_call_blocked_budget,
)


def test_telemetry_increments_exist() -> None:
    """Telemetry helpers do not raise when called (smoke test)."""
    inc_cache_hit("standings")
    inc_cache_miss("team_stats")
    inc_call_made("form", "nba")
    inc_call_blocked_budget("standings", "nfl")


@pytest.mark.asyncio
async def test_first_call_miss_then_second_call_hit_no_call_made(db) -> None:
    """
    First request: cache miss for teams -> inc_cache_miss + inc_call_made, client.get_teams called.
    Second request: get_cached returns index -> no client.get_teams call (simulated hit).
    """
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

    mock_quota = MagicMock()
    mock_quota.remaining_async = AsyncMock(return_value=BUDGET_RESERVE + 10)
    index = {"boston celtics": {"id": 1, "name": "Boston Celtics"}, "los angeles lakers": {"id": 2, "name": "Los Angeles Lakers"}}
    standings_return = {"response": [{"league": {"standings": [[{"team": {"id": 1, "name": "Boston Celtics"}, "all": {"win": 1, "lose": 0}}, {"team": {"id": 2, "name": "Los Angeles Lakers"}, "all": {"win": 0, "lose": 1}}]]}}]}
    # First build: get_cached("teams") called from enrichment then from get_teams_index -> need two None then index for next time
    teams_returns: List[Optional[Dict[str, Any]]] = [None, None, index]

    async def get_cached_side_effect(dataset: str, *args: object, **kwargs: object) -> object:
        if dataset == "teams":
            return teams_returns.pop(0) if teams_returns else index
        if dataset == "standings":
            return standings_return
        return None

    call_made_calls = []
    cache_miss_calls = []
    async_cached = AsyncMock(side_effect=get_cached_side_effect)
    async_set_cached = AsyncMock()

    with patch("app.services.analysis_enrichment_service.get_cached", async_cached):
        with patch("app.services.analysis_enrichment_service.set_cached", async_set_cached):
            with patch("app.services.apisports.teams_index_service.get_cached", async_cached):
                with patch("app.services.apisports.teams_index_service.set_cached", async_set_cached):
                    with patch("app.services.analysis_enrichment_service.get_apisports_client") as p_client:
                        mock_client = MagicMock()
                        mock_client.get_teams = AsyncMock(return_value={"response": [{"team": {"id": 1, "name": "Boston Celtics"}}, {"team": {"id": 2, "name": "Los Angeles Lakers"}}]})
                        mock_client.get_standings = AsyncMock(return_value=standings_return)
                        mock_client.get_team_stats = AsyncMock(return_value=None)
                        mock_client.get_games = AsyncMock(return_value={})
                        mock_client.get_injuries = AsyncMock(return_value=None)
                        p_client.return_value = mock_client
                        with patch("app.services.analysis_enrichment_service.get_quota_manager", return_value=mock_quota):
                            with patch("app.services.analysis_enrichment_service.is_enrichment_supported_for_sport", return_value=True):
                                with patch("app.services.analysis_enrichment_service.get_league_id_for_sport", return_value=12):
                                    with patch("app.services.analysis_enrichment_service.get_sport_config") as p_cfg:
                                        p_cfg.return_value = MagicMock(odds_key="basketball_nba", display_name="NBA")
                                    with patch("app.services.analysis_enrichment_service.get_season_for_sport_at_date", return_value="2024-2025"):
                                        with patch("app.services.analysis_enrichment_service.get_season_int_for_sport_at_date", return_value=2024):
                                            with patch("app.services.analysis_enrichment_service.get_capability") as p_cap:
                                                from app.services.apisports.capabilities import SportEnrichmentCapability
                                                p_cap.return_value = SportEnrichmentCapability(team_stats=True)
                                            with patch("app.services.apisports.telemetry_helpers.inc_call_made", side_effect=lambda d, s="": call_made_calls.append((d, s))):
                                                with patch("app.services.apisports.telemetry_helpers.inc_cache_miss", side_effect=lambda d: cache_miss_calls.append(d)):
                                                    payload1, _ = await build_enrichment_for_game(db, game, "nba")
                                                    payload2, _ = await build_enrichment_for_game(db, game, "nba")

    assert payload1 is not None
    assert payload2 is not None
    assert "teams_index" in cache_miss_calls
    assert any(c[0] == "teams_index" for c in call_made_calls)
    mock_client.get_teams.assert_called_once()
