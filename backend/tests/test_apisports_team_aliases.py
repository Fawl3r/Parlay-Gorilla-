"""Tests for team alias resolution and mapping-failure diagnostic notes."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.game import Game
from app.services.analysis_enrichment_service import BUDGET_RESERVE, build_enrichment_for_game
from app.services.apisports.team_aliases import TEAM_ALIASES, get_team_alias
from app.services.apisports.teams_index_service import normalize_team_name, resolve_team_id


def test_get_team_alias_returns_alias_when_present() -> None:
    assert get_team_alias("la lakers") == "los angeles lakers"
    assert get_team_alias("ny knicks") == "new york knicks"
    assert get_team_alias("la clippers") == "los angeles clippers"


def test_get_team_alias_returns_input_when_no_alias() -> None:
    assert get_team_alias("boston celtics") == "boston celtics"
    assert get_team_alias("") == ""


def test_resolve_team_id_uses_alias_before_index_lookup() -> None:
    # Index has "los angeles lakers" -> id 1; odds name "LA Lakers" normalizes to "la lakers"
    index = {normalize_team_name("Los Angeles Lakers"): {"id": 1, "name": "Los Angeles Lakers"}}
    # resolve_team_id should map "la lakers" via alias to "los angeles lakers" and find id 1
    tid = resolve_team_id(index, "LA Lakers")
    assert tid == 1


def test_resolve_team_id_alias_mapping_ny_knicks() -> None:
    index = {normalize_team_name("New York Knicks"): {"id": 2, "name": "New York Knicks"}}
    assert resolve_team_id(index, "NY Knicks") == 2


def test_resolve_team_id_returns_none_when_not_found() -> None:
    index = {"other team": {"id": 99, "name": "Other Team"}}
    assert resolve_team_id(index, "Unknown Team XYZ") is None


def test_team_aliases_contains_common_variants() -> None:
    assert "la lakers" in TEAM_ALIASES
    assert "ny yankees" in TEAM_ALIASES
    assert TEAM_ALIASES["la lakers"] == "los angeles lakers"


@pytest.mark.asyncio
async def test_mapping_failure_emits_diagnostic_note(db) -> None:
    """When team ID resolution fails, data_quality.notes includes the odds-team name that failed."""
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
    mock_quota.remaining_async = AsyncMock(return_value=BUDGET_RESERVE + 5)
    mock_client = MagicMock()
    mock_client.get_games = AsyncMock(return_value={})
    mock_client.get_injuries = AsyncMock(return_value=None)

    async def get_cached_side_effect(dataset: str, *args: object, **kwargs: object) -> object:
        if dataset == "teams":
            return {}  # empty index -> resolve_team_id returns None for both
        if dataset == "standings":
            return {"response": [{"league": {"standings": [[{"team": {"id": 1, "name": "Celtics"}, "all": {"win": 1, "lose": 0}}]]}}]}
        return None

    async_cached = AsyncMock(side_effect=get_cached_side_effect)
    async_set_cached = AsyncMock()
    with patch("app.services.analysis_enrichment_service.get_cached", async_cached):
        with patch("app.services.analysis_enrichment_service.set_cached", async_set_cached):
            with patch("app.services.apisports.teams_index_service.get_cached", async_cached):
                with patch("app.services.apisports.teams_index_service.set_cached", async_set_cached):
                    with patch("app.services.analysis_enrichment_service.get_apisports_client", return_value=mock_client):
                        with patch("app.services.analysis_enrichment_service.get_quota_manager", return_value=mock_quota):
                            with patch("app.services.analysis_enrichment_service.is_enrichment_supported_for_sport", return_value=True):
                                with patch("app.services.analysis_enrichment_service.get_league_id_for_sport", return_value=12):
                                    with patch("app.services.analysis_enrichment_service.get_sport_config") as p_config:
                                        p_config.return_value = MagicMock(odds_key="basketball_nba", display_name="NBA")
                                        with patch("app.services.analysis_enrichment_service.get_season_for_sport_at_date", return_value="2024-2025"):
                                            with patch("app.services.analysis_enrichment_service.get_season_int_for_sport_at_date", return_value=2024):
                                                with patch("app.services.analysis_enrichment_service.get_capability") as p_cap:
                                                    from app.services.apisports.capabilities import SportEnrichmentCapability
                                                    p_cap.return_value = SportEnrichmentCapability(team_stats=True)
                                                payload, reason = await build_enrichment_for_game(db, game, "nba")

    assert payload is not None
    assert reason is None
    notes = payload.get("data_quality", {}).get("notes") or []
    assert any("Team ID not found" in n and "Boston Celtics" in n for n in notes)
    assert any("Team ID not found" in n and "Los Angeles Lakers" in n for n in notes)
