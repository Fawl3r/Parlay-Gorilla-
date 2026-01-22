"""Canonical injury schema for cross-sport normalization."""

from __future__ import annotations

from typing import Dict, List, Literal, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class UnitCount(BaseModel):
    """Count of injuries by severity for a unit."""
    out: int = 0
    doubtful: int = 0
    questionable: int = 0
    probable: int = 0


class UnitCounts(BaseModel):
    """Injury counts by unit (sport-specific)."""
    # NFL units
    qb_room: UnitCount = Field(default_factory=UnitCount)
    skill_positions: UnitCount = Field(default_factory=UnitCount)
    offensive_line: UnitCount = Field(default_factory=UnitCount)
    defensive_front: UnitCount = Field(default_factory=UnitCount)
    secondary: UnitCount = Field(default_factory=UnitCount)
    
    # NBA units
    guard_rotation: UnitCount = Field(default_factory=UnitCount)
    wing_rotation: UnitCount = Field(default_factory=UnitCount)
    big_rotation: UnitCount = Field(default_factory=UnitCount)
    
    # MLB units
    starter_rotation: UnitCount = Field(default_factory=UnitCount)
    bullpen: UnitCount = Field(default_factory=UnitCount)
    lineup_core: UnitCount = Field(default_factory=UnitCount)
    
    # NHL units
    top_lines: UnitCount = Field(default_factory=UnitCount)
    defense_pairs: UnitCount = Field(default_factory=UnitCount)
    goalie_status: UnitCount = Field(default_factory=UnitCount)
    
    # Soccer units
    forward_line: UnitCount = Field(default_factory=UnitCount)
    midfield: UnitCount = Field(default_factory=UnitCount)
    defense: UnitCount = Field(default_factory=UnitCount)
    goalkeeper: UnitCount = Field(default_factory=UnitCount)
    
    class Config:
        """Pydantic config."""
        extra = "allow"  # Allow additional sport-specific units


class ImpactScores(BaseModel):
    """Impact scores for injuries."""
    offense_impact: float = 0.0  # 0.0-1.0, weighted impact on offense
    defense_impact: float = 0.0  # 0.0-1.0, weighted impact on defense
    overall_impact: float = 0.0  # 0.0-1.0, overall weighted impact
    uncertainty: float = 0.0  # 0.0-1.0, uncertainty in impact assessment


class CanonicalInjuries(BaseModel):
    """Canonical injury schema that applies across all sports.
    
    Unit counts are sport-specific, but the structure is consistent.
    Impact scores are computed from unit counts.
    """
    unit_counts: UnitCounts = Field(default_factory=UnitCounts)
    impact_scores: ImpactScores = Field(default_factory=ImpactScores)
    trend: Literal["improving", "worsening", "stable"] = "stable"
    last_updated: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    
    class Config:
        """Pydantic config."""
        extra = "allow"


def normalize_injuries(raw_injuries: Dict, sport: str, unit_mappings: Dict[str, List[str]]) -> Dict:
    """Normalize raw injury data from external sources to canonical schema.
    
    Args:
        raw_injuries: Raw injury dictionary from external API
        sport: Sport identifier (e.g., "NFL", "MLB", "NHL")
        unit_mappings: Sport-specific unit mappings from sport_registry
    
    Returns:
        Normalized dictionary matching CanonicalInjuries schema
    """
    # Initialize unit counts
    unit_counts = {}
    
    # Extract player injuries from raw data
    players = raw_injuries.get("players", raw_injuries.get("key_players_out", []))
    if not isinstance(players, list):
        players = []
    
    # Map players to units based on position/role
    for player in players:
        if not isinstance(player, dict):
            continue
        
        position = (player.get("position") or player.get("pos") or "").lower()
        status = (player.get("status") or player.get("injury_status") or "questionable").lower()
        
        # Determine which unit this player belongs to
        unit_name = None
        for unit, keywords in unit_mappings.items():
            if any(keyword in position for keyword in keywords):
                unit_name = unit
                break
        
        if not unit_name:
            continue
        
        # Initialize unit if not exists
        if unit_name not in unit_counts:
            unit_counts[unit_name] = {"out": 0, "doubtful": 0, "questionable": 0, "probable": 0}
        
        # Count by status
        if status in ["out", "injured reserve", "ir"]:
            unit_counts[unit_name]["out"] += 1
        elif status in ["doubtful"]:
            unit_counts[unit_name]["doubtful"] += 1
        elif status in ["questionable", "day-to-day", "dtd"]:
            unit_counts[unit_name]["questionable"] += 1
        elif status in ["probable", "likely"]:
            unit_counts[unit_name]["probable"] += 1
        else:
            # Default to questionable if unknown
            unit_counts[unit_name]["questionable"] += 1
    
    # Build unit_counts dict with all possible units (sport-specific ones will be populated)
    all_unit_counts = {
        "qb_room": unit_counts.get("qb_room", {"out": 0, "doubtful": 0, "questionable": 0, "probable": 0}),
        "skill_positions": unit_counts.get("skill_positions", {"out": 0, "doubtful": 0, "questionable": 0, "probable": 0}),
        "offensive_line": unit_counts.get("offensive_line", {"out": 0, "doubtful": 0, "questionable": 0, "probable": 0}),
        "defensive_front": unit_counts.get("defensive_front", {"out": 0, "doubtful": 0, "questionable": 0, "probable": 0}),
        "secondary": unit_counts.get("secondary", {"out": 0, "doubtful": 0, "questionable": 0, "probable": 0}),
        "guard_rotation": unit_counts.get("guard_rotation", {"out": 0, "doubtful": 0, "questionable": 0, "probable": 0}),
        "wing_rotation": unit_counts.get("wing_rotation", {"out": 0, "doubtful": 0, "questionable": 0, "probable": 0}),
        "big_rotation": unit_counts.get("big_rotation", {"out": 0, "doubtful": 0, "questionable": 0, "probable": 0}),
        "starter_rotation": unit_counts.get("starter_rotation", {"out": 0, "doubtful": 0, "questionable": 0, "probable": 0}),
        "bullpen": unit_counts.get("bullpen", {"out": 0, "doubtful": 0, "questionable": 0, "probable": 0}),
        "lineup_core": unit_counts.get("lineup_core", {"out": 0, "doubtful": 0, "questionable": 0, "probable": 0}),
        "top_lines": unit_counts.get("top_lines", {"out": 0, "doubtful": 0, "questionable": 0, "probable": 0}),
        "defense_pairs": unit_counts.get("defense_pairs", {"out": 0, "doubtful": 0, "questionable": 0, "probable": 0}),
        "goalie_status": unit_counts.get("goalie_status", {"out": 0, "doubtful": 0, "questionable": 0, "probable": 0}),
        "forward_line": unit_counts.get("forward_line", {"out": 0, "doubtful": 0, "questionable": 0, "probable": 0}),
        "midfield": unit_counts.get("midfield", {"out": 0, "doubtful": 0, "questionable": 0, "probable": 0}),
        "defense": unit_counts.get("defense", {"out": 0, "doubtful": 0, "questionable": 0, "probable": 0}),
        "goalkeeper": unit_counts.get("goalkeeper", {"out": 0, "doubtful": 0, "questionable": 0, "probable": 0}),
    }
    
    # Impact scores will be computed by injury_feature_builder
    impact_scores = {
        "offense_impact": 0.0,
        "defense_impact": 0.0,
        "overall_impact": 0.0,
        "uncertainty": 0.0,
    }
    
    # Trend will be computed by comparing with previous snapshot
    trend = "stable"
    
    # Last updated timestamp
    last_updated = raw_injuries.get("last_updated") or datetime.utcnow().isoformat()
    
    normalized = {
        "unit_counts": all_unit_counts,
        "impact_scores": impact_scores,
        "trend": trend,
        "last_updated": last_updated,
    }
    
    # Validate with Pydantic model
    try:
        canonical = CanonicalInjuries(**normalized)
        return canonical.dict(exclude_none=False)
    except Exception:
        # If validation fails, return normalized dict anyway (graceful degradation)
        return normalized
