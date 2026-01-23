"""Score normalizer for converting scraped data to canonical format."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.services.team_name_normalizer import TeamNameNormalizer


@dataclass
class GameUpdate:
    """Normalized game update from scraper."""
    external_game_key: str
    home_team: str
    away_team: str
    home_score: Optional[int]
    away_score: Optional[int]
    status: str  # SCHEDULED, LIVE, FINAL, POSTPONED, CANCELLED
    period: Optional[str]  # Q3, 2nd, 7th inning, etc.
    clock: Optional[str]  # 04:12, etc.
    start_time: datetime
    data_source: str  # espn, yahoo, etc.


class ScoreNormalizer:
    """Normalize scraped score data to match games table."""
    
    def __init__(self):
        self._team_normalizer = TeamNameNormalizer()
    
    def normalize_team_name(self, team_name: str) -> str:
        """Normalize team name for matching."""
        return self._team_normalizer.normalize(team_name)
    
    def normalize_status(self, raw_status: str, sport: str) -> str:
        """Normalize game status to canonical format.
        
        Maps various status strings to: SCHEDULED, LIVE, FINAL, POSTPONED, CANCELLED
        """
        status_lower = str(raw_status or "").lower().strip()
        
        # FINAL states
        if status_lower in ("final", "finished", "complete", "ft", "f", "completed"):
            return "FINAL"
        
        # LIVE states
        if status_lower in ("live", "in progress", "in-progress", "in_progress", "playing", "active"):
            return "LIVE"
        
        # POSTPONED states
        if status_lower in ("postponed", "postponed", "delayed", "suspended"):
            return "POSTPONED"
        
        # CANCELLED states
        if status_lower in ("cancelled", "canceled", "cancelled"):
            return "CANCELLED"
        
        # Default to SCHEDULED
        return "SCHEDULED"
    
    def normalize_period(self, raw_period: str, sport: str) -> Optional[str]:
        """Normalize period/quarter/inning to canonical format."""
        if not raw_period:
            return None
        
        period_str = str(raw_period).strip()
        
        # Sport-specific normalization
        sport_upper = sport.upper()
        
        if sport_upper in ("NFL", "NCAAF"):
            # Quarters: Q1, Q2, Q3, Q4, OT
            if period_str.upper().startswith("Q"):
                return period_str.upper()
            if "overtime" in period_str.lower() or "ot" in period_str.lower():
                return "OT"
        
        elif sport_upper in ("NBA", "NCAAB"):
            # Quarters: Q1, Q2, Q3, Q4, OT
            if period_str.upper().startswith("Q"):
                return period_str.upper()
            if "overtime" in period_str.lower() or "ot" in period_str.lower():
                return "OT"
        
        elif sport_upper == "NHL":
            # Periods: 1st, 2nd, 3rd, OT
            if "period" in period_str.lower():
                return period_str
            if "overtime" in period_str.lower() or "ot" in period_str.lower():
                return "OT"
        
        elif sport_upper == "MLB":
            # Innings: 1st, 2nd, 3rd, etc.
            if "inning" in period_str.lower():
                return period_str
        
        # Return as-is if no specific normalization
        return period_str
    
    def create_external_game_key(self, home_team: str, away_team: str, start_time: datetime, sport: str) -> str:
        """Create external game key for scraper matching.
        
        Format: sport:normalized_home:normalized_away:date
        """
        home_norm = self.normalize_team_name(home_team)
        away_norm = self.normalize_team_name(away_team)
        date_str = start_time.strftime("%Y%m%d")
        
        return f"{sport.lower()}:{home_norm}:{away_norm}:{date_str}"
