"""Build 'What Changed' delta summaries comparing current vs previous analysis."""

from typing import Dict, Any, Optional, List
from datetime import datetime, timezone


class DeltaSummaryBuilder:
    """Generate delta summaries for analysis updates."""
    
    @staticmethod
    def build(
        *,
        current_analysis: Dict[str, Any],
        previous_analysis: Optional[Dict[str, Any]] = None,
        line_movement: Optional[Dict[str, Any]] = None,
        matchup_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Build delta summary showing what changed since last update.
        
        Args:
            current_analysis: Current analysis content
            previous_analysis: Previous analysis content (if available)
            line_movement: Line movement data from odds history
            matchup_data: Current matchup data (for injury changes)
        
        Returns:
            Dict with delta summary including:
            - line_changes: Spread/total/moneyline changes
            - injury_changes: New injuries or status updates
            - pick_changes: Changes to recommended picks
            - summary: Human-readable summary
        """
        deltas: List[str] = []
        line_changes: Dict[str, Any] = {}
        injury_changes: List[str] = []
        pick_changes: List[str] = []
        
        # Check line movement
        if line_movement:
            spread_change = line_movement.get("spread_movement")
            total_change = line_movement.get("total_movement")
            ml_change = line_movement.get("moneyline_movement")
            
            if spread_change:
                old_spread = spread_change.get("old")
                new_spread = spread_change.get("new")
                if old_spread != new_spread:
                    line_changes["spread"] = {
                        "old": old_spread,
                        "new": new_spread,
                        "direction": "up" if (new_spread or 0) > (old_spread or 0) else "down",
                    }
                    deltas.append(f"Spread moved from {old_spread} to {new_spread}")
            
            if total_change:
                old_total = total_change.get("old")
                new_total = total_change.get("new")
                if old_total != new_total:
                    line_changes["total"] = {
                        "old": old_total,
                        "new": new_total,
                        "direction": "up" if (new_total or 0) > (old_total or 0) else "down",
                    }
                    deltas.append(f"Total moved from {old_total} to {new_total}")
            
            if ml_change:
                old_home_ml = ml_change.get("home_ml_old")
                new_home_ml = ml_change.get("home_ml_new")
                if old_home_ml != new_home_ml:
                    line_changes["moneyline"] = {
                        "home_old": old_home_ml,
                        "home_new": new_home_ml,
                    }
                    deltas.append(f"Home moneyline moved from {old_home_ml} to {new_home_ml}")
        
        # Check injury changes (compare current vs previous)
        if previous_analysis:
            prev_injuries = previous_analysis.get("matchup_data", {}).get("home_injuries", [])
            curr_injuries = matchup_data.get("home_injuries", [])
            
            if isinstance(curr_injuries, list) and isinstance(prev_injuries, list):
                new_injuries = [inj for inj in curr_injuries if inj not in prev_injuries]
                if new_injuries:
                    injury_changes.extend([f"New injury: {inj}" for inj in new_injuries[:3]])
                    deltas.extend([f"New injury: {inj}" for inj in new_injuries[:3]])
        
        # Check pick changes
        if previous_analysis:
            prev_spread_pick = previous_analysis.get("ai_spread_pick", {})
            curr_spread_pick = current_analysis.get("ai_spread_pick", {})
            
            prev_side = prev_spread_pick.get("side")
            curr_side = curr_spread_pick.get("side")
            
            if prev_side and curr_side and prev_side != curr_side:
                pick_changes.append(f"Spread pick changed from {prev_side} to {curr_side}")
                deltas.append(f"Spread pick changed from {prev_side} to {curr_side}")
            
            prev_total_pick = previous_analysis.get("ai_total_pick", {})
            curr_total_pick = current_analysis.get("ai_total_pick", {})
            
            prev_direction = prev_total_pick.get("direction")
            curr_direction = curr_total_pick.get("direction")
            
            if prev_direction and curr_direction and prev_direction != curr_direction:
                pick_changes.append(f"Total pick changed from {prev_direction} to {curr_direction}")
                deltas.append(f"Total pick changed from {prev_direction} to {curr_direction}")
        
        # Build summary
        summary = ""
        if deltas:
            if len(deltas) == 1:
                summary = deltas[0]
            elif len(deltas) <= 3:
                summary = f"Updates: {', '.join(deltas)}"
            else:
                summary = f"Multiple updates: {', '.join(deltas[:3])} and {len(deltas) - 3} more"
        else:
            summary = "No significant changes since last update"
        
        return {
            "has_changes": len(deltas) > 0,
            "line_changes": line_changes,
            "injury_changes": injury_changes,
            "pick_changes": pick_changes,
            "summary": summary,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
