"""
Normalized API-Sports enrichment schema (single contract for all sports).

Returned as GameAnalysisResponse.enrichment. Supports standings, team stats,
recent form, injuries summary (counts only), and data_quality.
Spec-aligned: StandingsSummary, EnrichmentTeamSide, key_team_stats, as_of.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class InjuryStatusCount(BaseModel):
    """Injuries summary: status and count only (no player names)."""
    status: str  # e.g. "out", "questionable", "doubtful", "probable"
    count: int = 0


class StandingsSummary(BaseModel):
    """Standings slice for one team (rank, record, points, conference/division)."""
    rank: Optional[int] = None
    record: Optional[str] = None  # "W-L" or "W-D-L"
    points: Optional[int] = None  # soccer
    conference: Optional[str] = None
    division: Optional[str] = None


class KeyTeamStatRow(BaseModel):
    """One row of key team stats table (home vs away)."""
    key: str = ""
    label: str = ""
    home_value: Optional[Union[str, int, float]] = None
    away_value: Optional[Union[str, int, float]] = None


class EnrichmentTeamSide(BaseModel):
    """One side (home or away) in the enrichment payload (spec name)."""
    team_name: str = ""
    apisports_team_id: Optional[int] = None
    standings: Optional[StandingsSummary] = None
    recent_form: Optional[List[str]] = None  # ["W","L","W","W","L"]
    injuries_summary: Optional[List[InjuryStatusCount]] = None


class TeamEnrichmentSchema(BaseModel):
    """Internal team block used when building enrichment (record/rank/team_stats)."""
    name: str = ""
    apisports_team_id: Optional[int] = None
    record: Optional[str] = None
    standings_rank: Optional[int] = None
    conference_division: Optional[str] = None
    points: Optional[int] = None
    recent_form: List[str] = Field(default_factory=list)
    team_stats: Dict[str, Any] = Field(default_factory=dict)
    injuries_summary: List[InjuryStatusCount] = Field(default_factory=list)


class DataQualitySchema(BaseModel):
    """What enrichment data is present and any notes."""
    has_standings: bool = False
    has_team_stats: bool = False
    has_form: bool = False
    has_injuries: bool = False
    notes: List[str] = Field(default_factory=list)
    source_timestamps: Dict[str, Optional[str]] = Field(default_factory=dict)


class EnrichmentIdsSchema(BaseModel):
    """IDs used for this enrichment (for debugging/audit)."""
    apisports_league_id: Optional[int] = None
    season: Optional[str] = None
    home_team_id: Optional[int] = None
    away_team_id: Optional[int] = None


class EnrichmentPayloadSchema(BaseModel):
    """Normalized enrichment for a game (single contract for all sports)."""
    sport: str = ""
    league: str = ""
    season: str = ""
    league_id: Optional[int] = None
    home_team: TeamEnrichmentSchema = Field(default_factory=TeamEnrichmentSchema)
    away_team: TeamEnrichmentSchema = Field(default_factory=TeamEnrichmentSchema)
    key_team_stats: List[KeyTeamStatRow] = Field(default_factory=list)
    data_quality: DataQualitySchema = Field(default_factory=DataQualitySchema)
    ids: Optional[EnrichmentIdsSchema] = None
    as_of: Optional[datetime] = None

    class Config:
        extra = "allow"
