"""Budget guard: when remaining < BUDGET_RESERVE, no API-Sports calls occur."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.game import Game
from app.services.analysis_enrichment_service import (
    BUDGET_RESERVE,
    NOTE_BUDGET_LOW,
    build_enrichment_for_game,
)


@pytest.mark.asyncio
async def test_budget_guard_blocks_all_apisports_calls(db):
    """When remaining < BUDGET_RESERVE, return (None, reason) and never call API-Sports client."""
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
    mock_quota.remaining_async = AsyncMock(return_value=BUDGET_RESERVE - 1)

    get_client_patch = patch(
        "app.services.analysis_enrichment_service.get_apisports_client",
        return_value=MagicMock(),
    )
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
    mock_config = MagicMock()
    mock_config.odds_key = "basketball_nba"
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
    get_capability_patch = patch(
        "app.services.analysis_enrichment_service.get_capability",
        return_value={},
    )

    with get_client_patch as p_get_client:
        with quota_patch:
            with support_patch:
                with league_patch:
                    with sport_config_patch:
                        with season_patch:
                            with season_int_patch:
                                with get_capability_patch:
                                    payload, reason = await build_enrichment_for_game(db, game, "nba")

    assert payload is None
    assert reason == NOTE_BUDGET_LOW
    p_get_client.assert_not_called()
