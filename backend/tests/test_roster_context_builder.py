"""
Tests for RosterContextBuilder: allowed player names from cached rosters.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.game import Game
from app.services.analysis.roster_context_builder import (
    RosterContextBuilder,
    _extract_names_from_payload,
)


class TestExtractNamesFromPayload:
    """_extract_names_from_payload payload shapes."""

    def test_players_list_with_name(self) -> None:
        payload = {"players": [{"name": "Patrick Mahomes"}, {"name": "Travis Kelce"}]}
        out = _extract_names_from_payload(payload)
        assert "Patrick Mahomes" in out
        assert "Travis Kelce" in out

    def test_players_list_first_last(self) -> None:
        payload = {"players": [{"firstname": "Patrick", "lastname": "Mahomes"}]}
        out = _extract_names_from_payload(payload)
        assert "Patrick Mahomes" in out

    def test_response_list(self) -> None:
        payload = {"response": [{"name": "Geno Smith"}]}
        out = _extract_names_from_payload(payload)
        assert "Geno Smith" in out

    def test_empty_or_invalid(self) -> None:
        assert _extract_names_from_payload({}) == set()
        assert _extract_names_from_payload({"players": "not a list"}) == set()


@pytest.mark.asyncio
class TestRosterContextBuilderGetAllowedPlayerNames:
    """RosterContextBuilder.get_allowed_player_names with mocked repo and mapper."""

    async def test_empty_when_no_sport(self) -> None:
        db = AsyncMock()
        builder = RosterContextBuilder(db)
        game = MagicMock(spec=Game)
        game.sport = ""
        game.home_team = "Seahawks"
        game.away_team = "Raiders"
        game.start_time = datetime(2025, 1, 15, tzinfo=timezone.utc)
        out = await builder.get_allowed_player_names(game)
        assert out == []

    async def test_empty_when_team_mapper_returns_none(self) -> None:
        db = AsyncMock()
        builder = RosterContextBuilder(db)
        builder._team_mapper.get_team_id = MagicMock(return_value=None)
        game = MagicMock(spec=Game)
        game.sport = "nfl"
        game.home_team = "Seahawks"
        game.away_team = "Raiders"
        game.start_time = datetime(2025, 1, 15, tzinfo=timezone.utc)
        out = await builder.get_allowed_player_names(game)
        assert out == []

    async def test_returns_names_from_rosters(self) -> None:
        db = AsyncMock()
        roster_repo = AsyncMock()
        roster_row = MagicMock()
        roster_row.payload_json = {"players": [{"name": "Patrick Mahomes"}, {"name": "Travis Kelce"}]}
        roster_repo.get_rosters_for_team_ids = AsyncMock(return_value=[roster_row])
        builder = RosterContextBuilder(db)
        builder._roster_repo = roster_repo
        builder._team_mapper.get_team_id = MagicMock(side_effect=[1, 2])
        game = MagicMock(spec=Game)
        game.sport = "nfl"
        game.home_team = "Chiefs"
        game.away_team = "Bills"
        game.start_time = datetime(2025, 1, 15, tzinfo=timezone.utc)
        out = await builder.get_allowed_player_names(game)
        assert "Patrick Mahomes" in out
        assert "Travis Kelce" in out
        roster_repo.get_rosters_for_team_ids.assert_called_once()
        call_args = roster_repo.get_rosters_for_team_ids.call_args
        assert call_args[0][0] == "nfl"
        assert set(call_args[0][1]) == {1, 2}
        assert call_args[0][2] == "2024"
