"""Tests for ESPN team resolver and matching logic."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.espn.espn_team_resolver import (
    ResolvedTeamRef,
    _normalize_for_match,
    _token_overlap_score,
    EspnTeamResolver,
)
from app.services.espn.espn_sport_resolver import EspnSportResolver


def test_normalize_for_match():
    """Normalization strips punctuation and collapses spaces."""
    assert _normalize_for_match("  L.A. Lakers  ") == "l a lakers"
    assert _normalize_for_match("New England Patriots") == "new england patriots"
    assert _normalize_for_match("") == ""


def test_token_overlap_score():
    """Token overlap is symmetric and in 0..1."""
    assert _token_overlap_score("Boston Celtics", "Boston Celtics") >= 0.99
    assert _token_overlap_score("Boston", "Boston Celtics") > 0.3
    assert _token_overlap_score("x y z", "a b c") == 0.0
    assert _token_overlap_score("", "x") == 0.0


def test_resolved_team_ref_roundtrip():
    """ResolvedTeamRef serializes and deserializes."""
    ref = ResolvedTeamRef(
        team_id="1",
        injuries_url="https://example.com/teams/1/injuries",
        team_url="https://example.com/teams/1",
        matched_name="Lakers",
        match_method="exact",
        confidence=1.0,
    )
    data = ref.to_dict()
    back = ResolvedTeamRef.from_dict(data)
    assert back.team_id == ref.team_id
    assert back.matched_name == ref.matched_name
    assert back.confidence == ref.confidence


def test_espn_sport_resolver_base_urls():
    """Sport resolver returns correct base URLs for major sports."""
    assert "nfl" in EspnSportResolver.get_base_url("nfl")
    assert "basketball/nba" in EspnSportResolver.get_base_url("nba")
    assert "hockey/nhl" in EspnSportResolver.get_base_url("nhl")
    assert "baseball/mlb" in EspnSportResolver.get_base_url("mlb")
    assert "soccer/eng.1" in EspnSportResolver.get_base_url("epl")
    assert "soccer/usa.1" in EspnSportResolver.get_base_url("mls")


def test_team_resolver_build_candidates_from_teams_key():
    """_build_candidates extracts teams from response.teams[].team."""
    resolver = EspnTeamResolver()
    data = {
        "teams": [
            {"team": {"id": "1", "displayName": "Lakers", "links": []}},
        ]
    }
    cands = resolver._build_candidates(data)
    assert len(cands) == 1
    assert cands[0]["displayName"] == "Lakers"
    assert cands[0]["id"] == "1"


def test_team_resolver_build_candidates_from_sports_leagues():
    """_build_candidates extracts from sports[0].leagues[0].teams[].team."""
    resolver = EspnTeamResolver()
    data = {
        "sports": [
            {
                "leagues": [
                    {
                        "teams": [
                            {"team": {"id": "2", "displayName": "Celtics"}},
                        ]
                    }
                ]
            }
        ]
    }
    cands = resolver._build_candidates(data)
    assert len(cands) == 1
    assert cands[0]["displayName"] == "Celtics"


def test_team_resolver_score_match_exact():
    """Exact match on displayName gets confidence 1.0."""
    resolver = EspnTeamResolver()
    candidate = {"displayName": "Boston Celtics", "shortDisplayName": "Celtics", "id": "2", "links": []}
    score, method = resolver._score_match("Boston Celtics", candidate)
    assert score == 1.0
    assert method == "exact"


def test_team_resolver_score_match_normalized():
    """Match on shortDisplayName gets high confidence."""
    resolver = EspnTeamResolver()
    candidate = {"displayName": "Boston Celtics", "shortDisplayName": "Celtics", "id": "2", "links": []}
    score, method = resolver._score_match("Celtics", candidate)
    assert score >= 0.85
    assert method in ("normalized", "contains")


def test_team_resolver_ref_from_candidate_builds_injuries_url():
    """_ref_from_candidate builds injuries URL when no link present."""
    resolver = EspnTeamResolver()
    candidate = {"id": "5", "displayName": "Bruins", "links": []}
    base = "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl"
    ref = resolver._ref_from_candidate(candidate, base, 0.9, "exact")
    assert ref.team_id == "5"
    assert ref.injuries_url == f"{base}/teams/5/injuries"
    assert ref.matched_name == "Bruins"


@pytest.mark.asyncio
async def test_resolve_team_ref_uses_espn_resolver_when_teams_returned():
    """resolve_team_ref returns ref when API returns teams and one matches."""
    resolver = EspnTeamResolver()
    mock_response = {
        "teams": [
            {"team": {"id": "10", "displayName": "Seattle Seahawks", "links": []}},
        ]
    }
    with patch("app.services.espn.espn_team_resolver.httpx.AsyncClient") as mock_client:
        mock_get = AsyncMock()
        mock_get.return_value.status_code = 200
        mock_get.return_value.json = MagicMock(return_value=mock_response)
        mock_client.return_value.__aenter__.return_value.get = mock_get
        ref = await resolver.resolve_team_ref("nfl", "Seattle Seahawks")
    assert ref is not None
    assert ref.team_id == "10"
    assert ref.matched_name == "Seattle Seahawks"
    assert ref.confidence >= 0.5


@pytest.mark.asyncio
async def test_resolve_team_ref_returns_none_on_http_error():
    """resolve_team_ref returns None when API returns non-200."""
    resolver = EspnTeamResolver()
    with patch("app.services.espn.espn_team_resolver.httpx.AsyncClient") as mock_client:
        mock_get = AsyncMock()
        mock_get.return_value.status_code = 404
        mock_client.return_value.__aenter__.return_value.get = mock_get
        ref = await resolver.resolve_team_ref("nfl", "Unknown Team")
    assert ref is None


@pytest.mark.asyncio
async def test_resolve_team_ref_returns_none_on_empty_teams():
    """resolve_team_ref returns None when API returns empty teams list."""
    resolver = EspnTeamResolver()
    with patch("app.services.espn.espn_team_resolver.httpx.AsyncClient") as mock_client:
        mock_get = AsyncMock()
        mock_get.return_value.status_code = 200
        mock_get.return_value.json = MagicMock(return_value={"teams": []})
        mock_client.return_value.__aenter__.return_value.get = mock_get
        ref = await resolver.resolve_team_ref("nhl", "Vegas Golden Knights")
    assert ref is None
