"""Canonical team stats schema for cross-sport normalization."""

from __future__ import annotations

from typing import Dict, Optional
from pydantic import BaseModel, Field


class Record(BaseModel):
    """Team win-loss-tie record."""
    wins: int = 0
    losses: int = 0
    ties: int = 0


class Scoring(BaseModel):
    """Scoring metrics (points/runs/goals depending on sport)."""
    points_for_avg: Optional[float] = None  # NFL/NBA/NHL
    points_against_avg: Optional[float] = None
    runs_for_avg: Optional[float] = None  # MLB
    runs_against_avg: Optional[float] = None
    goals_for_avg: Optional[float] = None  # NHL
    goals_against_avg: Optional[float] = None


class Efficiency(BaseModel):
    """Efficiency ratings."""
    offense_rating: Optional[float] = None
    defense_rating: Optional[float] = None
    net_rating: Optional[float] = None


class Tempo(BaseModel):
    """Tempo/pace metrics."""
    pace: Optional[float] = None  # Plays/game, possessions/game, etc.


class SplitStats(BaseModel):
    """Home or away split statistics."""
    points_for_avg: Optional[float] = None
    points_against_avg: Optional[float] = None
    runs_for_avg: Optional[float] = None  # MLB
    runs_against_avg: Optional[float] = None
    goals_for_avg: Optional[float] = None  # NHL
    goals_against_avg: Optional[float] = None


class Splits(BaseModel):
    """Home/away splits."""
    home: SplitStats = Field(default_factory=SplitStats)
    away: SplitStats = Field(default_factory=SplitStats)


class LastNStats(BaseModel):
    """Statistics for last N games."""
    form_score: Optional[float] = None  # -1.0 to 1.0, weighted by recency
    points_for_avg: Optional[float] = None
    points_against_avg: Optional[float] = None
    runs_for_avg: Optional[float] = None  # MLB
    runs_against_avg: Optional[float] = None
    goals_for_avg: Optional[float] = None  # NHL
    goals_against_avg: Optional[float] = None
    wins: Optional[int] = None
    losses: Optional[int] = None
    ties: Optional[int] = None


class LastN(BaseModel):
    """Last N games statistics."""
    last_3: LastNStats = Field(default_factory=LastNStats)
    last_5: LastNStats = Field(default_factory=LastNStats)
    last_10: LastNStats = Field(default_factory=LastNStats)


class CanonicalTeamStats(BaseModel):
    """Canonical team statistics schema that applies across all sports.
    
    Some fields may be null depending on sport, but keys should exist
    for consistency.
    """
    record: Record = Field(default_factory=Record)
    scoring: Scoring = Field(default_factory=Scoring)
    efficiency: Efficiency = Field(default_factory=Efficiency)
    tempo: Tempo = Field(default_factory=Tempo)
    splits: Splits = Field(default_factory=Splits)
    last_n: LastN = Field(default_factory=LastN)
    
    class Config:
        """Pydantic config."""
        extra = "allow"  # Allow additional fields for extensibility


def normalize_stats(raw_stats: Dict, sport: str) -> Dict:
    """Normalize raw stats from external sources to canonical schema.
    
    Args:
        raw_stats: Raw stats dictionary from external API
        sport: Sport identifier (e.g., "NFL", "MLB", "NHL")
    
    Returns:
        Normalized dictionary matching CanonicalTeamStats schema
    """
    sport_lower = sport.lower()
    
    # Extract record
    record = {
        "wins": raw_stats.get("wins", raw_stats.get("record", {}).get("wins", 0)),
        "losses": raw_stats.get("losses", raw_stats.get("record", {}).get("losses", 0)),
        "ties": raw_stats.get("ties", raw_stats.get("record", {}).get("ties", 0)),
    }
    
    # Extract scoring - map sport-specific fields
    scoring = {}
    if sport_lower in ["nfl", "nba", "ncaaf", "ncaab"]:
        scoring["points_for_avg"] = raw_stats.get("points_per_game") or raw_stats.get("offense", {}).get("points_per_game")
        scoring["points_against_avg"] = raw_stats.get("points_allowed_per_game") or raw_stats.get("defense", {}).get("points_allowed_per_game")
    elif sport_lower in ["mlb"]:
        scoring["runs_for_avg"] = raw_stats.get("runs_per_game") or raw_stats.get("offense", {}).get("runs_per_game")
        scoring["runs_against_avg"] = raw_stats.get("runs_allowed_per_game") or raw_stats.get("defense", {}).get("runs_allowed_per_game")
    elif sport_lower in ["nhl"]:
        scoring["goals_for_avg"] = raw_stats.get("goals_per_game") or raw_stats.get("offense", {}).get("goals_per_game")
        scoring["goals_against_avg"] = raw_stats.get("goals_allowed_per_game") or raw_stats.get("defense", {}).get("goals_allowed_per_game")
        # Also include points for NHL (points = wins*2 + ot_losses*1)
        scoring["points_for_avg"] = scoring.get("goals_for_avg")
        scoring["points_against_avg"] = scoring.get("goals_against_avg")
    
    # Extract efficiency ratings
    efficiency = {
        "offense_rating": raw_stats.get("offensive_rating") or raw_stats.get("strength_ratings", {}).get("offensive_rating"),
        "defense_rating": raw_stats.get("defensive_rating") or raw_stats.get("strength_ratings", {}).get("defensive_rating"),
        "net_rating": raw_stats.get("overall_rating") or raw_stats.get("strength_ratings", {}).get("overall_rating"),
    }
    
    # Extract tempo/pace
    tempo = {
        "pace": raw_stats.get("pace") or raw_stats.get("tempo", {}).get("pace"),
    }
    
    # Extract splits
    splits = {
        "home": {
            "points_for_avg": raw_stats.get("home_record", {}).get("points_for_avg") if isinstance(raw_stats.get("home_record"), dict) else None,
            "points_against_avg": raw_stats.get("home_record", {}).get("points_against_avg") if isinstance(raw_stats.get("home_record"), dict) else None,
        },
        "away": {
            "points_for_avg": raw_stats.get("away_record", {}).get("points_for_avg") if isinstance(raw_stats.get("away_record"), dict) else None,
            "points_against_avg": raw_stats.get("away_record", {}).get("points_against_avg") if isinstance(raw_stats.get("away_record"), dict) else None,
        },
    }
    
    # Extract last N games
    recent_form = raw_stats.get("recent_form", {})
    last_n = {
        "last_3": {
            "form_score": None,  # Will be computed by feature builder
            "points_for_avg": recent_form.get("last_3", {}).get("points_for_avg") if isinstance(recent_form.get("last_3"), dict) else None,
            "points_against_avg": recent_form.get("last_3", {}).get("points_against_avg") if isinstance(recent_form.get("last_3"), dict) else None,
            "wins": recent_form.get("last_3", {}).get("wins") if isinstance(recent_form.get("last_3"), dict) else None,
            "losses": recent_form.get("last_3", {}).get("losses") if isinstance(recent_form.get("last_3"), dict) else None,
        },
        "last_5": {
            "form_score": None,
            "points_for_avg": recent_form.get("last_5", {}).get("points_for_avg") if isinstance(recent_form.get("last_5"), dict) else None,
            "points_against_avg": recent_form.get("last_5", {}).get("points_against_avg") if isinstance(recent_form.get("last_5"), dict) else None,
            "wins": recent_form.get("recent_wins") or recent_form.get("last_5", {}).get("wins") if isinstance(recent_form.get("last_5"), dict) else None,
            "losses": recent_form.get("recent_losses") or recent_form.get("last_5", {}).get("losses") if isinstance(recent_form.get("last_5"), dict) else None,
        },
        "last_10": {
            "form_score": None,
            "points_for_avg": recent_form.get("last_10", {}).get("points_for_avg") if isinstance(recent_form.get("last_10"), dict) else None,
            "points_against_avg": recent_form.get("last_10", {}).get("points_against_avg") if isinstance(recent_form.get("last_10"), dict) else None,
        },
    }
    
    # Build normalized dict
    normalized = {
        "record": record,
        "scoring": scoring,
        "efficiency": efficiency,
        "tempo": tempo,
        "splits": splits,
        "last_n": last_n,
    }
    
    # Validate with Pydantic model
    try:
        canonical = CanonicalTeamStats(**normalized)
        return canonical.dict(exclude_none=False)
    except Exception:
        # If validation fails, return normalized dict anyway (graceful degradation)
        return normalized
