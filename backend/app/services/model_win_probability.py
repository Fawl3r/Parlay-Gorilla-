"""
Model Win Probability Calculator

Calculates win probabilities for matchups using a weighted combination of:
- Market odds (implied probabilities) - 50% weight
- Team statistics and performance metrics - 30% weight  
- Situational factors (rest, travel, weather, injuries) - 20% weight

Confidence score is based on both data quality (0-50 pts) and model edge (0-50 pts).
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.probability_engine import get_probability_engine, BaseProbabilityEngine


# Weight constants for probability calculation
ODDS_WEIGHT = 0.50      # 50% weight for market-implied probability
STATS_WEIGHT = 0.30     # 30% weight for team statistics
SITUATIONAL_WEIGHT = 0.20  # 20% weight for situational factors

# Sport-specific home advantage adjustments
HOME_ADVANTAGE = {
    "NFL": 0.025,       # 2.5% home field advantage
    "NBA": 0.035,       # 3.5% home court advantage
    "NHL": 0.025,       # 2.5% home ice advantage
    "MLB": 0.020,       # 2.0% home field advantage
    "SOCCER": 0.030,    # 3.0% home field advantage
    "SOCCER_EPL": 0.030,
    "SOCCER_USA_MLS": 0.025,
    "AMERICANFOOTBALL_NFL": 0.025,
    "BASKETBALL_NBA": 0.035,
    "ICEHOCKEY_NHL": 0.025,
    "BASEBALL_MLB": 0.020,
}

# Sport-specific stat weights for probability adjustments
# Each sport has different factors that influence outcomes
SPORT_STAT_WEIGHTS = {
    "NFL": {
        "win_pct": 0.20,        # Season win percentage
        "ppg_diff": 0.05,       # Points scored vs allowed
        "recent_form": 0.06,    # Last 5 games
        "weather_impact": 0.03, # Weather affects outdoor play
        "rest_impact": 0.01,    # Rest days matter
    },
    "NBA": {
        "win_pct": 0.18,        # Season win percentage
        "ppg_diff": 0.06,       # Points matter more in high-scoring
        "recent_form": 0.08,    # Recent form very important (82 game season)
        "pace": 0.03,           # Pace affects scoring
        "rest_impact": 0.02,    # Back-to-backs are significant
    },
    "NHL": {
        "win_pct": 0.15,        # Lower weight due to parity
        "ppg_diff": 0.04,       # Goal differential
        "recent_form": 0.07,    # Recent form important
        "special_teams": 0.05,  # Power play/penalty kill
        "goalie": 0.04,         # Goaltender performance
    },
    "MLB": {
        "win_pct": 0.12,        # Lower weight (variance in baseball)
        "run_diff": 0.04,       # Run differential
        "recent_form": 0.05,    # Recent form
        "starting_pitcher": 0.08,  # Starter is crucial
        "bullpen": 0.04,        # Bullpen strength
    },
    "SOCCER": {
        "win_pct": 0.15,        # Points per game more common
        "goal_diff": 0.05,      # Goal differential
        "recent_form": 0.08,    # Very important in soccer
        "xg": 0.04,             # Expected goals
        "home_form": 0.03,      # Home vs away form
    },
}


@dataclass
class TeamMatchupStats:
    """
    Structured container for team matchup statistics.
    All fields are optional to support graceful degradation.
    """
    home_team_stats: Optional[Dict] = None
    away_team_stats: Optional[Dict] = None
    home_injuries: Optional[Dict] = None
    away_injuries: Optional[Dict] = None
    weather: Optional[Dict] = None
    rest_days_home: Optional[int] = None
    rest_days_away: Optional[int] = None
    travel_distance: Optional[float] = None
    is_divisional: Optional[bool] = None
    head_to_head: Optional[Dict] = None
    home_team_name: str = ""
    away_team_name: str = ""
    sport: str = "NFL"
    
    @classmethod
    def from_matchup_data(cls, matchup_data: Dict, home_team: str, away_team: str, sport: str = "NFL") -> "TeamMatchupStats":
        """Create TeamMatchupStats from matchup_data dictionary"""
        return cls(
            home_team_stats=matchup_data.get("home_team_stats"),
            away_team_stats=matchup_data.get("away_team_stats"),
            home_injuries=matchup_data.get("home_injuries"),
            away_injuries=matchup_data.get("away_injuries"),
            weather=matchup_data.get("weather"),
            rest_days_home=matchup_data.get("rest_days_home"),
            rest_days_away=matchup_data.get("rest_days_away"),
            travel_distance=matchup_data.get("travel_distance"),
            is_divisional=matchup_data.get("is_divisional"),
            head_to_head=matchup_data.get("head_to_head"),
            home_team_name=home_team,
            away_team_name=away_team,
            sport=sport.upper(),
        )


class ModelWinProbabilityCalculator:
    """
    Calculates model win probabilities using a weighted combination of factors.
    
    Weighting:
    - Market odds (implied probabilities): 50%
    - Team statistics and performance: 30%
    - Situational factors: 20%
    
    Confidence is calculated from:
    - Data quality (0-50 points): How much data is available
    - Model edge (0-50 points): How much model differs from market
    """
    
    def __init__(self, db: AsyncSession, sport: str = "NFL"):
        self.db = db
        self.sport = sport.upper()
        self.prob_engine: BaseProbabilityEngine = get_probability_engine(db, sport)
    
    async def compute_model_win_probabilities(
        self,
        base: Dict[str, float],
        stats: TeamMatchupStats,
        odds_data: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Compute model win probabilities with weighted factors.
        
        Args:
            base: {home_fair_prob, away_fair_prob} - vig-removed implied probs
            stats: TeamMatchupStats containing all matchup data
            odds_data: Raw odds data for additional context
        
        Returns:
            {
                home_model_prob: float (0-1),
                away_model_prob: float (0-1),
                ai_confidence: float (0-100),
                calculation_method: str,
                data_quality_score: float (0-50),
                model_edge_score: float (0-50),
                adjustments_applied: Dict
            }
        """
        home_fair_prob = base.get("home_fair_prob", 0.5)
        away_fair_prob = base.get("away_fair_prob", 0.5)
        
        # Track which adjustments were applied
        adjustments_applied = {}
        data_sources_used = []
        
        # 1. Calculate stats-based probability adjustment (30% weight)
        stats_adjustment = await self._calculate_stats_adjustment(stats)
        adjustments_applied["stats"] = stats_adjustment
        if stats.home_team_stats or stats.away_team_stats:
            data_sources_used.append("team_stats")
        
        # 2. Calculate situational adjustment (20% weight)
        situational_adjustment = await self._calculate_situational_adjustment(stats)
        adjustments_applied["situational"] = situational_adjustment
        if stats.weather or stats.rest_days_home is not None or stats.home_injuries:
            data_sources_used.append("situational")
        
        # 3. Add sport-specific home advantage
        home_advantage = self._get_home_advantage(stats.sport)
        adjustments_applied["home_advantage"] = home_advantage
        
        # 4. Combine with weights
        # The weighted combination ensures:
        # - Odds provide 50% of the signal
        # - Stats provide 30% of the signal  
        # - Situational factors provide 20% of the signal
        
        # Base probability from odds (50% weight)
        odds_component = home_fair_prob * ODDS_WEIGHT
        
        # Stats component (30% weight) - use fair prob as base, add adjustment
        # The adjustment itself already accounts for the stat differences
        stats_base = home_fair_prob + stats_adjustment
        stats_component = stats_base * STATS_WEIGHT
        
        # Situational component (20% weight)
        # Home advantage is a baseline situational factor
        situational_base = home_fair_prob + situational_adjustment + home_advantage
        situational_component = situational_base * SITUATIONAL_WEIGHT
        
        # Final home model probability
        home_model_prob = odds_component + stats_component + situational_component
        
        # Also add a direct adjustment for extreme stat differences
        # This ensures dominant teams are properly reflected
        total_adjustment = stats_adjustment + situational_adjustment + home_advantage
        home_model_prob += total_adjustment * 0.3  # Additional direct impact
        
        # Normalize to ensure probabilities sum to 1
        home_model_prob = max(0.08, min(0.92, home_model_prob))  # Keep within reasonable bounds
        away_model_prob = 1.0 - home_model_prob
        
        # 5. Calculate confidence score
        data_quality_score = self._calculate_data_quality_score(stats, odds_data, data_sources_used)
        model_edge = abs(home_model_prob - home_fair_prob)
        model_edge_score = self._calculate_model_edge_score(model_edge)
        ai_confidence = data_quality_score + model_edge_score
        
        # Determine calculation method
        if odds_data and (odds_data.get("home_ml") or odds_data.get("home_implied_prob")):
            if stats.home_team_stats or stats.away_team_stats:
                calculation_method = "odds_and_stats"
            else:
                calculation_method = "odds_only"
        elif stats.home_team_stats or stats.away_team_stats:
            calculation_method = "stats_only"
        else:
            calculation_method = "minimal_data"
        
        return {
            "home_model_prob": round(home_model_prob, 4),
            "away_model_prob": round(away_model_prob, 4),
            "ai_confidence": round(ai_confidence, 1),
            "calculation_method": calculation_method,
            "data_quality_score": round(data_quality_score, 1),
            "model_edge_score": round(model_edge_score, 1),
            "adjustments_applied": adjustments_applied,
            "data_sources_used": data_sources_used,
        }
    
    async def _calculate_stats_adjustment(self, stats: TeamMatchupStats) -> float:
        """
        Calculate probability adjustment based on team statistics.
        
        Returns adjustment in range [-0.15, +0.15] for home team.
        Positive = favors home, negative = favors away.
        
        Uses sport-specific weights and factors.
        """
        if not stats.home_team_stats and not stats.away_team_stats:
            return 0.0
        
        # Get sport-specific weights
        sport_weights = SPORT_STAT_WEIGHTS.get(stats.sport.upper(), SPORT_STAT_WEIGHTS["NFL"])
        
        adjustment = 0.0
        
        # Win percentage comparison (all sports)
        home_win_pct = self._extract_win_pct(stats.home_team_stats)
        away_win_pct = self._extract_win_pct(stats.away_team_stats)
        
        if home_win_pct is not None and away_win_pct is not None:
            win_pct_diff = home_win_pct - away_win_pct
            weight = sport_weights.get("win_pct", 0.20)
            adjustment += win_pct_diff * weight
        
        # Points/goals per game differential
        home_ppg = self._extract_ppg(stats.home_team_stats)
        away_ppg = self._extract_ppg(stats.away_team_stats)
        home_papg = self._extract_papg(stats.home_team_stats)
        away_papg = self._extract_papg(stats.away_team_stats)
        
        if all(v is not None for v in [home_ppg, away_ppg, home_papg, away_papg]):
            home_net = home_ppg - home_papg
            away_net = away_ppg - away_papg
            net_diff = home_net - away_net
            weight = sport_weights.get("ppg_diff", 0.05)
            # Normalize by sport (NFL ~7 ppg diff, NBA ~10, NHL ~0.5)
            normalizer = 10.0 if stats.sport in ["NBA", "BASKETBALL_NBA"] else (0.5 if stats.sport in ["NHL", "ICEHOCKEY_NHL"] else 7.0)
            adjustment += (net_diff / normalizer) * weight
        
        # Recent form (last 5 games)
        home_recent = self._extract_recent_form(stats.home_team_stats)
        away_recent = self._extract_recent_form(stats.away_team_stats)
        
        if home_recent is not None and away_recent is not None:
            form_diff = home_recent - away_recent
            weight = sport_weights.get("recent_form", 0.06)
            adjustment += form_diff * weight
        
        # Sport-specific adjustments
        sport_adj = self._apply_sport_specific_stats(stats)
        adjustment += sport_adj
        
        # Clamp adjustment to reasonable range
        return max(-0.15, min(0.15, adjustment))
    
    def _apply_sport_specific_stats(self, stats: TeamMatchupStats) -> float:
        """Apply sport-specific statistical adjustments."""
        sport = stats.sport.upper()
        adjustment = 0.0
        
        if sport in ["NBA", "BASKETBALL_NBA"]:
            adjustment += self._nba_specific_adjustment(stats)
        elif sport in ["NHL", "ICEHOCKEY_NHL"]:
            adjustment += self._nhl_specific_adjustment(stats)
        elif sport in ["MLB", "BASEBALL_MLB"]:
            adjustment += self._mlb_specific_adjustment(stats)
        elif "SOCCER" in sport:
            adjustment += self._soccer_specific_adjustment(stats)
        # NFL uses base adjustments
        
        return adjustment
    
    def _nba_specific_adjustment(self, stats: TeamMatchupStats) -> float:
        """NBA-specific adjustments: pace, offensive/defensive rating."""
        adjustment = 0.0
        
        home_stats = stats.home_team_stats or {}
        away_stats = stats.away_team_stats or {}
        
        # Pace comparison (affects totals more, but also win prob)
        home_pace = home_stats.get("pace", home_stats.get("possessions_per_game"))
        away_pace = away_stats.get("pace", away_stats.get("possessions_per_game"))
        
        if home_pace and away_pace:
            # Higher pace teams may have slight advantage at home
            pace_diff = (home_pace - away_pace) / 100.0
            adjustment += pace_diff * 0.01
        
        # Offensive rating vs defensive rating matchup
        home_off_rtg = home_stats.get("offensive_rating", home_stats.get("off_rating"))
        away_def_rtg = away_stats.get("defensive_rating", away_stats.get("def_rating"))
        
        if home_off_rtg and away_def_rtg:
            matchup_edge = (home_off_rtg - away_def_rtg) / 100.0
            adjustment += matchup_edge * 0.02
        
        return adjustment
    
    def _nhl_specific_adjustment(self, stats: TeamMatchupStats) -> float:
        """NHL-specific adjustments: special teams, goaltending."""
        adjustment = 0.0
        
        home_stats = stats.home_team_stats or {}
        away_stats = stats.away_team_stats or {}
        
        # Power play vs penalty kill
        home_pp = home_stats.get("power_play_pct", home_stats.get("pp_pct", 20))
        away_pk = away_stats.get("penalty_kill_pct", away_stats.get("pk_pct", 80))
        
        if home_pp and away_pk:
            # PP vs PK matchup
            special_teams_edge = (home_pp - (100 - away_pk)) / 100.0
            adjustment += special_teams_edge * 0.02
        
        # Goals for vs goals against
        home_gf = home_stats.get("goals_for", home_stats.get("goals_per_game", 3.0))
        away_ga = away_stats.get("goals_against", away_stats.get("goals_allowed_per_game", 2.8))
        
        if home_gf and away_ga:
            goal_edge = (home_gf - away_ga) * 0.02
            adjustment += goal_edge
        
        return adjustment
    
    def _mlb_specific_adjustment(self, stats: TeamMatchupStats) -> float:
        """MLB-specific adjustments: run differential, bullpen."""
        adjustment = 0.0
        
        home_stats = stats.home_team_stats or {}
        away_stats = stats.away_team_stats or {}
        
        # Run differential
        home_runs = home_stats.get("runs_per_game", home_stats.get("runs_scored_per_game"))
        home_runs_allowed = home_stats.get("runs_allowed_per_game")
        away_runs = away_stats.get("runs_per_game", away_stats.get("runs_scored_per_game"))
        away_runs_allowed = away_stats.get("runs_allowed_per_game")
        
        if all([home_runs, home_runs_allowed, away_runs, away_runs_allowed]):
            home_diff = home_runs - home_runs_allowed
            away_diff = away_runs - away_runs_allowed
            run_edge = (home_diff - away_diff) * 0.01
            adjustment += run_edge
        
        # ERA comparison (lower is better)
        home_era = home_stats.get("era", home_stats.get("team_era"))
        away_era = away_stats.get("era", away_stats.get("team_era"))
        
        if home_era and away_era:
            era_edge = (away_era - home_era) * 0.01  # Lower ERA is better
            adjustment += era_edge
        
        return adjustment
    
    def _soccer_specific_adjustment(self, stats: TeamMatchupStats) -> float:
        """Soccer-specific adjustments: xG, possession, form."""
        adjustment = 0.0
        
        home_stats = stats.home_team_stats or {}
        away_stats = stats.away_team_stats or {}
        
        # Expected goals (xG)
        home_xg = home_stats.get("xg", home_stats.get("expected_goals"))
        away_xg = away_stats.get("xg", away_stats.get("expected_goals"))
        
        if home_xg and away_xg:
            xg_edge = (home_xg - away_xg) * 0.02
            adjustment += xg_edge
        
        # Points per game
        home_ppg = home_stats.get("points_per_game")
        away_ppg = away_stats.get("points_per_game")
        
        if home_ppg and away_ppg:
            ppg_edge = (home_ppg - away_ppg) / 3.0 * 0.05  # 3 points max per game
            adjustment += ppg_edge
        
        # Home vs away form
        home_home_form = home_stats.get("home_win_pct", home_stats.get("home_form"))
        away_away_form = away_stats.get("away_win_pct", away_stats.get("away_form"))
        
        if home_home_form and away_away_form:
            form_edge = (home_home_form - away_away_form) * 0.03
            adjustment += form_edge
        
        return adjustment
    
    async def _calculate_situational_adjustment(self, stats: TeamMatchupStats) -> float:
        """
        Calculate probability adjustment based on situational factors.
        
        Returns adjustment in range [-0.10, +0.10] for home team.
        """
        adjustment = 0.0
        
        # Rest advantage
        if stats.rest_days_home is not None and stats.rest_days_away is not None:
            rest_diff = stats.rest_days_home - stats.rest_days_away
            # Each extra rest day = ~0.5% advantage
            adjustment += rest_diff * 0.005
        
        # Travel fatigue (away team disadvantage)
        if stats.travel_distance is not None:
            # Long travel (>1000 miles) = 1% away team disadvantage
            if stats.travel_distance > 1000:
                adjustment += 0.01
            elif stats.travel_distance > 2000:
                adjustment += 0.015
        
        # Divisional games tend to be closer
        if stats.is_divisional:
            # Reduce home advantage slightly for divisional games
            adjustment -= 0.005
        
        # Weather impact (favors home team in bad weather)
        if stats.weather:
            weather_adjustment = self._calculate_weather_adjustment(stats.weather)
            adjustment += weather_adjustment
        
        # Injury impact
        if stats.home_injuries or stats.away_injuries:
            injury_adjustment = self._calculate_injury_adjustment(
                stats.home_injuries, stats.away_injuries
            )
            adjustment += injury_adjustment
        
        # Clamp adjustment to reasonable range
        return max(-0.10, min(0.10, adjustment))
    
    def _calculate_weather_adjustment(self, weather: Dict) -> float:
        """Calculate adjustment based on weather conditions."""
        if not weather:
            return 0.0
        
        # Indoor games aren't affected
        if not weather.get("is_outdoor", True):
            return 0.0
        
        if not weather.get("affects_game", False):
            return 0.0
        
        adjustment = 0.0
        
        # Extreme cold
        temp = weather.get("temperature")
        if temp is not None and temp < 32:
            adjustment += 0.01  # Home team advantage in cold
        
        # High wind
        wind = weather.get("wind_speed", 0)
        if wind > 20:
            adjustment += 0.01  # Affects passing game, home team adjusts better
        
        # Rain/snow
        precipitation = weather.get("precipitation", 0)
        if precipitation > 0:
            adjustment += 0.01  # Home team advantage in precipitation
        
        return min(0.03, adjustment)  # Cap weather adjustment
    
    def _calculate_injury_adjustment(
        self, 
        home_injuries: Optional[Dict], 
        away_injuries: Optional[Dict]
    ) -> float:
        """Calculate adjustment based on key player injuries."""
        adjustment = 0.0
        
        # Home team injuries (reduce home probability)
        if home_injuries:
            impact = home_injuries.get("impact_score", 0)
            # High impact injuries reduce home win probability
            adjustment -= impact * 0.02
            
            # Count key players out
            key_out = len(home_injuries.get("key_players_out", []))
            adjustment -= key_out * 0.01
        
        # Away team injuries (increase home probability)
        if away_injuries:
            impact = away_injuries.get("impact_score", 0)
            adjustment += impact * 0.02
            
            key_out = len(away_injuries.get("key_players_out", []))
            adjustment += key_out * 0.01
        
        return max(-0.08, min(0.08, adjustment))
    
    def _get_home_advantage(self, sport: str) -> float:
        """Get sport-specific home advantage."""
        return HOME_ADVANTAGE.get(sport.upper(), 0.025)
    
    def _calculate_data_quality_score(
        self, 
        stats: TeamMatchupStats, 
        odds_data: Optional[Dict],
        data_sources_used: list
    ) -> float:
        """
        Calculate data quality score (0-50 points).
        
        More data sources = higher quality score.
        """
        score = 0.0
        
        # Odds data available (15 points)
        if odds_data:
            if odds_data.get("home_implied_prob") or odds_data.get("home_ml"):
                score += 15
        
        # Team stats available (10 points each)
        if stats.home_team_stats:
            score += 10
        if stats.away_team_stats:
            score += 10
        
        # Weather data (5 points)
        if stats.weather:
            score += 5
        
        # Injury data (5 points each)
        if stats.home_injuries:
            score += 2.5
        if stats.away_injuries:
            score += 2.5
        
        # Rest/travel data (5 points)
        if stats.rest_days_home is not None or stats.rest_days_away is not None:
            score += 2.5
        if stats.travel_distance is not None:
            score += 2.5
        
        return min(50, score)
    
    def _calculate_model_edge_score(self, edge: float) -> float:
        """
        Calculate model edge score (0-50 points).
        
        Larger edge = higher confidence that model found value.
        But extremely large edges may indicate data issues.
        """
        # Edge of 0.05 (5%) = 25 points
        # Edge of 0.10 (10%) = 50 points
        # Edge > 0.15 starts to decrease (possible data issue)
        
        if edge <= 0.10:
            # Linear scaling up to 10% edge
            score = edge * 500  # 0.10 * 500 = 50
        else:
            # Diminishing returns / skepticism for large edges
            score = 50 - ((edge - 0.10) * 100)
        
        return max(10, min(50, score))  # Minimum 10 for having any model
    
    # Helper methods for extracting stats
    def _extract_win_pct(self, team_stats: Optional[Dict]) -> Optional[float]:
        """Extract win percentage from team stats."""
        if not team_stats:
            return None
        
        # Try direct win_percentage field
        if "win_percentage" in team_stats:
            return team_stats["win_percentage"]
        
        # Try record.win_percentage
        record = team_stats.get("record", {})
        if "win_percentage" in record:
            return record["win_percentage"]
        
        # Calculate from wins/losses
        wins = record.get("wins", team_stats.get("wins", 0))
        losses = record.get("losses", team_stats.get("losses", 0))
        total = wins + losses
        
        if total > 0:
            return wins / total
        
        return None
    
    def _extract_ppg(self, team_stats: Optional[Dict]) -> Optional[float]:
        """Extract points per game."""
        if not team_stats:
            return None
        
        # Try direct field
        if "points_per_game" in team_stats:
            return team_stats["points_per_game"]
        
        # Try offense object
        offense = team_stats.get("offense", {})
        if "points_per_game" in offense:
            return offense["points_per_game"]
        
        return None
    
    def _extract_papg(self, team_stats: Optional[Dict]) -> Optional[float]:
        """Extract points allowed per game."""
        if not team_stats:
            return None
        
        # Try direct field
        if "points_allowed_per_game" in team_stats:
            return team_stats["points_allowed_per_game"]
        
        # Try defense object
        defense = team_stats.get("defense", {})
        if "points_allowed_per_game" in defense:
            return defense["points_allowed_per_game"]
        
        return None
    
    def _extract_recent_form(self, team_stats: Optional[Dict]) -> Optional[float]:
        """Extract recent form (win pct in last 5 games)."""
        if not team_stats:
            return None
        
        # Try recent_wins/recent_losses
        recent_wins = team_stats.get("recent_wins")
        recent_losses = team_stats.get("recent_losses")
        
        if recent_wins is not None and recent_losses is not None:
            total = recent_wins + recent_losses
            if total > 0:
                return recent_wins / total
        
        return None


def american_odds_to_probability(american_odds: int) -> float:
    """Convert American odds to implied probability."""
    if american_odds > 0:
        return 100 / (american_odds + 100)
    else:
        return abs(american_odds) / (abs(american_odds) + 100)


def remove_vig_and_normalize(home_prob: float, away_prob: float) -> tuple[float, float]:
    """
    Remove the vig from bookmaker probabilities and normalize to sum to 1.
    
    Args:
        home_prob: Raw implied probability for home team
        away_prob: Raw implied probability for away team
    
    Returns:
        (home_fair_prob, away_fair_prob) that sum to 1.0
    """
    total = home_prob + away_prob
    if total <= 0:
        return 0.5, 0.5
    
    home_fair = home_prob / total
    away_fair = away_prob / total
    
    return home_fair, away_fair


def calculate_fair_probabilities_from_odds(odds_data: Dict) -> tuple[float, float]:
    """
    Calculate fair (vig-removed) probabilities from odds data.
    
    Returns (home_fair_prob, away_fair_prob).
    """
    # Method 1: Use pre-calculated implied probabilities
    home_implied = odds_data.get("home_implied_prob")
    away_implied = odds_data.get("away_implied_prob")
    
    if home_implied and away_implied and home_implied > 0 and away_implied > 0:
        return remove_vig_and_normalize(home_implied, away_implied)
    
    # Method 2: Calculate from moneyline odds
    home_ml = odds_data.get("home_ml")
    away_ml = odds_data.get("away_ml")
    
    if home_ml and away_ml:
        try:
            # Parse odds if string
            if isinstance(home_ml, str):
                home_ml = int(home_ml.replace("+", ""))
            if isinstance(away_ml, str):
                away_ml = int(away_ml.replace("+", ""))
            
            home_prob = american_odds_to_probability(home_ml)
            away_prob = american_odds_to_probability(away_ml)
            
            return remove_vig_and_normalize(home_prob, away_prob)
        except (ValueError, TypeError):
            pass
    
    # Fallback
    return 0.5, 0.5


async def compute_game_win_probability(
    db: AsyncSession,
    home_team: str,
    away_team: str,
    sport: str,
    matchup_data: Dict,
    odds_data: Optional[Dict] = None,
) -> Dict[str, Any]:
    """
    Convenience function to compute win probabilities for a game.
    
    This is the main entry point for calculating model win probabilities.
    """
    # Calculate fair probabilities from odds
    if odds_data:
        home_fair_prob, away_fair_prob = calculate_fair_probabilities_from_odds(odds_data)
        # If odds calculation returned 0.5/0.5 (no valid odds), we'll still apply adjustments
    else:
        # No odds data - start with 0.5/0.5 but adjustments will be applied
        home_fair_prob, away_fair_prob = 0.5, 0.5
    
    # Build TeamMatchupStats from matchup_data
    stats = TeamMatchupStats.from_matchup_data(
        matchup_data=matchup_data,
        home_team=home_team,
        away_team=away_team,
        sport=sport,
    )
    
    # Calculate model probabilities
    calculator = ModelWinProbabilityCalculator(db, sport)
    result = await calculator.compute_model_win_probabilities(
        base={"home_fair_prob": home_fair_prob, "away_fair_prob": away_fair_prob},
        stats=stats,
        odds_data=odds_data,
    )
    
    return result

