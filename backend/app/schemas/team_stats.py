"""Team statistics schemas"""

from pydantic import BaseModel
from typing import Optional, Dict, Any


class TeamMatchupStats(BaseModel):
    """
    Structured container for team matchup statistics.
    All fields are optional to support graceful degradation when data is unavailable.
    """
    home_team_stats: Optional[Dict[str, Any]] = None
    away_team_stats: Optional[Dict[str, Any]] = None
    home_injuries: Optional[Dict[str, Any]] = None
    away_injuries: Optional[Dict[str, Any]] = None
    weather: Optional[Dict[str, Any]] = None
    rest_days_home: Optional[int] = None
    rest_days_away: Optional[int] = None
    travel_distance: Optional[float] = None
    is_divisional: Optional[bool] = None
    head_to_head: Optional[Dict[str, Any]] = None
    home_team_name: str = ""
    away_team_name: str = ""
    sport: str = "NFL"
    
    class Config:
        extra = "allow"


class TeamStatsResponse(BaseModel):
    id: str
    team_name: str
    season: str
    week: Optional[int]
    wins: int
    losses: int
    ties: int
    win_percentage: float
    points_per_game: float
    yards_per_game: float
    points_allowed_per_game: float
    ats_record_overall: str
    ats_record_home: str
    ats_record_away: str
    ou_record_overall: str
    ou_record_home: str
    ou_record_away: str
    offensive_rating: float
    defensive_rating: float
    overall_rating: float

