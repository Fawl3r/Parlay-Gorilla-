"""Analytics-related Pydantic schemas"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class AnalyticsGameResponse(BaseModel):
    """Game data for analytics heatmap"""
    game_id: str
    matchup: str  # "Away @ Home"
    home_team: str
    away_team: str
    sport: str
    start_time: str  # ISO format
    slug: Optional[str] = None  # Analysis slug if exists
    
    # Market data
    home_win_prob: Optional[float] = None  # 0-1, only for moneyline
    away_win_prob: Optional[float] = None  # 0-1, only for moneyline
    spread_confidence: Optional[float] = None  # 0-100, only for spreads
    total_confidence: Optional[float] = None  # 0-100, only for totals
    
    # Status badges
    has_cached_analysis: bool
    is_trending: bool
    traffic_score: float  # 0-1
    
    # Confidence threshold for high-confidence badge
    confidence_threshold: float = 70.0


class AnalyticsSnapshotResponse(BaseModel):
    """Analytics hero snapshot data"""
    games_tracked_today: int
    model_accuracy_last_100: Optional[float] = None  # 0-100
    high_confidence_games: int
    trending_matchup: Optional[str] = None  # "Away @ Home"


class AnalyticsResponse(BaseModel):
    """Complete analytics page data"""
    snapshot: AnalyticsSnapshotResponse
    games: List[AnalyticsGameResponse]
    total_games: int
