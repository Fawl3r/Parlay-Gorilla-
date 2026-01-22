"""Tools-related Pydantic schemas"""

from pydantic import BaseModel
from typing import Optional


class HeatmapProbabilityResponse(BaseModel):
    """Model probabilities for a game in the odds heatmap"""
    game_id: str
    home_win_prob: float
    away_win_prob: float
    spread_confidence: Optional[float] = None  # From ai_spread_pick (0-100)
    total_confidence: Optional[float] = None  # From ai_total_pick (0-100)
    has_cached_analysis: bool
