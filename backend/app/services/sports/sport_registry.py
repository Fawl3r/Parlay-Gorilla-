"""Sport capabilities registry for stats platform v2.

Defines sport-specific capabilities including season modes, stat windows,
feature sets, injury support, and unit mappings.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from app.services.sports_config import SPORT_CONFIGS, get_sport_config


class SeasonMode(str, Enum):
    """Season mode for a sport at a given date."""
    IN_SEASON = "IN_SEASON"
    OFF_SEASON = "OFF_SEASON"


@dataclass(frozen=True)
class SportCapability:
    """Capabilities and configuration for a sport in the stats platform."""
    
    sport_slug: str
    sport_code: str
    stat_windows: List[str]  # e.g., ["last_3", "last_5", "last_10", "last_14d", "last_30d"]
    feature_sets: List[str]  # e.g., ["form", "strength", "tempo_volatility", "matchup_edges"]
    injury_supported: bool
    prop_supported: bool
    unit_mappings: Dict[str, List[str]]  # Sport-specific injury unit names
    
    def get_season_mode(self, date: datetime) -> SeasonMode:
        """Determine if sport is in season or off-season at given date."""
        return get_season_mode(self.sport_slug, date)
    
    def get_last_completed_season(self, date: datetime) -> Optional[str]:
        """Get last completed season year if off-season, None if in-season."""
        if self.get_season_mode(date) == SeasonMode.IN_SEASON:
            return None
        return get_last_completed_season(self.sport_slug, date)


# Sport capability definitions
SPORT_CAPABILITIES: Dict[str, SportCapability] = {
    "nfl": SportCapability(
        sport_slug="nfl",
        sport_code="NFL",
        stat_windows=["last_3", "last_5", "last_10", "last_14d", "last_30d"],
        feature_sets=["form", "strength", "tempo_volatility", "matchup_edges"],
        injury_supported=True,
        prop_supported=True,
        unit_mappings={
            "qb_room": ["qb", "quarterback"],
            "skill_positions": ["rb", "wr", "te", "running back", "wide receiver", "tight end"],
            "offensive_line": ["ol", "offensive line", "lineman"],
            "defensive_front": ["dl", "lb", "defensive line", "linebacker"],
            "secondary": ["cb", "s", "cornerback", "safety", "defensive back"],
        },
    ),
    "nba": SportCapability(
        sport_slug="nba",
        sport_code="NBA",
        stat_windows=["last_3", "last_5", "last_10", "last_14d", "last_30d"],
        feature_sets=["form", "strength", "tempo_volatility", "matchup_edges"],
        injury_supported=True,
        prop_supported=True,
        unit_mappings={
            "guard_rotation": ["pg", "sg", "point guard", "shooting guard"],
            "wing_rotation": ["sf", "small forward"],
            "big_rotation": ["pf", "c", "power forward", "center"],
        },
    ),
    "wnba": SportCapability(
        sport_slug="wnba",
        sport_code="WNBA",
        stat_windows=["last_3", "last_5", "last_10", "last_14d", "last_30d"],
        feature_sets=["form", "strength", "tempo_volatility", "matchup_edges"],
        injury_supported=True,
        prop_supported=False,
        unit_mappings={
            "guard_rotation": ["pg", "sg", "point guard", "shooting guard"],
            "wing_rotation": ["sf", "small forward"],
            "big_rotation": ["pf", "c", "power forward", "center"],
        },
    ),
    "nhl": SportCapability(
        sport_slug="nhl",
        sport_code="NHL",
        stat_windows=["last_3", "last_5", "last_10", "last_14d", "last_30d"],
        feature_sets=["form", "strength", "tempo_volatility", "matchup_edges"],
        injury_supported=True,
        prop_supported=True,
        unit_mappings={
            "top_lines": ["forward", "center", "winger"],
            "defense_pairs": ["defenseman", "defender"],
            "goalie_status": ["goalie", "goalkeeper"],
        },
    ),
    "mlb": SportCapability(
        sport_slug="mlb",
        sport_code="MLB",
        stat_windows=["last_3", "last_5", "last_10", "last_14d", "last_30d"],
        feature_sets=["form", "strength", "tempo_volatility", "matchup_edges"],
        injury_supported=True,  # Limited but normalize if present
        prop_supported=True,
        unit_mappings={
            "starter_rotation": ["sp", "starting pitcher"],
            "bullpen": ["rp", "relief pitcher", "closer"],
            "lineup_core": ["c", "1b", "2b", "3b", "ss", "of", "catcher", "infielder", "outfielder"],
        },
    ),
    "ncaaf": SportCapability(
        sport_slug="ncaaf",
        sport_code="NCAAF",
        stat_windows=["last_3", "last_5", "last_10", "last_14d", "last_30d"],
        feature_sets=["form", "strength", "tempo_volatility", "matchup_edges"],
        injury_supported=True,
        prop_supported=False,
        unit_mappings={
            "qb_room": ["qb", "quarterback"],
            "skill_positions": ["rb", "wr", "te", "running back", "wide receiver", "tight end"],
            "offensive_line": ["ol", "offensive line", "lineman"],
            "defensive_front": ["dl", "lb", "defensive line", "linebacker"],
            "secondary": ["cb", "s", "cornerback", "safety", "defensive back"],
        },
    ),
    "ncaab": SportCapability(
        sport_slug="ncaab",
        sport_code="NCAAB",
        stat_windows=["last_3", "last_5", "last_10", "last_14d", "last_30d"],
        feature_sets=["form", "strength", "tempo_volatility", "matchup_edges"],
        injury_supported=True,
        prop_supported=False,
        unit_mappings={
            "guard_rotation": ["pg", "sg", "point guard", "shooting guard"],
            "wing_rotation": ["sf", "small forward"],
            "big_rotation": ["pf", "c", "power forward", "center"],
        },
    ),
    "mls": SportCapability(
        sport_slug="mls",
        sport_code="MLS",
        stat_windows=["last_3", "last_5", "last_10", "last_14d", "last_30d"],
        feature_sets=["form", "strength", "tempo_volatility", "matchup_edges"],
        injury_supported=True,
        prop_supported=False,
        unit_mappings={
            "forward_line": ["forward", "striker"],
            "midfield": ["midfielder", "cm", "cam", "cdm"],
            "defense": ["defender", "cb", "fb", "center back", "fullback"],
            "goalkeeper": ["gk", "goalkeeper"],
        },
    ),
    "epl": SportCapability(
        sport_slug="epl",
        sport_code="EPL",
        stat_windows=["last_3", "last_5", "last_10", "last_14d", "last_30d"],
        feature_sets=["form", "strength", "tempo_volatility", "matchup_edges"],
        injury_supported=True,
        prop_supported=False,
        unit_mappings={
            "forward_line": ["forward", "striker"],
            "midfield": ["midfielder", "cm", "cam", "cdm"],
            "defense": ["defender", "cb", "fb", "center back", "fullback"],
            "goalkeeper": ["gk", "goalkeeper"],
        },
    ),
    "laliga": SportCapability(
        sport_slug="laliga",
        sport_code="LALIGA",
        stat_windows=["last_3", "last_5", "last_10", "last_14d", "last_30d"],
        feature_sets=["form", "strength", "tempo_volatility", "matchup_edges"],
        injury_supported=True,
        prop_supported=False,
        unit_mappings={
            "forward_line": ["forward", "striker"],
            "midfield": ["midfielder", "cm", "cam", "cdm"],
            "defense": ["defender", "cb", "fb", "center back", "fullback"],
            "goalkeeper": ["gk", "goalkeeper"],
        },
    ),
    "ucl": SportCapability(
        sport_slug="ucl",
        sport_code="UCL",
        stat_windows=["last_3", "last_5", "last_10", "last_14d", "last_30d"],
        feature_sets=["form", "strength", "tempo_volatility", "matchup_edges"],
        injury_supported=True,
        prop_supported=False,
        unit_mappings={
            "forward_line": ["forward", "striker"],
            "midfield": ["midfielder", "cm", "cam", "cdm"],
            "defense": ["defender", "cb", "fb", "center back", "fullback"],
            "goalkeeper": ["gk", "goalkeeper"],
        },
    ),
    "soccer": SportCapability(  # Legacy soccer
        sport_slug="soccer",
        sport_code="SOCCER",
        stat_windows=["last_3", "last_5", "last_10", "last_14d", "last_30d"],
        feature_sets=["form", "strength", "tempo_volatility", "matchup_edges"],
        injury_supported=True,
        prop_supported=False,
        unit_mappings={
            "forward_line": ["forward", "striker"],
            "midfield": ["midfielder", "cm", "cam", "cdm"],
            "defense": ["defender", "cb", "fb", "center back", "fullback"],
            "goalkeeper": ["gk", "goalkeeper"],
        },
    ),
    "ufc": SportCapability(
        sport_slug="ufc",
        sport_code="UFC",
        stat_windows=["last_3", "last_5", "last_10"],
        feature_sets=["form", "strength"],  # Limited features for combat sports
        injury_supported=False,  # Injuries not typically tracked pre-fight
        prop_supported=False,
        unit_mappings={},
    ),
    "boxing": SportCapability(
        sport_slug="boxing",
        sport_code="BOXING",
        stat_windows=["last_3", "last_5", "last_10"],
        feature_sets=["form", "strength"],  # Limited features for combat sports
        injury_supported=False,  # Injuries not typically tracked pre-fight
        prop_supported=False,
        unit_mappings={},
    ),
}


def get_sport_capability(sport_identifier: str) -> SportCapability:
    """Get sport capability by identifier (slug, code, or alias)."""
    try:
        sport_config = get_sport_config(sport_identifier)
        capability = SPORT_CAPABILITIES.get(sport_config.slug)
        if not capability:
            # Fallback to default capability if not found
            return _default_capability(sport_config.slug, sport_config.code)
        return capability
    except ValueError:
        # If sport not found, return default
        slug = sport_identifier.lower()
        return _default_capability(slug, slug.upper())


def _default_capability(slug: str, code: str) -> SportCapability:
    """Create a default capability for unknown sports."""
    return SportCapability(
        sport_slug=slug,
        sport_code=code,
        stat_windows=["last_3", "last_5", "last_10"],
        feature_sets=["form", "strength"],
        injury_supported=False,
        prop_supported=False,
        unit_mappings={},
    )


def get_season_mode(sport: str, date: datetime) -> SeasonMode:
    """Determine if a sport is in season or off-season at a given date.
    
    Always returns a valid mode, never errors. Uses conservative estimates
    for season calendars.
    """
    sport_lower = sport.lower()
    month = date.month
    
    # MLB: Typically March-October in season, Nov-Feb off-season
    if sport_lower in ["mlb", "baseball"]:
        if month in [11, 12, 1, 2]:
            return SeasonMode.OFF_SEASON
        return SeasonMode.IN_SEASON
    
    # NFL: Typically September-February in season
    if sport_lower in ["nfl", "americanfootball_nfl"]:
        if month in [3, 4, 5, 6, 7, 8]:
            return SeasonMode.OFF_SEASON
        return SeasonMode.IN_SEASON
    
    # NBA: Typically October-June in season
    if sport_lower in ["nba", "basketball_nba"]:
        if month in [7, 8, 9]:
            return SeasonMode.OFF_SEASON
        return SeasonMode.IN_SEASON

    # WNBA: Typically May-September in season
    if sport_lower in ["wnba", "basketball_wnba"]:
        if month in [10, 11, 12, 1, 2, 3, 4]:
            return SeasonMode.OFF_SEASON
        return SeasonMode.IN_SEASON

    # NHL: Typically October-June in season
    if sport_lower in ["nhl", "icehockey_nhl", "hockey"]:
        if month in [7, 8, 9]:
            return SeasonMode.OFF_SEASON
        return SeasonMode.IN_SEASON
    
    # NCAAF: Typically August-January in season
    if sport_lower in ["ncaaf", "americanfootball_ncaaf", "cfb", "college football"]:
        if month in [2, 3, 4, 5, 6, 7]:
            return SeasonMode.OFF_SEASON
        return SeasonMode.IN_SEASON
    
    # NCAAB: Typically November-March in season
    if sport_lower in ["ncaab", "basketball_ncaab", "cbb", "college basketball"]:
        if month in [4, 5, 6, 7, 8, 9, 10]:
            return SeasonMode.OFF_SEASON
        return SeasonMode.IN_SEASON
    
    # Soccer leagues: Year-round with breaks, assume in-season most of the time
    if sport_lower in ["mls", "epl", "laliga", "ucl", "soccer"]:
        # Most soccer leagues run August-May, with summer breaks
        if month in [6, 7]:
            return SeasonMode.OFF_SEASON
        return SeasonMode.IN_SEASON
    
    # UFC/Boxing: Year-round, always "in season" (events happen throughout year)
    if sport_lower in ["ufc", "mma", "boxing"]:
        return SeasonMode.IN_SEASON
    
    # Default: Assume in-season (conservative)
    return SeasonMode.IN_SEASON


def get_last_completed_season(sport: str, date: datetime) -> Optional[str]:
    """Get the last completed season year for a sport.
    
    Returns None if currently in-season, or the year string of the last
    completed season if off-season.
    """
    mode = get_season_mode(sport, date)
    if mode == SeasonMode.IN_SEASON:
        return None
    
    sport_lower = sport.lower()
    current_year = date.year
    month = date.month
    
    # MLB: Season ends in October, so if we're in Nov-Feb, last season was current year
    # If we're in March, might be last year's season
    if sport_lower in ["mlb", "baseball"]:
        if month in [11, 12]:
            return str(current_year)
        elif month in [1, 2]:
            return str(current_year - 1)
        elif month == 3:
            # Early March might still be off-season
            return str(current_year - 1)
        return None
    
    # NFL: Season ends in February, so if we're in Mar-Aug, last season was previous year
    if sport_lower in ["nfl", "americanfootball_nfl"]:
        if month in [3, 4, 5, 6, 7, 8]:
            if month <= 2:
                return str(current_year - 1)
            return str(current_year - 1)
        return None
    
    # NBA/NHL: Season ends in June, so if we're in Jul-Sep, last season was current year
    if sport_lower in ["nba", "basketball_nba", "nhl", "icehockey_nhl", "hockey"]:
        if month in [7, 8, 9]:
            return str(current_year)
        return None

    # WNBA: Season ends in September, so if we're in Oct-Apr, last season was current year (or year-1 for Jan-Apr)
    if sport_lower in ["wnba", "basketball_wnba"]:
        if month in [10, 11, 12]:
            return str(current_year)
        if month in [1, 2, 3, 4]:
            return str(current_year - 1)
        return None

    # NCAAF: Season ends in January, so if we're in Feb-Jul, last season was previous year
    if sport_lower in ["ncaaf", "americanfootball_ncaaf", "cfb", "college football"]:
        if month in [2, 3, 4, 5, 6, 7]:
            return str(current_year - 1)
        return None
    
    # NCAAB: Season ends in March/April, so if we're in Apr-Oct, last season was current year
    if sport_lower in ["ncaab", "basketball_ncaab", "cbb", "college basketball"]:
        if month in [4, 5, 6, 7, 8, 9, 10]:
            return str(current_year)
        return None
    
    # Soccer: Season typically ends in May, so if we're in Jun-Jul, last season was current year
    if sport_lower in ["mls", "epl", "laliga", "ucl", "soccer"]:
        if month in [6, 7]:
            return str(current_year)
        return None
    
    # Default: Return previous year as conservative estimate
    return str(current_year - 1)
