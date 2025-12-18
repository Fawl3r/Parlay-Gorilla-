from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.data_fetchers.injuries import InjuryFetcher
from app.services.data_fetchers.nba_stats import NBAStatsFetcher
from app.services.data_fetchers.nfl_stats import NFLStatsFetcher
from app.services.data_fetchers.nhl_stats import NHLStatsFetcher
from app.services.data_fetchers.weather import WeatherFetcher
from app.services.probability_engine_impl.base_engine import BaseProbabilityEngine


class GenericProbabilityEngine(BaseProbabilityEngine):
    """Fallback probability engine for sports without dedicated models."""

    sport_code = "GENERIC"

    def __init__(self, db: AsyncSession):
        super().__init__(db, injury_fetcher=InjuryFetcher())


class NFLProbabilityEngine(BaseProbabilityEngine):
    """NFL-specific probability engine (default)."""

    sport_code = "NFL"

    def __init__(self, db: AsyncSession):
        super().__init__(
            db,
            stats_fetcher=NFLStatsFetcher(),
            weather_fetcher=WeatherFetcher(),
            injury_fetcher=InjuryFetcher(),
        )


class NBAProbabilityEngine(BaseProbabilityEngine):
    """NBA probability engine with pace/offensive rating heuristics."""

    sport_code = "NBA"

    def __init__(self, db: AsyncSession):
        super().__init__(db, stats_fetcher=NBAStatsFetcher(), injury_fetcher=InjuryFetcher())

    async def _apply_situational_adjustments(
        self,
        home_team: str,
        away_team: str,
        is_home_outcome: bool,
        game_start_time: Optional[datetime],
    ) -> float:
        base = await super()._apply_situational_adjustments(
            home_team, away_team, is_home_outcome, game_start_time
        )
        if is_home_outcome:
            base += 0.02  # NBA home-court edge
        if game_start_time and game_start_time.weekday() in (0, 1):  # Monday/Tuesday
            base -= 0.01
        return base

    async def _apply_sport_specific_adjustments(
        self,
        implied_prob: float,
        market_id: str,
        outcome: str,
        home_team: str,
        away_team: str,
        market_type: Optional[str] = None,
    ) -> float:
        if not self.stats_fetcher:
            return 0.0

        favored_team = home_team if "home" in (outcome or "").lower() else away_team
        opponent_team = away_team if favored_team == home_team else home_team

        team_stats = await self._get_team_stats(favored_team)
        opponent_stats = await self._get_team_stats(opponent_team)
        if not team_stats or not opponent_stats:
            return 0.0

        offensive_edge = (
            team_stats.get("offensive_rating", 110) - opponent_stats.get("defensive_rating", 110)
        ) / 100.0
        adjustment = offensive_edge * 0.1

        if market_type == "totals":
            pace_avg = (team_stats.get("pace", 99) + opponent_stats.get("pace", 99)) / 2
            adjustment += (pace_avg - 100) * 0.003

        rebound_edge = (team_stats.get("rebound_rate", 50) - opponent_stats.get("rebound_rate", 50)) / 100.0
        adjustment += rebound_edge * 0.05

        return adjustment


class NHLProbabilityEngine(BaseProbabilityEngine):
    """NHL probability engine using goal differential & special teams heuristics."""

    sport_code = "NHL"

    def __init__(self, db: AsyncSession):
        super().__init__(db, stats_fetcher=NHLStatsFetcher(), injury_fetcher=InjuryFetcher())

    async def _apply_sport_specific_adjustments(
        self,
        implied_prob: float,
        market_id: str,
        outcome: str,
        home_team: str,
        away_team: str,
        market_type: Optional[str] = None,
    ) -> float:
        if not self.stats_fetcher:
            return 0.0

        favored_team = home_team if "home" in (outcome or "").lower() else away_team
        opponent_team = away_team if favored_team == home_team else home_team

        team_stats = await self._get_team_stats(favored_team)
        opponent_stats = await self._get_team_stats(opponent_team)
        if not team_stats or not opponent_stats:
            return 0.0

        adjustment = 0.0
        goal_edge = (team_stats.get("goals_for", 3.0) - opponent_stats.get("goals_against", 2.8)) * 0.05
        adjustment += goal_edge

        special_teams_edge = (
            (team_stats.get("power_play_pct", 20) - opponent_stats.get("penalty_kill_pct", 80)) / 100.0
        )
        adjustment += special_teams_edge * 0.05

        recent_form = await self._get_recent_form(favored_team, games=5)
        if recent_form:
            wins = sum(1 for game in recent_form if game.get("is_win"))
            adjustment += (wins / len(recent_form) - 0.5) * 0.05

        return adjustment


class MLBProbabilityEngine(BaseProbabilityEngine):
    """
    MLB probability engine with baseball-specific adjustments.
    
    Heavy weights:
    - Starting pitcher ERA/WHIP (25%)
    - Bullpen strength (15%)
    - Run differential (20%)
    
    Medium weights:
    - Recent form (15%)
    - Home/away splits (10%)
    
    Light weights:
    - Weather/park factors (10%)
    - Injuries (5%)
    """

    sport_code = "MLB"

    # Weight constants for MLB probability calculation
    STARTER_WEIGHT = 0.25
    BULLPEN_WEIGHT = 0.15
    RUN_DIFF_WEIGHT = 0.20
    FORM_WEIGHT = 0.15
    HOME_AWAY_WEIGHT = 0.10
    WEATHER_WEIGHT = 0.10
    INJURY_WEIGHT = 0.05

    def __init__(self, db: AsyncSession):
        super().__init__(
            db,
            stats_fetcher=None,  # Use feature pipeline instead
            weather_fetcher=WeatherFetcher(),
            injury_fetcher=InjuryFetcher(),
        )

    async def _apply_situational_adjustments(
        self,
        home_team: str,
        away_team: str,
        is_home_outcome: bool,
        game_start_time: Optional[datetime],
    ) -> float:
        base = await super()._apply_situational_adjustments(
            home_team, away_team, is_home_outcome, game_start_time
        )
        if is_home_outcome:
            base += 0.01  # Slight home boost
        return base

    async def _apply_sport_specific_adjustments(
        self,
        implied_prob: float,
        market_id: str,
        outcome: str,
        home_team: str,
        away_team: str,
        market_type: Optional[str] = None,
    ) -> float:
        favored_team = home_team if "home" in (outcome or "").lower() else away_team
        opponent_team = away_team if favored_team == home_team else home_team

        team_stats = self._team_stats_cache.get(favored_team.lower())
        opponent_stats = self._team_stats_cache.get(opponent_team.lower())
        if not team_stats or not opponent_stats:
            return 0.0

        adjustment = 0.0

        team_era = team_stats.get("pitching", {}).get("era", team_stats.get("era", 4.00))
        opp_era = opponent_stats.get("pitching", {}).get("era", opponent_stats.get("era", 4.00))
        era_diff = (opp_era - team_era) / 2.0
        adjustment += era_diff * self.STARTER_WEIGHT * 0.5

        team_bp_era = team_stats.get("bullpen", {}).get("bullpen_era", 4.00)
        opp_bp_era = opponent_stats.get("bullpen", {}).get("bullpen_era", 4.00)
        bp_diff = (opp_bp_era - team_bp_era) / 2.0
        adjustment += bp_diff * self.BULLPEN_WEIGHT * 0.3

        team_runs = team_stats.get("batting", {}).get("runs_per_game", 4.5)
        team_runs_allowed = team_stats.get("pitching", {}).get("runs_allowed_per_game", 4.5)
        opp_runs = opponent_stats.get("batting", {}).get("runs_per_game", 4.5)
        opp_runs_allowed = opponent_stats.get("pitching", {}).get("runs_allowed_per_game", 4.5)

        team_diff = team_runs - team_runs_allowed
        opp_diff = opp_runs - opp_runs_allowed
        run_diff_edge = (team_diff - opp_diff) / 3.0
        adjustment += run_diff_edge * self.RUN_DIFF_WEIGHT * 0.4

        if market_type == "totals":
            team_ops = team_stats.get("batting", {}).get("ops", 0.720)
            opp_ops = opponent_stats.get("batting", {}).get("ops", 0.720)
            combined_ops = (team_ops + opp_ops) / 2
            if combined_ops > 0.750:
                adjustment += 0.02
            elif combined_ops < 0.690:
                adjustment -= 0.02

        return max(-0.10, min(0.10, adjustment))


class SoccerProbabilityEngine(BaseProbabilityEngine):
    """
    Soccer probability engine with xG and points-per-game weighting.
    
    Heavy weights:
    - Expected goals (xG) (25%)
    - Points per game (20%)
    - Goal differential (15%)
    
    Medium weights:
    - Home/away form splits (15%)
    - Recent form (10%)
    
    Light weights:
    - Head-to-head (10%)
    - Injuries (5%)
    """

    sport_code = "SOCCER"

    # Weight constants for Soccer probability calculation
    XG_WEIGHT = 0.25
    PPG_WEIGHT = 0.20
    GOAL_DIFF_WEIGHT = 0.15
    FORM_SPLIT_WEIGHT = 0.15
    RECENT_FORM_WEIGHT = 0.10
    H2H_WEIGHT = 0.10
    INJURY_WEIGHT = 0.05

    def __init__(self, db: AsyncSession, league: str = "epl"):
        super().__init__(db, stats_fetcher=None, injury_fetcher=InjuryFetcher())
        self.league = league

    async def _apply_situational_adjustments(
        self,
        home_team: str,
        away_team: str,
        is_home_outcome: bool,
        game_start_time: Optional[datetime],
    ) -> float:
        base = await super()._apply_situational_adjustments(
            home_team, away_team, is_home_outcome, game_start_time
        )
        if is_home_outcome:
            base += 0.025  # 2.5% home boost

        # Midweek games (European competition fatigue)
        if game_start_time and game_start_time.weekday() in (1, 2):  # Tue/Wed
            base -= 0.005

        return base

    async def _apply_sport_specific_adjustments(
        self,
        implied_prob: float,
        market_id: str,
        outcome: str,
        home_team: str,
        away_team: str,
        market_type: Optional[str] = None,
    ) -> float:
        adjustment = 0.0
        favored_team = home_team if "home" in (outcome or "").lower() else away_team
        opponent_team = away_team if favored_team == home_team else home_team

        # Get team stats from cache
        team_stats = self._team_stats_cache.get(favored_team.lower())
        opponent_stats = self._team_stats_cache.get(opponent_team.lower())

        if not team_stats or not opponent_stats:
            return 0.0

        # 1. Expected Goals (xG)
        team_xg = team_stats.get("offense", {}).get("xg", team_stats.get("xg", 1.5))
        team_xga = team_stats.get("defense", {}).get("xg_against", team_stats.get("xga", 1.3))
        opp_xg = opponent_stats.get("offense", {}).get("xg", opponent_stats.get("xg", 1.5))
        opp_xga = opponent_stats.get("defense", {}).get("xg_against", opponent_stats.get("xga", 1.3))

        team_net_xg = team_xg - team_xga
        opp_net_xg = opp_xg - opp_xga
        xg_edge = (team_net_xg - opp_net_xg) / 1.5
        adjustment += xg_edge * self.XG_WEIGHT

        # 2. Points per game
        team_ppg = team_stats.get("record", {}).get("points_per_game", 1.5)
        opp_ppg = opponent_stats.get("record", {}).get("points_per_game", 1.5)
        ppg_edge = (team_ppg - opp_ppg) / 1.5
        adjustment += ppg_edge * self.PPG_WEIGHT * 0.5

        # 3. Goal differential per game
        team_goals = team_stats.get("goals", {})
        opp_goals = opponent_stats.get("goals", {})

        team_gpg = team_goals.get("per_game", 1.5)
        team_gapg = team_goals.get("conceded_per_game", 1.3)
        opp_gpg = opp_goals.get("per_game", 1.5)
        opp_gapg = opp_goals.get("conceded_per_game", 1.3)

        team_gd = team_gpg - team_gapg
        opp_gd = opp_gpg - opp_gapg
        gd_edge = (team_gd - opp_gd) / 1.0
        adjustment += gd_edge * self.GOAL_DIFF_WEIGHT * 0.4

        # 4. Home/away form splits
        is_home = favored_team.lower() == home_team.lower()
        if is_home:
            home_form = team_stats.get("situational", {}).get("home_form", {})
            home_ppg = home_form.get("points_per_game", team_ppg)
            adjustment += (home_ppg - 1.5) * self.FORM_SPLIT_WEIGHT * 0.3
        else:
            away_form = team_stats.get("situational", {}).get("away_form", {})
            away_ppg = away_form.get("points_per_game", team_ppg * 0.8)
            adjustment += (away_ppg - 1.2) * self.FORM_SPLIT_WEIGHT * 0.3

        # 5. Totals adjustments for over/under
        if market_type == "totals":
            combined_xg = team_xg + opp_xg
            if combined_xg > 3.0:
                adjustment += 0.015
            elif combined_xg < 2.5:
                adjustment -= 0.015

        return max(-0.12, min(0.12, adjustment))


