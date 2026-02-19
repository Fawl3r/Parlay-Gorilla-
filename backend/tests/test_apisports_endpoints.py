"""Unit tests for API-Sports endpoint resolver (single source of truth for team stats paths)."""

import pytest

from app.services.apisports.endpoints import get_team_stats_endpoint, TeamStatsEndpoint


@pytest.mark.parametrize(
    "sport_slug,expected_path,expected_sport_key",
    [
        ("nba", "/statistics", "nba"),
        ("NBA", "/statistics", "nba"),
        ("wnba", "/statistics", "wnba"),
        ("nfl", "/statistics", "nfl"),
        ("nhl", "/statistics", "nhl"),
        ("mlb", "/statistics", "mlb"),
        ("epl", "/teams/statistics", "football"),
        ("mls", "/teams/statistics", "football"),
        ("laliga", "/teams/statistics", "football"),
        ("ucl", "/teams/statistics", "football"),
    ],
)
def test_team_stats_endpoint_resolver_returns_correct_path(
    sport_slug: str, expected_path: str, expected_sport_key: str
) -> None:
    """Endpoint resolver returns correct path and sport_key for nba/wnba/nfl/nhl/mlb/soccer."""
    ep = get_team_stats_endpoint(sport_slug)
    assert ep is not None
    assert ep.path == expected_path
    assert ep.sport_key == expected_sport_key
    assert ep.required_params == ["league", "season", "team"]


def test_team_stats_endpoint_unsupported_returns_none() -> None:
    assert get_team_stats_endpoint("unknown") is None
    assert get_team_stats_endpoint("") is None


def test_team_stats_endpoint_required_params() -> None:
    ep = get_team_stats_endpoint("nba")
    assert ep is not None
    assert "league" in ep.required_params
    assert "season" in ep.required_params
    assert "team" in ep.required_params
