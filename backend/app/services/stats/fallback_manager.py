"""Smart fallback rules for stats and injury data fetching."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.services.fetch_budget import FetchBudgetManager
from app.services.sports.sport_registry import SeasonMode, get_season_mode


@dataclass
class FetchContext:
    """Context for determining whether to fetch data."""
    game_time: Optional[datetime] = None  # Proximity to game
    traffic_gate: bool = False  # Is this high-traffic game?
    fetch_budget: Optional[FetchBudgetManager] = None  # Budget tracking
    season_mode: Optional[SeasonMode] = None  # IN_SEASON | OFF_SEASON


class FallbackManager:
    """Manages smart fallback rules for data fetching."""
    
    # TTL thresholds (hours)
    STATS_TTL_HOURS = 24
    INJURY_TTL_HOURS = 12
    FEATURES_TTL_HOURS = 24
    
    def __init__(self, stats_ttl_hours: int = None, injury_ttl_hours: int = None):
        """Initialize with optional custom TTLs."""
        if stats_ttl_hours is not None:
            self.STATS_TTL_HOURS = stats_ttl_hours
        if injury_ttl_hours is not None:
            self.INJURY_TTL_HOURS = injury_ttl_hours
    
    def should_fetch_stats(
        self,
        freshness_hours: float,
        context: FetchContext,
        data_missing: bool = False,
    ) -> bool:
        """Determine if stats should be fetched from external API.
        
        Args:
            freshness_hours: Hours since data was last updated
            context: Fetch context with game_time, traffic_gate, etc.
            data_missing: True if no data exists (always fetch if missing)
        
        Returns:
            True if should fetch, False otherwise
        """
        # Always fetch if data is missing and we're in season
        if data_missing:
            if context.season_mode == SeasonMode.OFF_SEASON:
                return False  # Don't fetch for off-season if missing
            return True
        
        # Check TTL
        if freshness_hours < self.STATS_TTL_HOURS:
            return False  # Still fresh, don't fetch
        
        # Check season mode
        if context.season_mode == SeasonMode.OFF_SEASON:
            return False  # Don't fetch for off-season
        
        # Check traffic gate
        if not context.traffic_gate:
            # Low traffic: only fetch if very stale (2x TTL)
            if freshness_hours < (self.STATS_TTL_HOURS * 2):
                return False
        
        # Check fetch budget
        if context.fetch_budget:
            # Check if we have budget for stats fetch
            # This is a simplified check - actual budget logic is in FetchBudgetManager
            pass  # Budget check handled by caller
        
        return True
    
    def should_fetch_injuries(
        self,
        freshness_hours: float,
        context: FetchContext,
        data_missing: bool = False,
    ) -> bool:
        """Determine if injuries should be fetched from external API.
        
        Args:
            freshness_hours: Hours since data was last updated
            context: Fetch context
            data_missing: True if no data exists
        
        Returns:
            True if should fetch, False otherwise
        """
        # Always fetch if data is missing and we're in season
        if data_missing:
            if context.season_mode == SeasonMode.OFF_SEASON:
                return False
            return True
        
        # Check TTL (tighter for injuries)
        if freshness_hours < self.INJURY_TTL_HOURS:
            return False
        
        # Check season mode
        if context.season_mode == SeasonMode.OFF_SEASON:
            return False
        
        # Injuries are higher priority near game time
        if context.game_time:
            hours_to_game = (context.game_time - datetime.utcnow()).total_seconds() / 3600.0
            if 0 <= hours_to_game <= 24:
                # Within 24 hours of game: always refresh if stale
                return True
        
        # Check traffic gate
        if not context.traffic_gate:
            # Low traffic: only fetch if very stale
            if freshness_hours < (self.INJURY_TTL_HOURS * 2):
                return False
        
        return True
    
    def should_fetch_features(
        self,
        freshness_hours: float,
        context: FetchContext,
    ) -> bool:
        """Determine if features should be recomputed.
        
        Features are computed from stats/injuries, so this is mainly
        a check for when to trigger recomputation.
        """
        if freshness_hours < self.FEATURES_TTL_HOURS:
            return False
        
        # Always recompute if stats/injuries were just updated
        # This is typically called after stats/injuries update
        return True
