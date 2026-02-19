"""Unit tests: enrichment data_quality.source_timestamps populated from cache/fetch."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.game import Game
from app.services.analysis_enrichment_service import build_enrichment_for_game


def _teams_index_cached():
    return (
        {
            "boston celtics": {"id": 1, "name": "Boston Celtics"},
            "los angeles lakers": {"id": 2, "name": "Los Angeles Lakers"},
        },
        "2025-01-15T12:00:00+00:00",
    )


def _standings_cached():
    return ([], "2025-01-15T12:01:00+00:00")  # empty entries ok


@pytest.mark.asyncio
async def test_source_timestamps_when_cached_data_exists(db):
    """When cached data exists, source_timestamps contains that dataset key with cached_at."""
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

    async def mock_get_cached_with_timestamp(dataset, sport, league_id, season, extra=""):
        if dataset == "teams":
            return _teams_index_cached()
        if dataset == "standings":
            return _standings_cached()
        return (None, None)

    mock_quota = MagicMock()
    mock_quota.remaining_async = AsyncMock(return_value=50)
    mock_config = MagicMock()
    mock_config.odds_key = "basketball_nba"
    mock_config.display_name = "NBA"
    mock_cap = MagicMock()
    mock_cap.team_stats = False
    mock_cap.standings = True
    mock_cap.form = False
    mock_cap.injuries = False

    cache_patch = patch(
        "app.services.analysis_enrichment_service.get_cached_with_timestamp",
        new_callable=AsyncMock,
        side_effect=mock_get_cached_with_timestamp,
    )
    set_cached_patch = patch("app.services.analysis_enrichment_service.set_cached", new_callable=AsyncMock)
    quota_patch = patch(
        "app.services.analysis_enrichment_service.get_quota_manager",
        return_value=mock_quota,
    )
    support_patch = patch(
        "app.services.analysis_enrichment_service.is_enrichment_supported_for_sport",
        return_value=True,
    )
    league_patch = patch(
        "app.services.analysis_enrichment_service.get_league_id_for_sport",
        return_value=12,
    )
    sport_config_patch = patch(
        "app.services.analysis_enrichment_service.get_sport_config",
        return_value=mock_config,
    )
    season_patch = patch(
        "app.services.analysis_enrichment_service.get_season_for_sport_at_date",
        return_value="2024-2025",
    )
    season_int_patch = patch(
        "app.services.analysis_enrichment_service.get_season_int_for_sport_at_date",
        return_value=2024,
    )
    capability_patch = patch(
        "app.services.analysis_enrichment_service.get_capability",
        return_value=mock_cap,
    )
    client = MagicMock()
    client.is_configured = MagicMock(return_value=True)
    client.get_games = AsyncMock(return_value={})
    client.get_standings = AsyncMock(return_value=None)
    client.get_injuries = AsyncMock(return_value=None)
    client_patch = patch(
        "app.services.analysis_enrichment_service.get_apisports_client",
        return_value=client,
    )

    with cache_patch:
        with set_cached_patch:
            with quota_patch:
                with support_patch:
                    with league_patch:
                        with sport_config_patch:
                            with season_patch:
                                with season_int_patch:
                                    with capability_patch:
                                        with client_patch:
                                            payload, reason = await build_enrichment_for_game(
                                                db, game, "nba", timeout_seconds=10.0
                                            )

    assert reason is None
    assert payload is not None
    dq = payload.get("data_quality") or {}
    ts = dq.get("source_timestamps") or {}
    assert "teams_index" in ts
    assert ts["teams_index"] == "2025-01-15T12:00:00+00:00"
    assert "standings" in ts
    assert ts["standings"] == "2025-01-15T12:01:00+00:00"
    assert "form" not in ts
    assert "injuries" not in ts


@pytest.mark.asyncio
async def test_source_timestamps_when_dataset_skipped_capability_false(db):
    """When a dataset is skipped (capability false), source_timestamps does not include it."""
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

    async def mock_get_cached_with_timestamp(dataset, sport, league_id, season, extra=""):
        if dataset == "teams":
            return _teams_index_cached()
        if dataset == "standings":
            return _standings_cached()
        return (None, None)

    mock_quota = MagicMock()
    mock_quota.remaining_async = AsyncMock(return_value=50)
    mock_config = MagicMock()
    mock_config.odds_key = "basketball_nba"
    mock_config.display_name = "NBA"
    cap_no_form = MagicMock()
    cap_no_form.team_stats = True
    cap_no_form.standings = True
    cap_no_form.form = False
    cap_no_form.injuries = False

    cache_patch = patch(
        "app.services.analysis_enrichment_service.get_cached_with_timestamp",
        new_callable=AsyncMock,
        side_effect=mock_get_cached_with_timestamp,
    )
    set_cached_patch = patch("app.services.analysis_enrichment_service.set_cached", new_callable=AsyncMock)
    quota_patch = patch(
        "app.services.analysis_enrichment_service.get_quota_manager",
        return_value=mock_quota,
    )
    support_patch = patch(
        "app.services.analysis_enrichment_service.is_enrichment_supported_for_sport",
        return_value=True,
    )
    league_patch = patch(
        "app.services.analysis_enrichment_service.get_league_id_for_sport",
        return_value=12,
    )
    sport_config_patch = patch(
        "app.services.analysis_enrichment_service.get_sport_config",
        return_value=mock_config,
    )
    season_patch = patch(
        "app.services.analysis_enrichment_service.get_season_for_sport_at_date",
        return_value="2024-2025",
    )
    season_int_patch = patch(
        "app.services.analysis_enrichment_service.get_season_int_for_sport_at_date",
        return_value=2024,
    )
    capability_patch = patch(
        "app.services.analysis_enrichment_service.get_capability",
        return_value=cap_no_form,
    )
    client = MagicMock()
    client.is_configured = MagicMock(return_value=True)
    client.get_games = AsyncMock(return_value={})
    client.get_standings = AsyncMock(return_value=None)
    client.get_injuries = AsyncMock(return_value=None)
    client_patch = patch(
        "app.services.analysis_enrichment_service.get_apisports_client",
        return_value=client,
    )

    with cache_patch:
        with set_cached_patch:
            with quota_patch:
                with support_patch:
                    with league_patch:
                        with sport_config_patch:
                            with season_patch:
                                with season_int_patch:
                                    with capability_patch:
                                        with client_patch:
                                            payload, _ = await build_enrichment_for_game(
                                                db, game, "nba", timeout_seconds=10.0
                                            )

    ts = (payload or {}).get("data_quality") or {}
    ts = ts.get("source_timestamps") or {}
    assert "form" not in ts
    assert "injuries" not in ts


@pytest.mark.asyncio
async def test_source_timestamps_provider_fetch_is_now_ish(db):
    """When provider fetch occurs (cache miss), timestamp is set to now-ish (patched)."""
    fixed_now = "2025-02-18T14:30:00+00:00"

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

    call_count = {"teams": 0}

    async def mock_get_cached_with_timestamp(dataset, sport, league_id, season, extra=""):
        if dataset == "teams":
            call_count["teams"] += 1
            if call_count["teams"] == 1:
                return (None, None)
            return _teams_index_cached()
        if dataset == "standings":
            return _standings_cached()
        return (None, None)

    mock_quota = MagicMock()
    mock_quota.remaining_async = AsyncMock(return_value=50)
    mock_config = MagicMock()
    mock_config.odds_key = "basketball_nba"
    mock_config.display_name = "NBA"
    mock_cap = MagicMock()
    mock_cap.team_stats = False
    mock_cap.standings = True
    mock_cap.form = False
    mock_cap.injuries = False

    cache_patch = patch(
        "app.services.analysis_enrichment_service.get_cached_with_timestamp",
        new_callable=AsyncMock,
        side_effect=mock_get_cached_with_timestamp,
    )
    set_cached_patch = patch("app.services.analysis_enrichment_service.set_cached", new_callable=AsyncMock)
    quota_patch = patch(
        "app.services.analysis_enrichment_service.get_quota_manager",
        return_value=mock_quota,
    )
    support_patch = patch(
        "app.services.analysis_enrichment_service.is_enrichment_supported_for_sport",
        return_value=True,
    )
    league_patch = patch(
        "app.services.analysis_enrichment_service.get_league_id_for_sport",
        return_value=12,
    )
    sport_config_patch = patch(
        "app.services.analysis_enrichment_service.get_sport_config",
        return_value=mock_config,
    )
    season_patch = patch(
        "app.services.analysis_enrichment_service.get_season_for_sport_at_date",
        return_value="2024-2025",
    )
    season_int_patch = patch(
        "app.services.analysis_enrichment_service.get_season_int_for_sport_at_date",
        return_value=2024,
    )
    capability_patch = patch(
        "app.services.analysis_enrichment_service.get_capability",
        return_value=mock_cap,
    )
    client = MagicMock()
    client.is_configured = MagicMock(return_value=True)
    client.get_teams = AsyncMock(
        return_value={
            "response": [
                {"team": {"id": 1, "name": "Boston Celtics"}, "name": "Boston Celtics"},
                {"team": {"id": 2, "name": "Los Angeles Lakers"}, "name": "Los Angeles Lakers"},
            ]
        }
    )
    client.get_games = AsyncMock(return_value={})
    client.get_standings = AsyncMock(return_value=None)
    client.get_injuries = AsyncMock(return_value=None)
    client_patch = patch(
        "app.services.analysis_enrichment_service.get_apisports_client",
        return_value=client,
    )
    datetime_patch = patch(
        "app.services.analysis_enrichment_service.datetime",
        wraps=datetime,
    )

    with datetime_patch as mock_dt:
        mock_dt.now.return_value = datetime(2025, 2, 18, 14, 30, 0, tzinfo=timezone.utc)
        with cache_patch:
            with set_cached_patch:
                with quota_patch:
                        with support_patch:
                            with league_patch:
                                with sport_config_patch:
                                    with season_patch:
                                        with season_int_patch:
                                            with capability_patch:
                                                with client_patch:
                                                    payload, reason = await build_enrichment_for_game(
                                                        db, game, "nba", timeout_seconds=10.0
                                                    )

    assert reason is None
    assert payload is not None
    ts = (payload.get("data_quality") or {}).get("source_timestamps") or {}
    assert "teams_index" in ts
    assert ts["teams_index"] == fixed_now
