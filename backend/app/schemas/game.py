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
    week: int | None = None  # NFL week number (1-18 for regular season)
    markets: List[MarketResponse]

