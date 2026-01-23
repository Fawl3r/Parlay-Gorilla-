"""System status schemas."""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel


class SystemStatusResponse(BaseModel):
    """System status response."""
    scraper_last_beat_at: Optional[str]
    settlement_last_beat_at: Optional[str]
    games_updated_last_run: int
    parlays_settled_today: int
    last_score_sync_at: Optional[str]
