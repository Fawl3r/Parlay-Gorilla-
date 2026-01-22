"""Team feature builder for derived bettor-grade metrics."""

from __future__ import annotations

import math
from typing import Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class TeamFeatureBuilder:
    """Builds derived features from canonical team stats."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def build_features(
        self,
        team_name: str,
        sport: str,
        season: str,
        canonical_stats: Dict,
    ) -> Dict:
        """Build derived features from canonical stats.
        
        Args:
            team_name: Team name
            sport: Sport identifier
            season: Season year
            canonical_stats: Canonical stats dictionary
        
        Returns:
            Features dictionary with form, strength, tempo_volatility, matchup_edges
        """
        # Compute form scores
        form = self._compute_form_scores(canonical_stats)
        
        # Compute opponent-adjusted strength
        strength = await self._compute_opponent_adjusted_strength(
            team_name, sport, season, canonical_stats
        )
        
        # Compute tempo and volatility
        tempo_volatility = self._compute_tempo_volatility(canonical_stats, sport)
        
        # Matchup edges (computed when comparing two teams)
        matchup_edges = {
            "offense_vs_defense_edge": None,  # Computed in matchup context
            "defense_vs_offense_edge": None,
        }
        
        return {
            "form": form,
            "strength": strength,
            "tempo_volatility": tempo_volatility,
            "matchup_edges": matchup_edges,
        }
    
    def _compute_form_scores(self, stats: Dict) -> Dict:
        """Compute form scores for last 5 and last 10 games.
        
        Form score: -1.0 (terrible) to 1.0 (excellent), weighted by recency.
        """
        last_5 = stats.get("last_n", {}).get("last_5", {})
        last_10 = stats.get("last_n", {}).get("last_10", {})
        
        form_5 = self._compute_form_score_from_last_n(last_5)
        form_10 = self._compute_form_score_from_last_n(last_10)
        
        # Home/away split delta
        splits = stats.get("splits", {})
        home = splits.get("home", {})
        away = splits.get("away", {})
        
        # Get scoring averages (sport-specific)
        home_avg = self._get_scoring_avg(home)
        away_avg = self._get_scoring_avg(away)
        home_avg_allowed = self._get_scoring_avg_allowed(home)
        away_avg_allowed = self._get_scoring_avg_allowed(away)
        
        home_away_split_delta = None
        if home_avg is not None and away_avg is not None:
            home_away_split_delta = home_avg - away_avg
        
        return {
            "form_score_5": form_5,
            "form_score_10": form_10,
            "home_away_split_delta": home_away_split_delta,
        }
    
    def _compute_form_score_from_last_n(self, last_n: Dict) -> Optional[float]:
        """Compute form score from last N games stats.
        
        Formula: (win_rate * 0.6) + (scoring_margin_normalized * 0.4)
        """
        wins = last_n.get("wins", 0)
        losses = last_n.get("losses", 0)
        ties = last_n.get("ties", 0)
        
        total_games = wins + losses + ties
        if total_games == 0:
            return None
        
        # Win rate component (0.0 to 1.0)
        win_rate = (wins + (ties * 0.5)) / total_games
        
        # Scoring margin component
        points_for = self._get_scoring_avg(last_n)
        points_against = self._get_scoring_avg_allowed(last_n)
        
        if points_for is None or points_against is None:
            # Fallback to win rate only
            return (win_rate * 2.0) - 1.0  # Scale to -1.0 to 1.0
        
        margin = points_for - points_against
        
        # Normalize margin (assume typical range is -20 to +20 for most sports)
        # This is a simple normalization, can be improved with league-specific baselines
        normalized_margin = max(-1.0, min(1.0, margin / 20.0))
        
        # Combined score
        form_score = (win_rate * 0.6) + (normalized_margin * 0.4)
        
        # Scale to -1.0 to 1.0
        return (form_score * 2.0) - 1.0
    
    def _get_scoring_avg(self, stats: Dict) -> Optional[float]:
        """Get scoring average from stats (points/runs/goals depending on sport)."""
        return (
            stats.get("points_for_avg") or
            stats.get("runs_for_avg") or
            stats.get("goals_for_avg")
        )
    
    def _get_scoring_avg_allowed(self, stats: Dict) -> Optional[float]:
        """Get scoring average allowed from stats."""
        return (
            stats.get("points_against_avg") or
            stats.get("runs_against_avg") or
            stats.get("goals_against_avg")
        )
    
    async def _compute_opponent_adjusted_strength(
        self,
        team_name: str,
        sport: str,
        season: str,
        stats: Dict,
    ) -> Dict:
        """Compute opponent-adjusted offense and defense ratings.
        
        Normalizes team performance relative to league averages.
        """
        # Get league averages
        league_avg = await self._get_league_averages(sport, season)
        
        if not league_avg:
            # Fallback to raw efficiency ratings if league averages unavailable
            efficiency = stats.get("efficiency", {})
            offense_rating = efficiency.get("offense_rating") or 0.0
            defense_rating = efficiency.get("defense_rating") or 0.0
            return {
                "opponent_adjusted_offense": offense_rating,
                "opponent_adjusted_defense": defense_rating,
                "net_strength": offense_rating - defense_rating,
            }
        
        # Get team's raw scoring
        scoring = stats.get("scoring", {})
        team_points_for = self._get_scoring_avg(scoring)
        team_points_against = self._get_scoring_avg_allowed(scoring)
        
        league_points_for = league_avg.get("points_for_avg") or league_avg.get("runs_for_avg") or league_avg.get("goals_for_avg")
        league_points_against = league_avg.get("points_against_avg") or league_avg.get("runs_against_avg") or league_avg.get("goals_against_avg")
        
        if not team_points_for or not team_points_against or not league_points_for or not league_points_against:
            # Fallback
            efficiency = stats.get("efficiency", {})
            offense_rating = efficiency.get("offense_rating") or 0.0
            defense_rating = efficiency.get("defense_rating") or 0.0
            return {
                "opponent_adjusted_offense": offense_rating,
                "opponent_adjusted_defense": defense_rating,
                "net_strength": offense_rating - defense_rating,
            }
        
        # Opponent-adjusted: team performance relative to league average
        # Positive = better than average, negative = worse than average
        opponent_adjusted_offense = team_points_for - league_points_for
        opponent_adjusted_defense = league_points_against - team_points_against  # Inverted (lower is better)
        
        net_strength = opponent_adjusted_offense + opponent_adjusted_defense
        
        return {
            "opponent_adjusted_offense": opponent_adjusted_offense,
            "opponent_adjusted_defense": opponent_adjusted_defense,
            "net_strength": net_strength,
        }
    
    async def _get_league_averages(self, sport: str, season: str) -> Optional[Dict]:
        """Get league average stats for opponent adjustment.
        
        Computes averages from all teams in team_stats_current.
        """
        result = await self.db.execute(
            text("""
                SELECT metrics_json FROM team_stats_current
                WHERE sport = :sport AND season = :season
            """),
            {"sport": sport, "season": season}
        )
        rows = result.fetchall()
        
        if not rows:
            return None
        
        # Aggregate scoring averages
        points_for_sum = 0.0
        points_against_sum = 0.0
        count = 0
        
        for row in rows:
            metrics = row[0]
            scoring = metrics.get("scoring", {})
            points_for = self._get_scoring_avg(scoring)
            points_against = self._get_scoring_avg_allowed(scoring)
            
            if points_for is not None and points_against is not None:
                points_for_sum += points_for
                points_against_sum += points_against
                count += 1
        
        if count == 0:
            return None
        
        return {
            "points_for_avg": points_for_sum / count,
            "points_against_avg": points_against_sum / count,
        }
    
    def _compute_tempo_volatility(self, stats: Dict, sport: str) -> Dict:
        """Compute tempo and scoring volatility.
        
        Volatility: standard deviation of scoring in recent games.
        If game logs unavailable, approximate from splits/trends.
        """
        tempo = stats.get("tempo", {})
        pace_proxy = tempo.get("pace")
        
        # Volatility: approximate from last_n stats if available
        last_10 = stats.get("last_n", {}).get("last_10", {})
        scoring_volatility = None
        
        # Simple approximation: if we have last_10 points_for_avg, assume some variance
        # This is a simplified approach - ideally we'd have actual game-by-game scores
        points_for_avg = self._get_scoring_avg(last_10)
        if points_for_avg is not None:
            # Rough estimate: assume 10-15% coefficient of variation
            # This is sport-dependent but provides a reasonable baseline
            scoring_volatility = points_for_avg * 0.12  # 12% std dev estimate
        
        return {
            "pace_proxy": pace_proxy,
            "scoring_volatility": scoring_volatility,
        }
    
    def compute_matchup_edges(
        self,
        team_stats: Dict,
        opponent_stats: Dict,
    ) -> Dict:
        """Compute matchup edges between two teams.
        
        Args:
            team_stats: Team's canonical stats
            opponent_stats: Opponent's canonical stats
        
        Returns:
            Matchup edges dictionary
        """
        team_scoring = team_stats.get("scoring", {})
        opponent_scoring = opponent_stats.get("scoring", {})
        
        team_points_for = self._get_scoring_avg(team_scoring)
        team_points_against = self._get_scoring_avg_allowed(team_scoring)
        opponent_points_for = self._get_scoring_avg(opponent_scoring)
        opponent_points_against = self._get_scoring_avg_allowed(opponent_scoring)
        
        offense_vs_defense_edge = None
        defense_vs_offense_edge = None
        
        if team_points_for is not None and opponent_points_against is not None:
            offense_vs_defense_edge = team_points_for - opponent_points_against
        
        if opponent_points_for is not None and team_points_against is not None:
            defense_vs_offense_edge = opponent_points_for - team_points_against
        
        return {
            "offense_vs_defense_edge": offense_vs_defense_edge,
            "defense_vs_offense_edge": defense_vs_offense_edge,
        }
