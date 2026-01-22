"""Portfolio guidance builder - risk buckets for betting recommendations."""

from __future__ import annotations

from typing import Any, Dict, List


class PortfolioGuidanceBuilder:
    """Build portfolio guidance with risk buckets."""

    @staticmethod
    def build(
        *,
        spread_pick: Dict[str, Any],
        total_pick: Dict[str, Any],
        same_game_parlays: Dict[str, Any],
        confidence_total: float,
    ) -> Dict[str, Any]:
        """
        Build portfolio guidance with risk categorization.
        
        Args:
            spread_pick: AI spread pick
            total_pick: AI total pick
            same_game_parlays: Same-game parlay structure
            confidence_total: Total confidence score (0-100)
            
        Returns:
            Dict with low_risk, medium_risk, high_risk, exposure_note
        """
        low_risk: List[str] = []
        medium_risk: List[str] = []
        high_risk: List[str] = []
        
        # Low risk: Core picks (always present)
        if spread_pick and spread_pick.get("pick"):
            low_risk.append("ai_spread_pick")
        
        if total_pick and total_pick.get("pick"):
            low_risk.append("ai_total_pick")
        
        # Medium risk: Alt lines and team totals (if present in analysis)
        # Note: These would need to be extracted from odds_snapshot or markets
        # For now, we'll check if they exist in the picks structure
        # This can be extended when alt lines are added to the analysis
        
        # High risk: Same-game parlays
        if same_game_parlays:
            safe_sgp = same_game_parlays.get("safe_3_leg")
            balanced_sgp = same_game_parlays.get("balanced_6_leg")
            
            if safe_sgp and isinstance(safe_sgp, dict) and safe_sgp.get("legs"):
                high_risk.append("safe_3_leg_sgp")
            
            if balanced_sgp and isinstance(balanced_sgp, dict) and balanced_sgp.get("legs"):
                high_risk.append("balanced_6_leg_sgp")
        
        return {
            "low_risk": low_risk,
            "medium_risk": medium_risk,  # Will be populated when alt lines are added
            "high_risk": high_risk,
            "exposure_note": "Keep exposure <= 2% bankroll per game; avoid stacking correlated legs.",
        }
