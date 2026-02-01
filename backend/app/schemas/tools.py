"""Tools-related Pydantic schemas"""

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


class HeatmapProbabilityResponse(BaseModel):
    """Model probabilities for a game in the odds heatmap"""
    game_id: str
    home_win_prob: float
    away_win_prob: float
    spread_confidence: Optional[float] = None  # From ai_spread_pick (0-100)
    total_confidence: Optional[float] = None  # From ai_total_pick (0-100)
    has_cached_analysis: bool


class UpsetCandidateToolsResponse(BaseModel):
    """One upset candidate from GET /api/tools/upsets"""
    game_id: str
    start_time: str
    league: str
    home_team: str
    away_team: str
    underdog_side: str
    underdog_team: str
    underdog_ml: int
    implied_prob: float
    model_prob: float
    edge: float
    confidence: float

    # ROI trust boosters (optional; safe for staggered deploys)
    books_count: int = 0
    best_underdog_ml: Optional[int] = None
    median_underdog_ml: Optional[int] = None
    price_spread: Optional[int] = None
    worst_underdog_ml: Optional[int] = None
    flags: List[str] = Field(default_factory=list)  # e.g. ["stale_odds_suspected","low_books"]
    odds_quality: str = "bad"  # good | thin | bad

    market_disagreement: Optional[str] = None
    reasons: List[str] = Field(default_factory=list)


class UpsetFinderToolsAccess(BaseModel):
    """Access state for Upset Finder results."""

    can_view_candidates: bool
    # "login_required" | "premium_required" | None
    reason: Optional[str] = None


class UpsetFinderToolsMeta(BaseModel):
    """Honest scanning meta for Upset Finder."""

    games_scanned: int
    games_with_odds: int
    missing_odds: int
    games_scanned_capped: Optional[bool] = None


class UpsetFinderToolsResponse(BaseModel):
    """Response for GET /api/tools/upsets"""
    sport: str
    window_days: int
    min_edge: float
    max_results: int
    min_underdog_odds: int
    generated_at: str
    access: UpsetFinderToolsAccess
    candidates: List[UpsetCandidateToolsResponse]
    meta: UpsetFinderToolsMeta
    # Populated only when backend couldn't compute real meta/results.
    error: Optional[str] = None
