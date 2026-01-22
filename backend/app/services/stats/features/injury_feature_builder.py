"""Injury feature builder for impact scoring and trend detection."""

from __future__ import annotations

from typing import Dict, List, Optional

from app.services.sports.sport_registry import get_sport_capability


class InjuryFeatureBuilder:
    """Builds injury impact features from canonical injury data."""
    
    # Severity weights
    SEVERITY_WEIGHTS = {
        "out": 1.0,
        "doubtful": 0.8,
        "questionable": 0.5,
        "probable": 0.2,
    }
    
    def build_impact_scores(
        self,
        canonical_injuries: Dict,
        sport: str,
        previous_injuries: Optional[Dict] = None,
    ) -> Dict:
        """Build impact scores and trend from canonical injuries.
        
        Args:
            canonical_injuries: Canonical injury dictionary
            sport: Sport identifier
            previous_injuries: Previous snapshot for trend detection
        
        Returns:
            Updated canonical_injuries with computed impact_scores and trend
        """
        unit_counts = canonical_injuries.get("unit_counts", {})
        capability = get_sport_capability(sport)
        unit_mappings = capability.unit_mappings
        
        # Compute impact scores
        impact_scores = self._compute_impact_scores(unit_counts, sport, unit_mappings)
        
        # Detect trend
        trend = self._detect_trend(canonical_injuries, previous_injuries)
        
        # Update canonical_injuries
        canonical_injuries["impact_scores"] = impact_scores
        canonical_injuries["trend"] = trend
        
        return canonical_injuries
    
    def _compute_impact_scores(
        self,
        unit_counts: Dict,
        sport: str,
        unit_mappings: Dict[str, List[str]],
    ) -> Dict:
        """Compute offense, defense, and overall impact scores.
        
        Impact is weighted by:
        - Severity (OUT > DOUBTFUL > QUESTIONABLE > PROBABLE)
        - Unit importance (sport-specific)
        """
        # Sport-specific unit importance weights
        # Higher weight = more important unit
        unit_weights = self._get_unit_weights(sport, unit_mappings)
        
        # Compute weighted impact per unit
        offense_impact_sum = 0.0
        defense_impact_sum = 0.0
        total_weight = 0.0
        
        for unit_name, counts in unit_counts.items():
            if not isinstance(counts, dict):
                continue
            
            # Get unit weight
            unit_weight = unit_weights.get(unit_name, 0.5)  # Default 0.5 if not specified
            
            # Compute weighted count
            weighted_count = (
                counts.get("out", 0) * self.SEVERITY_WEIGHTS["out"] +
                counts.get("doubtful", 0) * self.SEVERITY_WEIGHTS["doubtful"] +
                counts.get("questionable", 0) * self.SEVERITY_WEIGHTS["questionable"] +
                counts.get("probable", 0) * self.SEVERITY_WEIGHTS["probable"]
            )
            
            # Determine if unit affects offense, defense, or both
            offense_weight, defense_weight = self._get_unit_offense_defense_weights(unit_name, sport)
            
            offense_impact_sum += weighted_count * unit_weight * offense_weight
            defense_impact_sum += weighted_count * unit_weight * defense_weight
            total_weight += unit_weight
        
        # Normalize to 0.0-1.0
        # Assume max impact is 3+ key players out (arbitrary threshold)
        max_expected_impact = 3.0 * total_weight if total_weight > 0 else 1.0
        
        offense_impact = min(1.0, offense_impact_sum / max_expected_impact) if max_expected_impact > 0 else 0.0
        defense_impact = min(1.0, defense_impact_sum / max_expected_impact) if max_expected_impact > 0 else 0.0
        overall_impact = (offense_impact + defense_impact) / 2.0
        
        # Uncertainty: increases with questionable/probable volume
        questionable_count = sum(
            counts.get("questionable", 0) + counts.get("probable", 0)
            for counts in unit_counts.values()
            if isinstance(counts, dict)
        )
        uncertainty = min(1.0, questionable_count / 5.0)  # 5+ questionable = high uncertainty
        
        return {
            "offense_impact": offense_impact,
            "defense_impact": defense_impact,
            "overall_impact": overall_impact,
            "uncertainty": uncertainty,
        }
    
    def _get_unit_weights(self, sport: str, unit_mappings: Dict[str, List[str]]) -> Dict[str, float]:
        """Get unit importance weights for a sport.
        
        Returns dict mapping unit_name -> weight (0.0-1.0)
        """
        sport_lower = sport.lower()
        
        if sport_lower in ["nfl", "ncaaf"]:
            return {
                "qb_room": 1.0,  # Most important
                "skill_positions": 0.7,
                "offensive_line": 0.6,
                "defensive_front": 0.7,
                "secondary": 0.6,
            }
        elif sport_lower in ["nba", "ncaab"]:
            return {
                "guard_rotation": 0.8,
                "wing_rotation": 0.7,
                "big_rotation": 0.7,
            }
        elif sport_lower in ["nhl"]:
            return {
                "top_lines": 0.9,
                "defense_pairs": 0.7,
                "goalie_status": 1.0,  # Most important
            }
        elif sport_lower in ["mlb"]:
            return {
                "starter_rotation": 0.8,
                "bullpen": 0.6,
                "lineup_core": 0.7,
            }
        elif sport_lower in ["mls", "epl", "laliga", "ucl", "soccer"]:
            return {
                "forward_line": 0.8,
                "midfield": 0.7,
                "defense": 0.7,
                "goalkeeper": 1.0,  # Most important
            }
        
        # Default weights
        return {}
    
    def _get_unit_offense_defense_weights(self, unit_name: str, sport: str) -> tuple[float, float]:
        """Get offense/defense impact weights for a unit.
        
        Returns (offense_weight, defense_weight) tuple.
        """
        sport_lower = sport.lower()
        
        if sport_lower in ["nfl", "ncaaf"]:
            if unit_name in ["qb_room", "skill_positions", "offensive_line"]:
                return (1.0, 0.0)  # Offense only
            elif unit_name in ["defensive_front", "secondary"]:
                return (0.0, 1.0)  # Defense only
        elif sport_lower in ["nba", "ncaab"]:
            # Basketball units affect both
            if unit_name in ["guard_rotation", "wing_rotation", "big_rotation"]:
                return (0.6, 0.4)  # Slightly more offense
        elif sport_lower in ["nhl"]:
            if unit_name == "goalie_status":
                return (0.0, 1.0)  # Defense only
            elif unit_name in ["top_lines"]:
                return (0.7, 0.3)  # More offense
            elif unit_name in ["defense_pairs"]:
                return (0.2, 0.8)  # More defense
        elif sport_lower in ["mlb"]:
            if unit_name in ["starter_rotation", "bullpen"]:
                return (0.0, 1.0)  # Pitching is defense
            elif unit_name in ["lineup_core"]:
                return (1.0, 0.0)  # Offense only
        elif sport_lower in ["mls", "epl", "laliga", "ucl", "soccer"]:
            if unit_name == "goalkeeper":
                return (0.0, 1.0)  # Defense only
            elif unit_name in ["forward_line"]:
                return (1.0, 0.0)  # Offense only
            elif unit_name in ["midfield"]:
                return (0.5, 0.5)  # Both
            elif unit_name in ["defense"]:
                return (0.0, 1.0)  # Defense only
        
        # Default: equal weight
        return (0.5, 0.5)
    
    def _detect_trend(
        self,
        current_injuries: Dict,
        previous_injuries: Optional[Dict],
    ) -> str:
        """Detect injury trend: improving, worsening, or stable.
        
        Compares current overall_impact with previous overall_impact.
        """
        if not previous_injuries:
            return "stable"
        
        current_impact = current_injuries.get("impact_scores", {}).get("overall_impact", 0.0)
        previous_impact = previous_injuries.get("impact_scores", {}).get("overall_impact", 0.0)
        
        # Threshold for significant change
        threshold = 0.1
        
        if current_impact < previous_impact - threshold:
            return "improving"
        elif current_impact > previous_impact + threshold:
            return "worsening"
        else:
            return "stable"
