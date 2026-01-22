"""Data quality scoring for stats and injury data."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional


class DataQualityScorer:
    """Calculates data quality metrics: freshness, completeness, consistency, trust."""
    
    def calculate_quality(
        self,
        updated_at: datetime,
        canonical_stats: Optional[Dict] = None,
        canonical_injuries: Optional[Dict] = None,
        previous_stats: Optional[Dict] = None,
        previous_injuries: Optional[Dict] = None,
        sources_used: List[str] = None,
    ) -> Dict:
        """Calculate comprehensive data quality metrics.
        
        Args:
            updated_at: Timestamp when data was last updated
            canonical_stats: Current canonical stats (for completeness check)
            canonical_injuries: Current canonical injuries (for completeness check)
            previous_stats: Previous stats snapshot (for consistency check)
            previous_injuries: Previous injuries snapshot (for consistency check)
            sources_used: List of data sources used (e.g., ["db", "api_espn"])
        
        Returns:
            Data quality dictionary with freshness, completeness, consistency, trust_score, warnings
        """
        now = datetime.utcnow()
        if isinstance(updated_at, str):
            # Parse ISO string if needed
            try:
                updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
            except:
                updated_at = now
        
        freshness_hours = (now - updated_at).total_seconds() / 3600.0
        
        completeness = self._calculate_completeness(canonical_stats, canonical_injuries)
        consistency = self._calculate_consistency(
            canonical_stats, previous_stats,
            canonical_injuries, previous_injuries
        )
        trust_score = self._calculate_trust_score(freshness_hours, completeness, consistency)
        
        warnings = self._generate_warnings(freshness_hours, completeness, consistency, sources_used)
        
        return {
            "freshness_hours": round(freshness_hours, 2),
            "completeness": round(completeness, 3),
            "consistency": round(consistency, 3),
            "trust_score": round(trust_score, 3),
            "sources_used": sources_used or [],
            "warnings": warnings,
        }
    
    def _calculate_freshness(self, updated_at: datetime) -> float:
        """Calculate freshness in hours.
        
        Returns:
            Hours since updated_at
        """
        now = datetime.utcnow()
        if isinstance(updated_at, str):
            try:
                updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
            except:
                updated_at = now
        
        return (now - updated_at).total_seconds() / 3600.0
    
    def _calculate_completeness(
        self,
        canonical_stats: Optional[Dict],
        canonical_injuries: Optional[Dict],
    ) -> float:
        """Calculate completeness score (0.0-1.0).
        
        Checks for presence of key canonical fields.
        """
        if not canonical_stats and not canonical_injuries:
            return 0.0
        
        required_fields = []
        present_fields = []
        
        # Stats completeness
        if canonical_stats:
            required_fields.extend([
                "record",
                "scoring",
                "efficiency",
            ])
            
            if canonical_stats.get("record"):
                present_fields.append("record")
            if canonical_stats.get("scoring"):
                scoring = canonical_stats["scoring"]
                # Check if at least one scoring metric is present
                if any([
                    scoring.get("points_for_avg"),
                    scoring.get("runs_for_avg"),
                    scoring.get("goals_for_avg"),
                ]):
                    present_fields.append("scoring")
            if canonical_stats.get("efficiency"):
                present_fields.append("efficiency")
        
        # Injuries completeness
        if canonical_injuries:
            required_fields.append("unit_counts")
            if canonical_injuries.get("unit_counts"):
                present_fields.append("unit_counts")
        
        if not required_fields:
            return 1.0  # No requirements = complete
        
        return len(present_fields) / len(required_fields)
    
    def _calculate_consistency(
        self,
        current_stats: Optional[Dict],
        previous_stats: Optional[Dict],
        current_injuries: Optional[Dict],
        previous_injuries: Optional[Dict],
    ) -> float:
        """Calculate consistency score (0.0-1.0).
        
        Compares current vs previous snapshot to detect unrealistic jumps.
        Penalizes large changes that suggest data errors.
        """
        if not previous_stats and not previous_injuries:
            return 1.0  # No previous data = consistent (can't compare)
        
        consistency_scores = []
        
        # Stats consistency
        if current_stats and previous_stats:
            stats_consistency = self._check_stats_consistency(current_stats, previous_stats)
            if stats_consistency is not None:
                consistency_scores.append(stats_consistency)
        
        # Injuries consistency
        if current_injuries and previous_injuries:
            injuries_consistency = self._check_injuries_consistency(current_injuries, previous_injuries)
            if injuries_consistency is not None:
                consistency_scores.append(injuries_consistency)
        
        if not consistency_scores:
            return 1.0  # Can't compute = assume consistent
        
        return sum(consistency_scores) / len(consistency_scores)
    
    def _check_stats_consistency(self, current: Dict, previous: Dict) -> Optional[float]:
        """Check consistency of stats between snapshots.
        
        Detects unrealistic jumps (e.g., PPG changes >50%).
        """
        current_scoring = current.get("scoring", {})
        previous_scoring = previous.get("scoring", {})
        
        # Get scoring averages
        current_avg = (
            current_scoring.get("points_for_avg") or
            current_scoring.get("runs_for_avg") or
            current_scoring.get("goals_for_avg")
        )
        previous_avg = (
            previous_scoring.get("points_for_avg") or
            previous_scoring.get("runs_for_avg") or
            previous_scoring.get("goals_for_avg")
        )
        
        if not current_avg or not previous_avg:
            return None  # Can't compare
        
        if previous_avg == 0:
            return 1.0  # Can't compute percentage change
        
        # Calculate percentage change
        pct_change = abs((current_avg - previous_avg) / previous_avg)
        
        # Penalize large changes
        # 0-10% change = 1.0 (consistent)
        # 10-25% change = 0.8 (slightly inconsistent)
        # 25-50% change = 0.5 (inconsistent)
        # >50% change = 0.2 (very inconsistent)
        if pct_change <= 0.10:
            return 1.0
        elif pct_change <= 0.25:
            return 0.8
        elif pct_change <= 0.50:
            return 0.5
        else:
            return 0.2
    
    def _check_injuries_consistency(self, current: Dict, previous: Dict) -> Optional[float]:
        """Check consistency of injuries between snapshots.
        
        Injuries can change, but large swings might indicate data errors.
        """
        current_impact = current.get("impact_scores", {}).get("overall_impact", 0.0)
        previous_impact = previous.get("impact_scores", {}).get("overall_impact", 0.0)
        
        # Impact changes are more acceptable than stats changes
        # 0-20% change = 1.0 (consistent)
        # 20-40% change = 0.8
        # 40-60% change = 0.6
        # >60% change = 0.4
        impact_change = abs(current_impact - previous_impact)
        
        if impact_change <= 0.20:
            return 1.0
        elif impact_change <= 0.40:
            return 0.8
        elif impact_change <= 0.60:
            return 0.6
        else:
            return 0.4
    
    def _calculate_trust_score(
        self,
        freshness_hours: float,
        completeness: float,
        consistency: float,
    ) -> float:
        """Calculate overall trust score (0.0-1.0).
        
        Weighted composite:
        - Freshness: 40%
        - Completeness: 30%
        - Consistency: 30%
        """
        # Freshness component (0.0-1.0)
        # 0-24 hours = 1.0
        # 24-48 hours = 0.8
        # 48-72 hours = 0.6
        # 72-168 hours (1 week) = 0.4
        # >168 hours = 0.2
        if freshness_hours <= 24:
            freshness_score = 1.0
        elif freshness_hours <= 48:
            freshness_score = 0.8
        elif freshness_hours <= 72:
            freshness_score = 0.6
        elif freshness_hours <= 168:
            freshness_score = 0.4
        else:
            freshness_score = 0.2
        
        # Weighted composite
        trust_score = (
            freshness_score * 0.4 +
            completeness * 0.3 +
            consistency * 0.3
        )
        
        # Clamp to 0.0-1.0
        return max(0.0, min(1.0, trust_score))
    
    def _generate_warnings(
        self,
        freshness_hours: float,
        completeness: float,
        consistency: float,
        sources_used: Optional[List[str]],
    ) -> List[str]:
        """Generate warnings based on data quality metrics."""
        warnings = []
        
        if freshness_hours > 48:
            warnings.append("stale_data")
        if freshness_hours > 168:
            warnings.append("very_stale_data")
        
        if completeness < 0.5:
            warnings.append("incomplete_data")
        if completeness < 0.3:
            warnings.append("severely_incomplete_data")
        
        if consistency < 0.5:
            warnings.append("inconsistent_data")
        
        if not sources_used or len(sources_used) == 0:
            warnings.append("no_sources")
        elif "db" not in sources_used and len(sources_used) == 1:
            warnings.append("api_only_data")
        
        return warnings
