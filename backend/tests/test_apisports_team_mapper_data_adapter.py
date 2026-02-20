"""Integration tests for API-Sports team mapper, data adapter, and feature pipeline.

Tests team name mapping accuracy, data adapter conversions, and that the feature
pipeline uses API-Sports components (SportsDataRepository, FeatureBuilderService).
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from app.services.apisports.team_mapper import (
    ApiSportsTeamMapper,
    get_team_mapper,
    TEAM_NAME_TO_ID,
    SPORT_KEY_NFL,
    SPORT_KEY_NBA,
    SPORT_KEY_WNBA,
    SPORT_KEY_FOOTBALL,
)
from app.services.apisports.data_adapter import ApiSportsDataAdapter
from app.services.feature_pipeline import FeaturePipeline


# ----- Team Mapper -----


def test_team_mapper_add_and_get_team_id():
    """Adding a mapping and get_team_id returns the correct ID."""
    mapper = ApiSportsTeamMapper()
    # Use a clean sport key; add_mapping mutates module-level TEAM_NAME_TO_ID
    mapper.add_mapping("Baltimore Ravens", 1, SPORT_KEY_NFL)
    assert mapper.get_team_id("Baltimore Ravens", SPORT_KEY_NFL) == 1
    assert mapper.get_team_id("baltimore ravens", SPORT_KEY_NFL) == 1


def test_team_mapper_get_team_name():
    """get_team_name returns normalized name for known team_id."""
    mapper = ApiSportsTeamMapper()
    mapper.add_mapping("Buffalo Bills", 2, SPORT_KEY_NFL)
    name = mapper.get_team_name(2, SPORT_KEY_NFL)
    assert name is not None
    assert "buffalo" in name.lower() and "bills" in name.lower()


def test_team_mapper_normalize_sport_key():
    """Sport key normalization: nfl -> americanfootball_nfl, etc."""
    mapper = ApiSportsTeamMapper()
    assert mapper.get_team_id("Unknown Team", "nfl") is None  # no mapping
    mapper.add_mapping("Kansas City Chiefs", 3, "nfl")
    # "nfl" should normalize to americanfootball_nfl
    assert mapper.get_team_id("Kansas City Chiefs", "americanfootball_nfl") == 3


def test_team_mapper_football_means_soccer():
    """football must mean soccer (SPORT_KEY_FOOTBALL), not NFL."""
    mapper = ApiSportsTeamMapper()
    mapper.add_mapping("Arsenal", 42, SPORT_KEY_FOOTBALL)
    # "football" must map to soccer, so get_team_id with "football" finds soccer mapping
    assert mapper.get_team_id("Arsenal", "football") == 42
    assert mapper.get_team_id("Arsenal", "soccer") == 42
    # American football must be explicit (nfl / americanfootball_nfl)
    mapper.add_mapping("Ravens", 1, SPORT_KEY_NFL)
    assert mapper.get_team_id("Ravens", "nfl") == 1
    assert mapper.get_team_id("Ravens", "americanfootball_nfl") == 1
    assert mapper.get_team_id("Ravens", "football") != 1  # football = soccer, not NFL


def test_team_mapper_populate_from_fixtures():
    """populate_from_fixtures adds mappings from fixture list."""
    mapper = ApiSportsTeamMapper()
    fixtures = [
        {
            "teams": {
                "home": {"id": 10, "name": "Team Alpha"},
                "away": {"id": 20, "name": "Team Beta"},
            }
        },
    ]
    count = mapper.populate_from_fixtures(fixtures, SPORT_KEY_NBA)
    assert count >= 2
    assert mapper.get_team_id("Team Alpha", SPORT_KEY_NBA) == 10
    assert mapper.get_team_id("Team Beta", SPORT_KEY_NBA) == 20


def test_get_team_mapper_singleton():
    """get_team_mapper returns an ApiSportsTeamMapper instance."""
    mapper = get_team_mapper()
    assert isinstance(mapper, ApiSportsTeamMapper)


# ----- Data Adapter -----


def test_adapter_fixture_to_game_schedule():
    """fixture_to_game_schedule converts API-Sports fixture to internal format."""
    fixture = {
        "fixture": {"id": 12345, "date": "2025-09-15T17:00:00+00:00", "status": {"short": "NS"}},
        "league": {"id": 1, "name": "NFL"},
        "teams": {
            "home": {"id": 1, "name": "Ravens"},
            "away": {"id": 2, "name": "Bills"},
        },
    }
    out = ApiSportsDataAdapter.fixture_to_game_schedule(fixture, SPORT_KEY_NFL)
    assert out is not None
    assert out["fixture_id"] == 12345
    assert out["league_id"] == 1
    assert out["home_team_name"] == "Ravens"
    assert out["away_team_name"] == "Bills"
    assert out["status"] == "NS"
    assert isinstance(out.get("date"), datetime)


def test_adapter_fixture_to_game_schedule_missing_id_returns_none():
    """fixture_to_game_schedule returns None when fixture has no id."""
    fixture = {"fixture": {}, "league": {}, "teams": {}}
    assert ApiSportsDataAdapter.fixture_to_game_schedule(fixture, SPORT_KEY_NFL) is None


def test_adapter_result_to_game_result():
    """result_to_game_result converts API-Sports result to internal format."""
    result = {
        "fixture": {"id": 999, "date": "2025-09-14T23:30:00+00:00"},
        "teams": {"home": {"id": 1}, "away": {"id": 2}},
        "score": {"fulltime": {"home": 27, "away": 24}},
    }
    out = ApiSportsDataAdapter.result_to_game_result(result, SPORT_KEY_NFL)
    assert out is not None
    assert out["fixture_id"] == 999
    assert out["home_team_id"] == 1
    assert out["away_team_id"] == 2
    assert out["home_score"] == 27
    assert out["away_score"] == 24
    assert out["sport"] == SPORT_KEY_NFL


def test_adapter_result_to_game_result_missing_id_returns_none():
    """result_to_game_result returns None when fixture has no id."""
    result = {"fixture": {}, "teams": {}, "score": {}}
    assert ApiSportsDataAdapter.result_to_game_result(result, SPORT_KEY_NFL) is None


def test_adapter_standings_to_team_strength():
    """standings_to_team_strength extracts team strength from standings."""
    standings = {
        "league": {
            "standings": [
                [
                    {"rank": 1, "team": {"id": 1}, "points": 30, "all": {"played": 10, "win": 8, "lose": 2, "draw": 0}},
                    {"rank": 2, "team": {"id": 2}, "points": 25, "all": {"played": 10, "win": 7, "lose": 2, "draw": 1}},
                ]
            ]
        }
    }
    out = ApiSportsDataAdapter.standings_to_team_strength(standings, "football", 39)
    assert isinstance(out, dict)
    assert 1 in out
    assert 2 in out
    assert out[1].get("rank") == 1
    assert out[1].get("points") == 30
    assert out[1].get("win_percentage") == 0.8


def test_standings_to_normalized_team_stats_nfl():
    """standings_to_normalized_team_stats derives normalized team stats (NFL-style)."""
    standings = {
        "league": {
            "standings": [
                {
                    "rank": 1,
                    "team": {"id": 10, "name": "Ravens"},
                    "all": {"played": 10, "win": 8, "lose": 2, "draw": 0, "goals": {"for": 250, "against": 180}},
                },
                {
                    "rank": 2,
                    "team": {"id": 20, "name": "Bills"},
                    "all": {"played": 10, "win": 7, "lose": 3, "draw": 0, "goals": {"for": 230, "against": 190}},
                },
            ]
        }
    }
    out = ApiSportsDataAdapter.standings_to_normalized_team_stats(standings, SPORT_KEY_NFL, 1, "2024")
    assert len(out) == 2
    by_id = {x["team_id"]: x for x in out}
    assert 10 in by_id and 20 in by_id
    r = by_id[10]
    assert r["team_name"] == "Ravens"
    assert r["wins"] == 8 and r["losses"] == 2
    assert r["games_played"] == 10
    assert r["points_per_game"] == 25.0  # 250/10
    assert r["points_allowed_per_game"] == 18.0  # 180/10


def test_standings_to_normalized_team_stats_nba():
    """standings_to_normalized_team_stats derives normalized team stats (NBA direct list)."""
    standings = {
        "league": {
            "standings": [
                {"team": {"id": 100, "name": "Lakers"}, "all": {"played": 20, "win": 14, "lose": 6, "draw": 0, "goals": {"for": 2240, "against": 2180}}},
                {"team": {"id": 101, "name": "Celtics"}, "all": {"played": 20, "win": 16, "lose": 4, "draw": 0, "goals": {"for": 2320, "against": 2100}}},
            ]
        }
    }
    out = ApiSportsDataAdapter.standings_to_normalized_team_stats(standings, SPORT_KEY_NBA, 12, "2024-2025")
    assert len(out) == 2
    by_id = {x["team_id"]: x for x in out}
    assert 100 in by_id
    assert by_id[100]["points_per_game"] == 112.0  # 2240/20
    assert by_id[100]["points_allowed_per_game"] == 109.0  # 2180/20


def test_standings_to_normalized_team_stats_wnba():
    """WNBA should use the same basketball extraction path as NBA."""
    standings = {
        "league": {
            "standings": [
                {"team": {"id": 200, "name": "Aces"}, "all": {"played": 20, "win": 15, "lose": 5, "draw": 0, "goals": {"for": 1700, "against": 1600}}},
                {"team": {"id": 201, "name": "Liberty"}, "all": {"played": 20, "win": 14, "lose": 6, "draw": 0, "goals": {"for": 1680, "against": 1580}}},
            ]
        }
    }
    out = ApiSportsDataAdapter.standings_to_normalized_team_stats(standings, SPORT_KEY_WNBA, 13, "2025")
    assert len(out) == 2
    by_id = {x["team_id"]: x for x in out}
    assert 200 in by_id
    assert by_id[200]["points_per_game"] == 85.0
    assert by_id[200]["points_allowed_per_game"] == 80.0


def test_adapter_normalized_payload_to_internal():
    """team_stats_to_internal_format accepts normalized payload and returns StatsScraperService-compatible dict."""
    normalized = {
        "team_id": 5,
        "team_name": "Test Team",
        "wins": 9,
        "losses": 3,
        "draws": 0,
        "games_played": 12,
        "points_per_game": 24.5,
        "points_allowed_per_game": 19.0,
    }
    out = ApiSportsDataAdapter.team_stats_to_internal_format(normalized, 5, SPORT_KEY_NFL, "2024")
    assert out is not None
    assert out.get("team_name") == "Test Team"
    assert out.get("record", {}).get("wins") == 9
    assert out.get("offense", {}).get("points_per_game") == 24.5
    assert out.get("defense", {}).get("points_allowed_per_game") == 19.0
    assert "recent_form" in out
    assert "strength_ratings" in out


# ----- Feature Pipeline (integration) -----


def test_adapter_outputs_have_expected_keys_and_types():
    """Data quality: adapter outputs have expected keys and value types."""
    fixture = {
        "fixture": {"id": 1, "date": "2025-01-01T12:00:00+00:00", "status": {"short": "FT"}},
        "league": {"id": 1, "name": "NFL"},
        "teams": {"home": {"id": 1, "name": "A"}, "away": {"id": 2, "name": "B"}},
    }
    schedule = ApiSportsDataAdapter.fixture_to_game_schedule(fixture, SPORT_KEY_NFL)
    assert schedule is not None
    assert "fixture_id" in schedule and isinstance(schedule["fixture_id"], int)
    assert "home_team_name" in schedule and "away_team_name" in schedule
    assert "date" in schedule and (schedule["date"] is None or hasattr(schedule["date"], "isoformat"))

    result = {
        "fixture": {"id": 2, "date": "2025-01-01T15:00:00+00:00"},
        "teams": {"home": {"id": 1}, "away": {"id": 2}},
        "score": {"fulltime": {"home": 21, "away": 17}},
    }
    game_result = ApiSportsDataAdapter.result_to_game_result(result, SPORT_KEY_NFL)
    assert game_result is not None
    assert "home_score" in game_result and "away_score" in game_result
    assert game_result["home_score"] == 21 and game_result["away_score"] == 17


@pytest.mark.asyncio
async def test_feature_pipeline_uses_apisports_components():
    """FeaturePipeline is constructed with SportsDataRepository and API-Sports services."""
    mock_db = AsyncMock()
    pipeline = FeaturePipeline(mock_db)
    assert hasattr(pipeline, "db")
    assert pipeline.db is mock_db
    assert hasattr(pipeline, "_apisports_repo")
    assert pipeline._apisports_repo is not None
    assert hasattr(pipeline, "_feature_builder")
    assert pipeline._feature_builder is not None
    assert hasattr(pipeline, "_team_mapper")
    assert hasattr(pipeline, "_data_adapter")
