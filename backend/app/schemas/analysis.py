"""Analysis schemas for API responses"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class SpreadPick(BaseModel):
    """AI spread pick with confidence"""
    pick: str
    confidence: float = Field(..., ge=0, le=100)
    rationale: str


class TotalPick(BaseModel):
    """AI total pick with confidence"""
    pick: str
    confidence: float = Field(..., ge=0, le=100)
    rationale: str


class BestBet(BaseModel):
    """Best bet recommendation"""
    bet_type: str
    pick: str
    confidence: float = Field(..., ge=0, le=100)
    rationale: str


class ModelWinProbability(BaseModel):
    """Model win probability with confidence score"""
    home_win_prob: float = Field(..., ge=0, le=1)
    away_win_prob: float = Field(..., ge=0, le=1)
    explanation: str
    ai_confidence: Optional[float] = Field(None, ge=0, le=100, description="Model confidence score (0-100)")
    calculation_method: Optional[str] = Field(None, description="How the probability was calculated")
    score_projection: Optional[str] = Field(None, description="Projected final score")


class MatchupEdges(BaseModel):
    """Offensive or defensive matchup edges"""
    home_advantage: str
    away_advantage: str
    key_matchup: str


class TrendAnalysis(BaseModel):
    """ATS or totals trend analysis"""
    home_team_trend: str
    away_team_trend: str
    analysis: str


class SameGameParlay(BaseModel):
    """Same-game parlay recommendation"""
    legs: List[Dict[str, Any]]
    hit_probability: Optional[float] = Field(None, ge=0, le=1)
    confidence: Optional[float] = Field(None, ge=0, le=100)
    # Alternative format fields
    type: Optional[str] = None
    title: Optional[str] = None
    total_odds: Optional[str] = None
    rationale: Optional[str] = None

    class Config:
        extra = "allow"  # Allow extra fields for flexibility


class SameGameParlays(BaseModel):
    """All same-game parlay tiers - dict format"""
    safe_3_leg: Optional[SameGameParlay] = None
    balanced_6_leg: Optional[SameGameParlay] = None
    degen_10_20_leg: Optional[SameGameParlay] = None

    class Config:
        extra = "allow"


class WeatherData(BaseModel):
    """Weather conditions for the game"""
    temperature: Optional[float] = None
    feels_like: Optional[float] = None
    condition: Optional[str] = None
    description: Optional[str] = None
    wind_speed: Optional[float] = None
    wind_direction: Optional[float] = None
    humidity: Optional[float] = None
    precipitation: Optional[float] = None
    is_outdoor: Optional[bool] = True
    affects_game: Optional[bool] = False


class GameAnalysisContent(BaseModel):
    """Full analysis content structure"""
    headline: Optional[str] = None
    subheadline: Optional[str] = None
    opening_summary: str
    offensive_matchup_edges: Optional[MatchupEdges] = None
    defensive_matchup_edges: Optional[MatchupEdges] = None
    key_stats: Optional[List[str]] = None
    ats_trends: Optional[TrendAnalysis] = None
    totals_trends: Optional[TrendAnalysis] = None
    weather_considerations: Optional[str] = None
    weather_data: Optional[WeatherData] = None
    model_win_probability: Optional[ModelWinProbability] = None
    ai_spread_pick: Optional[SpreadPick] = None
    ai_total_pick: Optional[TotalPick] = None
    best_bets: Optional[List[BestBet]] = None
    # Accept either list or dict format for same_game_parlays
    same_game_parlays: Optional[Any] = None
    full_article: Optional[str] = None

    class Config:
        extra = "allow"  # Allow extra fields for flexibility


class GameAnalysisResponse(BaseModel):
    """Complete game analysis response"""
    id: str
    slug: str
    league: str
    matchup: str
    game_id: str
    analysis_content: GameAnalysisContent
    seo_metadata: Optional[Dict[str, Any]] = None
    generated_at: datetime
    expires_at: Optional[datetime] = None
    version: int


class GameAnalysisListItem(BaseModel):
    """List item for analysis index"""
    id: str
    slug: str
    league: str
    matchup: str
    game_time: datetime
    generated_at: datetime


class AnalysisGenerationRequest(BaseModel):
    """Request to generate analysis"""
    game_id: str
    force_regenerate: bool = False

