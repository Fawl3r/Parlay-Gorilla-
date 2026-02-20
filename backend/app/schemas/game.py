"""Game-related Pydantic schemas"""

from pydantic import BaseModel
from datetime import datetime
from typing import List
from decimal import Decimal


class OddsResponse(BaseModel):
    """Odds response schema"""
    id: str
    outcome: str
    price: str
    decimal_price: Decimal
    implied_prob: Decimal
    created_at: datetime


class MarketResponse(BaseModel):
    """Market response schema"""
    id: str
    market_type: str
    book: str
    odds: List[OddsResponse]


class GameResponse(BaseModel):
    """Game response schema"""
    id: str
    external_game_id: str
    sport: str
    home_team: str
    away_team: str
    start_time: datetime
    status: str
    week: int | None = None  # NFL week number (1-18 regular season, 19-22 postseason)
    markets: List[MarketResponse]
    home_score: int | None = None  # Final/live score (cached with games list to reduce requests)
    away_score: int | None = None


class GamesListResponse(BaseModel):
    """Games list with optional sport-state metadata for empty-state UI."""
    games: List[GameResponse]
    sport_state: str | None = None
    next_game_at: str | None = None
    status_label: str | None = None
    days_to_next: int | None = None
    preseason_enable_days: int | None = None

