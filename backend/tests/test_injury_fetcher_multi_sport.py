import pytest
from unittest.mock import AsyncMock

from app.services.data_fetchers.injuries import InjuryFetcher
from app.services.espn.espn_injuries_client import EspnInjuriesClient
from app.services.espn.espn_team_resolver import EspnTeamResolver, ResolvedTeamRef


@pytest.mark.asyncio
async def test_injury_fetcher_resolves_non_nfl_sport(monkeypatch):
    resolved_sports = []

    async def fake_resolve(self, sport: str, team_name: str):
        resolved_sports.append(sport)
        return ResolvedTeamRef(
            team_id="1",
            injuries_url="https://example.com/injuries",
            team_url=None,
            matched_name=team_name,
            match_method="exact",
            confidence=1.0,
        )

    async def fake_fetch(self, sport: str, team_ref: ResolvedTeamRef):
        return {
            "key_players_out": [
                {"name": "Star Guard", "position": "PG", "status": "Out", "description": "ankle"},
            ]
        }

    monkeypatch.setattr(EspnTeamResolver, "resolve_team_ref", fake_resolve)
    monkeypatch.setattr(EspnInjuriesClient, "fetch_injuries_for_team_ref", fake_fetch)

    fetcher = InjuryFetcher("nba")
    injuries = await fetcher.get_team_injuries("Boston Celtics")
    key_status = await fetcher.get_key_player_status("Boston Celtics")

    assert resolved_sports and resolved_sports[0] == "nba"
    assert injuries and injuries[0]["player"] == "Star Guard"
    assert key_status["Star Guard"]["impact"] == "high"


@pytest.mark.asyncio
async def test_injury_fetcher_falls_back_to_legacy_for_nfl(monkeypatch):
    async def fake_resolve(self, sport: str, team_name: str):
        return None

    monkeypatch.setattr(EspnTeamResolver, "resolve_team_ref", fake_resolve)

    fetcher = InjuryFetcher("nfl")
    legacy = AsyncMock(return_value=[{"player": "Legacy QB", "position": "QB", "status": "Out", "injury": "knee"}])
    monkeypatch.setattr(fetcher, "_get_nfl_legacy_injuries", legacy)

    injuries = await fetcher.get_team_injuries("Kansas City Chiefs")

    assert injuries and injuries[0]["player"] == "Legacy QB"
    legacy.assert_awaited_once()


@pytest.mark.asyncio
async def test_injury_fetcher_resolves_wnba_sport_code(monkeypatch):
    resolved_sports = []

    async def fake_resolve(self, sport: str, team_name: str):
        resolved_sports.append(sport)
        return ResolvedTeamRef(
            team_id="10",
            injuries_url="https://example.com/injuries",
            team_url=None,
            matched_name=team_name,
            match_method="exact",
            confidence=1.0,
        )

    async def fake_fetch(self, sport: str, team_ref: ResolvedTeamRef):
        return {"key_players_out": []}

    monkeypatch.setattr(EspnTeamResolver, "resolve_team_ref", fake_resolve)
    monkeypatch.setattr(EspnInjuriesClient, "fetch_injuries_for_team_ref", fake_fetch)

    fetcher = InjuryFetcher("basketball_wnba")
    await fetcher.get_team_injuries("Las Vegas Aces")

    assert resolved_sports and resolved_sports[0] == "wnba"
