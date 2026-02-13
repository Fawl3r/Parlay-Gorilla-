"""Shared minimal fixtures for UgieV2Builder and analysis-edge tests. One place for draft/odds/probs/matchup/game."""

from datetime import datetime, timezone
from typing import Any, Dict


def minimal_draft() -> Dict[str, Any]:
    return {
        "offensive_matchup_edges": {},
        "defensive_matchup_edges": {},
        "outcome_paths": {},
        "confidence_breakdown": {},
        "best_bets": [],
        "ai_spread_pick": {},
        "ai_total_pick": {},
    }


def minimal_matchup_data() -> Dict[str, Any]:
    return {
        "home_injuries": {},
        "away_injuries": {},
        "home_team_stats": {},
        "away_team_stats": {},
    }


def minimal_game(sport: str = "nfl") -> Any:
    g = type("Game", (), {})()
    g.sport = sport
    g.home_team = "Home"
    g.away_team = "Away"
    return g


def minimal_odds() -> Dict[str, Any]:
    return {"home_spread_point": -3.0, "total_line": 45.0, "home_ml": -150, "away_ml": 130}


def minimal_model_probs() -> Dict[str, Any]:
    return {"home_win_prob": 0.55, "away_win_prob": 0.45, "ai_confidence": 60.0}


def fixed_test_now() -> datetime:
    """Fixed UTC time for deterministic sport-state/listing-window tests."""
    return datetime(2026, 2, 13, 12, 0, 0, tzinfo=timezone.utc)
