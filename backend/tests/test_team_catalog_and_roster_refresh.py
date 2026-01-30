"""
Tests for team catalog and roster refresh: skip when fresh, quota reserve.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.apisports.roster_refresh_service import RosterRefreshService
from app.services.apisports.team_catalog_refresh_service import TeamCatalogRefreshService


@pytest.mark.asyncio
class TestTeamCatalogRefreshService:
    """TeamCatalogRefreshService skips when fresh (TTL)."""

    async def test_skip_when_fresh(self) -> None:
        db = AsyncMock()
        repo = AsyncMock()
        row = MagicMock()
        row.last_fetched_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
        repo.get_teams_by_sport_league_season = AsyncMock(return_value=[row])
        repo.upsert_team = AsyncMock()
        with patch(
            "app.services.apisports.team_catalog_refresh_service.ApisportsTeamRepository.is_fresh",
            return_value=True,
        ):
            svc = TeamCatalogRefreshService(db)
            svc._repo = repo
            n = await svc.refresh_teams("nfl", 1, "2024")
        assert n == 0
        repo.upsert_team.assert_not_called()


@pytest.mark.asyncio
class TestRosterRefreshService:
    """RosterRefreshService respects quota reserve."""

    async def test_is_soccer_detection(self) -> None:
        db = AsyncMock()
        svc = RosterRefreshService(db)
        assert svc._is_soccer("football") is True
        assert svc._is_soccer("soccer") is True
        assert svc._is_soccer("nfl") is False
        assert svc._is_soccer("americanfootball_nfl") is False

    async def test_refresh_empty_team_ids_returns_zero(self) -> None:
        db = AsyncMock()
        svc = RosterRefreshService(db)
        n = await svc.refresh_rosters_for_team_ids("nfl", [], "2024")
        assert n == 0
