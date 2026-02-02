"""
Unit tests for UGIE hydration: key_players and availability on detail page.
"""

from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.game import Game
from app.models.game_analysis import GameAnalysis
from app.services.analysis.ugie_v2.ugie_hydration_service import (
    hydrate_key_players_and_availability,
    _needs_hydration,
    _game_within_window,
)


class TestNeedsHydration:
    def test_true_when_key_players_unavailable_roster_missing(self) -> None:
        content = {
            "ugie_v2": {
                "key_players": {"status": "unavailable", "reason": "roster_missing_or_empty"},
            }
        }
        assert _needs_hydration(content) is True

    def test_true_when_availability_contains_unable_to_assess(self) -> None:
        content = {
            "ugie_v2": {
                "pillars": {
                    "availability": {"why_summary": "Unable to assess injury impact without current data."},
                },
            }
        }
        assert _needs_hydration(content) is True

    def test_false_when_no_ugie(self) -> None:
        assert _needs_hydration({}) is False
        assert _needs_hydration({"ugie_v2": None}) is False

    def test_false_when_healthy_ugie(self) -> None:
        content = {
            "ugie_v2": {
                "key_players": {"status": "ready"},
                "pillars": {"availability": {"why_summary": "No major injuries."}},
            }
        }
        assert _needs_hydration(content) is False


class TestGameWithinWindow:
    def test_true_when_game_in_three_days(self) -> None:
        start = datetime.now(timezone.utc) + timedelta(days=3)
        game = MagicMock(spec=Game)
        game.start_time = start
        assert _game_within_window(game) is True

    def test_false_when_game_in_past(self) -> None:
        start = datetime.now(timezone.utc) - timedelta(days=1)
        game = MagicMock(spec=Game)
        game.start_time = start
        assert _game_within_window(game) is False

    def test_false_when_game_more_than_seven_days_out(self) -> None:
        start = datetime.now(timezone.utc) + timedelta(days=10)
        game = MagicMock(spec=Game)
        game.start_time = start
        assert _game_within_window(game) is False


@pytest.mark.asyncio
class TestHydrateKeyPlayersAndAvailability:
    async def test_returns_none_when_no_game_row(self) -> None:
        db = AsyncMock()
        analysis = MagicMock(spec=GameAnalysis)
        analysis.analysis_content = {"ugie_v2": {"key_players": {"status": "unavailable", "reason": "roster_missing_or_empty"}}}
        out = await hydrate_key_players_and_availability(db, analysis, None)
        assert out is None

    async def test_returns_none_when_game_far_in_future(self) -> None:
        db = AsyncMock()
        analysis = MagicMock(spec=GameAnalysis)
        analysis.analysis_content = {"ugie_v2": {"key_players": {"status": "unavailable", "reason": "roster_missing_or_empty"}}}
        game = MagicMock(spec=Game)
        game.start_time = datetime.now(timezone.utc) + timedelta(days=14)
        out = await hydrate_key_players_and_availability(db, analysis, game)
        assert out is None

    async def test_returns_none_when_does_not_need_hydration(self) -> None:
        db = AsyncMock()
        analysis = MagicMock(spec=GameAnalysis)
        analysis.analysis_content = {"ugie_v2": {"key_players": {"status": "ready"}, "pillars": {"availability": {"why_summary": "OK"}}}}
        game = MagicMock(spec=Game)
        game.start_time = datetime.now(timezone.utc) + timedelta(days=2)
        game.home_team = "Chiefs"
        game.away_team = "Bills"
        game.sport = "NFL"
        out = await hydrate_key_players_and_availability(db, analysis, game)
        assert out is None
