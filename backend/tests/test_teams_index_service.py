"""Tests for API-Sports teams index: normalization, alias, cache."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.apisports.teams_index_service import (
    normalize_team_name,
    resolve_team_id,
    get_teams_index,
    TEAM_ALIAS_OVERRIDES,
)


def test_normalize_team_name():
    """Normalization: lowercase, strip punctuation, collapse spaces."""
    assert normalize_team_name("") == ""
    assert normalize_team_name("Lakers") == "lakers"
    assert normalize_team_name("  Boston  Celtics  ") == "boston celtics"
    assert normalize_team_name("L.A. Clippers") == "la clippers"
    assert normalize_team_name("San Antonio Spurs") == "san antonio spurs"


def test_resolve_team_id_exact_match():
    """Exact normalized key returns team id."""
    index = {"lakers": {"id": 1, "name": "Lakers"}, "celtics": {"id": 2, "name": "Celtics"}}
    assert resolve_team_id(index, "Lakers") == 1
    assert resolve_team_id(index, "Celtics") == 2


def test_resolve_team_id_substring_match():
    """Substring/containment fallback matches when normalized name is contained in index key or vice versa."""
    index = {"los angeles lakers": {"id": 1, "name": "Los Angeles Lakers"}}
    assert resolve_team_id(index, "Lakers") == 1  # "lakers" in "los angeles lakers"
    index2 = {"lakers": {"id": 1, "name": "Lakers"}}
    assert resolve_team_id(index2, "LA Lakers") == 1  # "lakers" in "la lakers"


def test_resolve_team_id_empty():
    """Empty name or index returns None."""
    assert resolve_team_id({}, "Lakers") is None
    assert resolve_team_id({"lakers": {"id": 1, "name": "Lakers"}}, "") is None


@pytest.mark.asyncio
async def test_get_teams_index_cache_hit():
    """When cache has index, API is not called."""
    mock_client = MagicMock()
    mock_client.get_teams = AsyncMock(return_value={"response": []})
    from app.services.apisports.teams_index_service import get_cached, set_cached
    from unittest.mock import patch

    cached_index = {"lakers": {"id": 100, "name": "Lakers"}}
    with patch("app.services.apisports.teams_index_service.get_cached", new_callable=AsyncMock, return_value=cached_index):
        with patch("app.services.apisports.teams_index_service.set_cached", new_callable=AsyncMock):
            result = await get_teams_index(mock_client, "basketball_nba", 12, "2024-2025")
            assert result == cached_index
            mock_client.get_teams.assert_not_called()
