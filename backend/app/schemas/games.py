"""Game feed schemas."""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel


class GameFeedResponse(BaseModel):
    """Game feed response."""
    id: str
    sport: str
    home_team: str
    away_team: str
    start_time: str
    status: str
    home_score: Optional[int]
    away_score: Optional[int]
    period: Optional[str]
    clock: Optional[str]
    is_stale: bool
