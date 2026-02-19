"""Unit tests for per-sport stat extractors (standings entry + raw API response -> key_team_stats)."""

import pytest

from app.services.apisports.stat_extractors import (
    extract_baseball_team_stats,
    extract_basketball_team_stats,
    extract_football_team_stats,
    extract_hockey_team_stats,
    extract_key_stats_baseball,
    extract_key_stats_basketball,
    extract_key_stats_football,
    extract_key_stats_hockey,
    extract_soccer_team_stats,
    format_display_value,
)


# Mock API-Sports standings entry shapes (one team row)

NBA_ENTRY = {
    "team": {"id": 1, "name": "Lakers"},
    "position": 3,
    "goalsFor": 112,
    "goalsAgainst": 108,
    "all": {"win": 42, "lose": 30, "played": 72},
}

WNBA_ENTRY = {
    "team": {"id": 2, "name": "Liberty"},
    "goals_for": 86,
    "goals_against": 82,
    "all": {"win": 28, "lose": 12},
}

NFL_ENTRY = {
    "team": {"id": 10, "name": "Chiefs"},
    "goalsFor": 450,
    "goalsAgainst": 320,
    "all": {"win": 14, "lose": 3},
    "total_yards": 6200,
    "pass_yards": 4200,
    "rush_yards": 2000,
}

NHL_ENTRY = {
    "team": {"id": 20, "name": "Bruins"},
    "goalsFor": 280,
    "goalsAgainst": 220,
    "all": {"win": 52, "lose": 22},
    "shotsFor": 2100,
    "shotsAgainst": 1900,
}

MLB_ENTRY = {
    "team": {"id": 30, "name": "Yankees"},
    "goalsFor": 850,
    "goalsAgainst": 680,
    "all": {"win": 95, "lose": 67},
    "runs_for": 850,
    "runs_against": 680,
    "era": 3.85,
    "avg": 0.262,
}


def test_extract_key_stats_basketball_nba():
    out = extract_key_stats_basketball(NBA_ENTRY)
    assert out.get("points_for") == 112
    assert out.get("points_against") == 108
    assert out.get("wins") == 42
    assert out.get("losses") == 30
    assert "points_for" in out
    assert "points_against" in out
    assert "wins" in out
    assert "losses" in out


def test_extract_key_stats_basketball_wnba():
    out = extract_key_stats_basketball(WNBA_ENTRY)
    assert out.get("points_for") == 86
    assert out.get("points_against") == 82
    assert out.get("wins") == 28
    assert out.get("losses") == 12


def test_extract_key_stats_basketball_empty():
    assert extract_key_stats_basketball({}) == {}
    assert extract_key_stats_basketball(None) == {}


def test_extract_key_stats_football():
    out = extract_key_stats_football(NFL_ENTRY)
    assert out.get("points_for") == 450
    assert out.get("points_against") == 320
    assert out.get("wins") == 14
    assert out.get("losses") == 3
    assert out.get("total_yards") == 6200
    assert out.get("pass_yards") == 4200
    assert out.get("rush_yards") == 2000


def test_extract_key_stats_football_minimal():
    out = extract_key_stats_football({"goalsFor": 300, "goalsAgainst": 250, "all": {"win": 10, "lose": 6}})
    assert out.get("points_for") == 300
    assert out.get("points_against") == 250
    assert out.get("wins") == 10
    assert out.get("losses") == 6


def test_extract_key_stats_hockey():
    out = extract_key_stats_hockey(NHL_ENTRY)
    assert out.get("goals_for") == 280
    assert out.get("goals_against") == 220
    assert out.get("wins") == 52
    assert out.get("losses") == 22
    assert out.get("shots_for") == 2100
    assert out.get("shots_against") == 1900


def test_extract_key_stats_hockey_minimal():
    out = extract_key_stats_hockey({"goalsFor": 200, "goalsAgainst": 180, "all": {"win": 44, "lose": 30}})
    assert out.get("goals_for") == 200
    assert out.get("goals_against") == 180
    assert out.get("wins") == 44
    assert out.get("losses") == 30


def test_extract_key_stats_baseball():
    out = extract_key_stats_baseball(MLB_ENTRY)
    assert out.get("runs_for") == 850
    assert out.get("runs_against") == 680
    assert out.get("wins") == 95
    assert out.get("losses") == 67
    assert out.get("era") == 3.85
    assert out.get("avg") == 0.262


def test_extract_key_stats_baseball_goals_aliases():
    out = extract_key_stats_baseball({"goalsFor": 700, "goalsAgainst": 600, "all": {"win": 88, "lose": 74}})
    assert out.get("runs_for") == 700
    assert out.get("runs_against") == 600
    assert out.get("wins") == 88
    assert out.get("losses") == 74


def test_extract_key_stats_values_normalized():
    out = extract_key_stats_basketball({"goalsFor": "110", "goalsAgainst": "105", "all": {"win": "40", "lose": "32"}})
    assert out["points_for"] == 110
    assert out["points_against"] == 105
    assert out["wins"] == 40
    assert out["losses"] == 32


# --- Raw API statistics response extractors (on-demand team stats) ---

RAW_NBA_RESPONSE = {
    "response": [{
        "games": 72,
        "points": 8200,
        "points_against": 7800,
        "wins": 42,
        "losses": 30,
        "fg_pct": 0.472,
        "three_pct": 0.362,
        "ft_pct": 0.798,
        "rebounds": 3500,
        "assists": 1800,
        "turnovers": 1100,
    }],
}

RAW_NFL_RESPONSE = {
    "response": [{
        "games": 17,
        "points": 450,
        "points_against": 320,
        "total_yards": 6200,
        "passing_yards": 4200,
        "rushing_yards": 2000,
        "turnovers": 18,
    }],
}

RAW_NHL_RESPONSE = {
    "response": [{
        "games": 82,
        "goals_for": 280,
        "goals_against": 220,
        "shots_for": 2500,
        "shots_against": 2300,
        "power_play_percentage": 22.5,
        "penalty_kill_percentage": 81.0,
    }],
}

RAW_MLB_RESPONSE = {
    "response": [{
        "games": 162,
        "runs": 750,
        "runs_against": 650,
        "avg": 0.258,
        "era": 3.85,
        "whip": 1.22,
        "hr": 220,
    }],
}

RAW_SOCCER_RESPONSE = {
    "response": {
        "fixtures": {"played": 38},
        "goals": {"for": 75, "against": 42},
        "possession": 58,
    },
}


def test_extract_basketball_team_stats_raw():
    out = extract_basketball_team_stats(RAW_NBA_RESPONSE)
    assert out["points_for"] == round(8200 / 72, 1)
    assert out["points_against"] == round(7800 / 72, 1)
    assert out["wins"] == 42
    assert out["losses"] == 30
    assert out["fg_pct"] == 47.2
    assert "rebounds" in out
    assert "assists" in out


def test_extract_football_team_stats_raw():
    out = extract_football_team_stats(RAW_NFL_RESPONSE)
    assert out["points_for"] == round(450 / 17, 1)
    assert out["points_against"] == round(320 / 17, 1)
    assert out["total_yards"] == round(6200 / 17, 1)
    assert out["pass_yards"] == round(4200 / 17, 1)
    assert out["rush_yards"] == round(2000 / 17, 1)


def test_extract_hockey_team_stats_raw():
    out = extract_hockey_team_stats(RAW_NHL_RESPONSE)
    assert out["goals_for"] == round(280 / 82, 2)
    assert out["goals_against"] == round(220 / 82, 2)
    assert out["shots_for"] == round(2500 / 82, 1)
    assert out["power_play_pct"] == 22.5
    assert out["penalty_kill_pct"] == 81.0


def test_extract_baseball_team_stats_raw():
    out = extract_baseball_team_stats(RAW_MLB_RESPONSE)
    assert out["runs_for"] == round(750 / 162, 2)
    assert out["runs_against"] == round(650 / 162, 2)
    assert out["era"] == 3.85
    assert out["whip"] == 1.22
    assert out["hr"] == 220


def test_extract_soccer_team_stats_raw():
    out = extract_soccer_team_stats(RAW_SOCCER_RESPONSE)
    assert out["goals_for"] == round(75 / 38, 2)
    assert out["goals_against"] == round(42 / 38, 2)
    assert out["possession"] == 58.0  # 0-100 scale


def test_raw_extractors_empty():
    assert extract_basketball_team_stats(None) == {}
    assert extract_basketball_team_stats({}) == {}
    assert extract_football_team_stats({}) == {}
    assert extract_soccer_team_stats({"response": []}) == {}


def test_format_display_value():
    assert format_display_value("fg_pct", 47.2) == "47.2%"
    assert format_display_value("points_for", 112.5) == "112.5"
    assert format_display_value("wins", 42) == "42"
    assert format_display_value("x", None) == "—"
