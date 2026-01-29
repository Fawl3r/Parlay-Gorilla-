"""
API-Sports Data Adapter

Converts API-Sports data format to internal format expected by services.
Maps:
- Fixtures → game schedules
- Standings → team strength metrics
- Team stats → offensive/defensive ratings
- Results → completed game scores
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class ApiSportsDataAdapter:
    """
    Adapter to convert API-Sports data format to internal service format.
    """
    
    @staticmethod
    def fixture_to_game_schedule(fixture: dict, sport: str) -> Optional[Dict[str, Any]]:
        """
        Convert API-Sports fixture to internal game schedule format.
        
        Args:
            fixture: API-Sports fixture dict
            sport: Sport key
        
        Returns:
            Dict with: date, home_team, away_team, fixture_id, league_id, status
        """
        if not fixture:
            return None
        
        fixture_obj = fixture.get("fixture", {}) if isinstance(fixture.get("fixture"), dict) else {}
        league_obj = fixture.get("league", {}) if isinstance(fixture.get("league"), dict) else {}
        teams_obj = fixture.get("teams", {}) if isinstance(fixture.get("teams"), dict) else {}
        
        fixture_id = fixture_obj.get("id")
        if not fixture_id:
            return None
        
        # Extract date
        date_str = fixture_obj.get("date")
        game_date = None
        if date_str:
            try:
                # API-Sports uses ISO 8601 format
                game_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            except Exception as e:
                logger.warning(f"Failed to parse fixture date '{date_str}': {e}")
        
        # Extract teams
        home_team_obj = teams_obj.get("home", {}) if isinstance(teams_obj.get("home"), dict) else {}
        away_team_obj = teams_obj.get("away", {}) if isinstance(teams_obj.get("away"), dict) else {}
        
        home_team_id = home_team_obj.get("id")
        home_team_name = home_team_obj.get("name")
        away_team_id = away_team_obj.get("id")
        away_team_name = away_team_obj.get("name")
        
        # Extract league
        league_id = league_obj.get("id")
        league_name = league_obj.get("name")
        
        # Extract status
        status_obj = fixture_obj.get("status", {}) if isinstance(fixture_obj.get("status"), dict) else {}
        status = status_obj.get("short", "NS")  # NS = Not Started
        
        return {
            "fixture_id": fixture_id,
            "league_id": league_id,
            "league_name": league_name,
            "date": game_date,
            "home_team_id": home_team_id,
            "home_team_name": home_team_name,
            "away_team_id": away_team_id,
            "away_team_name": away_team_name,
            "status": status,
            "sport": sport,
        }
    
    @staticmethod
    def standings_to_team_strength(standings: dict, sport: str, league_id: int) -> Dict[int, Dict[str, Any]]:
        """
        Convert API-Sports standings to team strength metrics.
        
        Args:
            standings: API-Sports standings dict (from payload_json)
            sport: Sport key
            league_id: League ID
        
        Returns:
            Dict mapping team_id -> strength metrics
        """
        team_strength = {}
        
        if not standings:
            return team_strength
        
        # Standings structure varies by sport
        # For football (soccer): standings[0]["league"]["standings"][0] -> list of teams
        # For NBA/NHL/MLB: might be different
        
        league_data = standings.get("league", {}) if isinstance(standings.get("league"), dict) else {}
        if not league_data:
            # Try direct access
            league_data = standings
        
        standings_list = league_data.get("standings", [])
        if not standings_list:
            return team_strength
        
        # Handle nested list structure (soccer groups/divisions)
        if standings_list and isinstance(standings_list[0], list):
            # Soccer format: list of lists (by group)
            for group in standings_list:
                for team_data in group:
                    if isinstance(team_data, dict):
                        team_info = team_data.get("team", {}) if isinstance(team_data.get("team"), dict) else team_data
                        team_id = team_info.get("id")
                        if team_id:
                            team_strength[team_id] = ApiSportsDataAdapter._extract_team_strength_from_standing(team_data, sport)
        elif isinstance(standings_list, list):
            # Direct list format
            for team_data in standings_list:
                if isinstance(team_data, dict):
                    team_info = team_data.get("team", {}) if isinstance(team_data.get("team"), dict) else team_data
                    team_id = team_info.get("id")
                    if team_id:
                        team_strength[team_id] = ApiSportsDataAdapter._extract_team_strength_from_standing(team_data, sport)
        
        return team_strength
    
    @staticmethod
    def _extract_team_strength_from_standing(team_data: dict, sport: str) -> Dict[str, Any]:
        """
        Extract team strength metrics from a single standing entry.
        
        Args:
            team_data: Single team standing dict
            sport: Sport key
        
        Returns:
            Dict with strength metrics
        """
        # Common fields across sports
        points = team_data.get("points", 0)
        wins = team_data.get("all", {}).get("win", 0) if isinstance(team_data.get("all"), dict) else team_data.get("wins", 0)
        losses = team_data.get("all", {}).get("lose", 0) if isinstance(team_data.get("all"), dict) else team_data.get("losses", 0)
        draws = team_data.get("all", {}).get("draw", 0) if isinstance(team_data.get("all"), dict) else team_data.get("draws", 0)
        games_played = team_data.get("all", {}).get("played", 0) if isinstance(team_data.get("all"), dict) else team_data.get("games", 0)
        
        # Calculate win percentage
        win_pct = 0.0
        if games_played > 0:
            win_pct = wins / games_played
        
        # Goals for/against (soccer) or points for/against (other sports)
        goals_for = team_data.get("all", {}).get("goals", {}).get("for", 0) if isinstance(team_data.get("all", {}).get("goals"), dict) else team_data.get("goals_for", 0)
        goals_against = team_data.get("all", {}).get("goals", {}).get("against", 0) if isinstance(team_data.get("all", {}).get("goals"), dict) else team_data.get("goals_against", 0)
        
        # Position/rank
        rank = team_data.get("rank", team_data.get("position", 0))
        
        return {
            "points": points,
            "wins": wins,
            "losses": losses,
            "draws": draws,
            "games_played": games_played,
            "win_percentage": win_pct,
            "goals_for": goals_for,
            "goals_against": goals_against,
            "goal_difference": goals_for - goals_against,
            "rank": rank,
        }

    @staticmethod
    def standings_to_normalized_team_stats(
        standings: dict,
        sport: str,
        league_id: int,
        season: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Derive normalized per-team stats from standings payload (no extra API calls).
        Each item is suitable for upsert into apisports_team_stats.payload_json and
        for StatsScraperService via team_stats_to_internal_format.

        Returns:
            List of dicts with: team_id, team_name, wins, losses, draws, games_played,
            points_for, points_against, points_per_game, points_allowed_per_game.
        """
        result: List[Dict[str, Any]] = []
        if not standings:
            return result

        league_data = standings.get("league", {}) if isinstance(standings.get("league"), dict) else standings
        standings_list = league_data.get("standings", [])
        if not standings_list:
            return result

        def iter_teams() -> Any:
            if standings_list and isinstance(standings_list[0], list):
                for group in standings_list:
                    for t in group:
                        yield t
            else:
                for t in standings_list:
                    yield t

        for team_data in iter_teams():
            if not isinstance(team_data, dict):
                continue
            team_info = team_data.get("team", {}) if isinstance(team_data.get("team"), dict) else team_data
            team_id = team_info.get("id")
            team_name = team_info.get("name") or team_data.get("name")
            if not team_id:
                continue
            strength = ApiSportsDataAdapter._extract_team_strength_from_standing(team_data, sport)
            games_played = strength.get("games_played") or 1
            goals_for = strength.get("goals_for", 0)
            goals_against = strength.get("goals_against", 0)
            # Use goals_for/against for soccer; same field names for points in other sports
            points_for = goals_for
            points_against = goals_against
            ppg = points_for / games_played if games_played else 0.0
            papg = points_against / games_played if games_played else 0.0
            result.append({
                "team_id": team_id,
                "team_name": team_name or "",
                "league_id": league_id,
                "season": season,
                "wins": strength.get("wins", 0),
                "losses": strength.get("losses", 0),
                "draws": strength.get("draws", 0),
                "games_played": games_played,
                "points_for": points_for,
                "points_against": points_against,
                "points_per_game": round(ppg, 2),
                "points_allowed_per_game": round(papg, 2),
            })
        return result

    @staticmethod
    def team_stats_to_internal_format(
        team_stats: dict,
        team_id: int,
        sport: str,
        season: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Convert API-Sports team stats to internal format (StatsScraperService-compatible).

        Accepts either:
        - Normalized payload from standings (team_name, points_per_game, points_allowed_per_game at top level).
        - Raw API-Sports team stats (nested, sport-specific).

        Returns:
            Dict with: team_id, season, record, offense (points_per_game, ...), defense (points_allowed_per_game, ...),
            recent_form, strength_ratings; plus team_name when present.
        """
        if not team_stats:
            return {}

        # Normalized payload from standings_derived (flat keys)
        if "points_per_game" in team_stats and "points_allowed_per_game" in team_stats:
            return ApiSportsDataAdapter._normalized_payload_to_internal(
                team_stats, team_id, sport, season
            )

        # Raw API-Sports structure
        wins = team_stats.get("wins", 0)
        losses = team_stats.get("losses", 0)
        draws = team_stats.get("draws", 0)
        games_played = wins + losses + draws
        win_pct = wins / games_played if games_played > 0 else 0.0

        offense = ApiSportsDataAdapter._extract_offensive_stats(team_stats, sport)
        defense = ApiSportsDataAdapter._extract_defensive_stats(team_stats, sport)
        offensive_rating = ApiSportsDataAdapter._calculate_offensive_rating(offense, sport)
        defensive_rating = ApiSportsDataAdapter._calculate_defensive_rating(defense, sport)
        overall_rating = (offensive_rating + defensive_rating) / 2.0

        out: Dict[str, Any] = {
            "team_id": team_id,
            "season": season,
            "record": {
                "wins": wins,
                "losses": losses,
                "ties": draws,
                "win_percentage": win_pct,
            },
            "offense": offense,
            "defense": defense,
            "recent_form": {
                "recent_wins": 0,
                "recent_losses": 0,
                "home_record": "0-0",
                "away_record": "0-0",
            },
            "strength_ratings": {
                "offensive_rating": offensive_rating,
                "defensive_rating": defensive_rating,
                "overall_rating": overall_rating,
            },
        }
        if team_stats.get("team_name"):
            out["team_name"] = team_stats["team_name"]
        return out

    @staticmethod
    def _normalized_payload_to_internal(
        payload: dict,
        team_id: int,
        sport: str,
        season: Optional[str],
    ) -> Dict[str, Any]:
        """Convert standings-derived normalized payload to StatsScraperService-compatible dict."""
        games_played = max(payload.get("games_played", 1), 1)
        wins = payload.get("wins", 0)
        losses = payload.get("losses", 0)
        draws = payload.get("draws", 0)
        win_pct = wins / games_played if games_played > 0 else 0.0
        ppg = float(payload.get("points_per_game", 0))
        papg = float(payload.get("points_allowed_per_game", 0))
        out: Dict[str, Any] = {
            "team_id": team_id,
            "season": season,
            "team_name": payload.get("team_name", ""),
            "record": {
                "wins": wins,
                "losses": losses,
                "ties": draws,
                "win_percentage": win_pct,
            },
            "offense": {
                "points_per_game": ppg,
                "yards_per_game": 0.0,
                "passing_yards_per_game": 0.0,
                "rushing_yards_per_game": 0.0,
            },
            "defense": {
                "points_allowed_per_game": papg,
                "yards_allowed_per_game": 0.0,
                "turnovers_forced": 0,
            },
            "recent_form": {
                "recent_wins": 0,
                "recent_losses": 0,
                "home_record": "0-0",
                "away_record": "0-0",
            },
            "strength_ratings": {
                "offensive_rating": min(100.0, max(0.0, (ppg / 30.0) * 50.0)),
                "defensive_rating": min(100.0, max(0.0, (30.0 / max(papg, 0.1)) * 50.0)),
                "overall_rating": 50.0,
            },
        }
        return out
    
    @staticmethod
    def _extract_offensive_stats(team_stats: dict, sport: str) -> Dict[str, Any]:
        """Extract offensive stats from API-Sports team stats."""
        offense = {}
        
        if sport in ["americanfootball_nfl", "nfl"]:
            # NFL: points, yards, passing yards, rushing yards
            offense["points_per_game"] = team_stats.get("points_for", 0) / max(team_stats.get("games", 1), 1)
            offense["yards_per_game"] = team_stats.get("total_yards", 0) / max(team_stats.get("games", 1), 1)
            offense["passing_yards_per_game"] = team_stats.get("passing_yards", 0) / max(team_stats.get("games", 1), 1)
            offense["rushing_yards_per_game"] = team_stats.get("rushing_yards", 0) / max(team_stats.get("games", 1), 1)
        elif sport in ["basketball_nba", "nba"]:
            # NBA: points, field goal %, assists
            offense["points_per_game"] = team_stats.get("points_for", 0) / max(team_stats.get("games", 1), 1)
            offense["field_goal_percentage"] = team_stats.get("fg_percentage", 0.0)
            offense["assists_per_game"] = team_stats.get("assists", 0) / max(team_stats.get("games", 1), 1)
        elif sport in ["icehockey_nhl", "nhl"]:
            # NHL: goals, shots, power play %
            offense["goals_per_game"] = team_stats.get("goals_for", 0) / max(team_stats.get("games", 1), 1)
            offense["shots_per_game"] = team_stats.get("shots_for", 0) / max(team_stats.get("games", 1), 1)
            offense["power_play_percentage"] = team_stats.get("pp_percentage", 0.0)
        elif sport in ["baseball_mlb", "mlb"]:
            # MLB: runs, batting average, on-base %
            offense["runs_per_game"] = team_stats.get("runs", 0) / max(team_stats.get("games", 1), 1)
            offense["batting_average"] = team_stats.get("avg", 0.0)
            offense["on_base_percentage"] = team_stats.get("obp", 0.0)
        elif sport == "football":
            # Soccer: goals, shots, possession
            offense["goals_per_game"] = team_stats.get("goals_for", 0) / max(team_stats.get("games", 1), 1)
            offense["shots_per_game"] = team_stats.get("shots_for", 0) / max(team_stats.get("games", 1), 1)
            offense["possession_percentage"] = team_stats.get("possession", 0.0)
        
        return offense
    
    @staticmethod
    def _extract_defensive_stats(team_stats: dict, sport: str) -> Dict[str, Any]:
        """Extract defensive stats from API-Sports team stats."""
        defense = {}
        
        if sport in ["americanfootball_nfl", "nfl"]:
            # NFL: points allowed, yards allowed, turnovers forced
            defense["points_allowed_per_game"] = team_stats.get("points_against", 0) / max(team_stats.get("games", 1), 1)
            defense["yards_allowed_per_game"] = team_stats.get("total_yards_allowed", 0) / max(team_stats.get("games", 1), 1)
            defense["turnovers_forced"] = team_stats.get("takeaways", 0)
        elif sport in ["basketball_nba", "nba"]:
            # NBA: points allowed, rebounds, steals
            defense["points_allowed_per_game"] = team_stats.get("points_against", 0) / max(team_stats.get("games", 1), 1)
            defense["rebounds_per_game"] = team_stats.get("rebounds", 0) / max(team_stats.get("games", 1), 1)
            defense["steals_per_game"] = team_stats.get("steals", 0) / max(team_stats.get("games", 1), 1)
        elif sport in ["icehockey_nhl", "nhl"]:
            # NHL: goals against, penalty kill %
            defense["goals_against_per_game"] = team_stats.get("goals_against", 0) / max(team_stats.get("games", 1), 1)
            defense["penalty_kill_percentage"] = team_stats.get("pk_percentage", 0.0)
        elif sport in ["baseball_mlb", "mlb"]:
            # MLB: ERA, WHIP
            defense["era"] = team_stats.get("era", 0.0)
            defense["whip"] = team_stats.get("whip", 0.0)
        elif sport == "football":
            # Soccer: goals against, clean sheets
            defense["goals_against_per_game"] = team_stats.get("goals_against", 0) / max(team_stats.get("games", 1), 1)
            defense["clean_sheets"] = team_stats.get("clean_sheets", 0)
        
        return defense
    
    @staticmethod
    def _calculate_offensive_rating(offense: dict, sport: str) -> float:
        """
        Calculate offensive rating (0-100 scale) from offensive stats.
        
        Higher is better. Normalized to league average = 50.
        """
        if not offense:
            return 50.0
        
        # Simple heuristic: use points/goals per game as base
        if sport in ["americanfootball_nfl", "nfl"]:
            ppg = offense.get("points_per_game", 0.0)
            # NFL average ~22 PPG, so scale: (ppg / 22) * 50
            return min(100.0, max(0.0, (ppg / 22.0) * 50.0))
        elif sport in ["basketball_nba", "nba"]:
            ppg = offense.get("points_per_game", 0.0)
            # NBA average ~112 PPG
            return min(100.0, max(0.0, (ppg / 112.0) * 50.0))
        elif sport in ["icehockey_nhl", "nhl"]:
            gpg = offense.get("goals_per_game", 0.0)
            # NHL average ~3.0 GPG
            return min(100.0, max(0.0, (gpg / 3.0) * 50.0))
        elif sport in ["baseball_mlb", "mlb"]:
            rpg = offense.get("runs_per_game", 0.0)
            # MLB average ~4.5 RPG
            return min(100.0, max(0.0, (rpg / 4.5) * 50.0))
        elif sport == "football":
            gpg = offense.get("goals_per_game", 0.0)
            # Soccer average ~1.5 GPG
            return min(100.0, max(0.0, (gpg / 1.5) * 50.0))
        
        return 50.0
    
    @staticmethod
    def _calculate_defensive_rating(defense: dict, sport: str) -> float:
        """
        Calculate defensive rating (0-100 scale) from defensive stats.
        
        Higher is better (fewer points/goals allowed = better defense).
        Normalized to league average = 50.
        """
        if not defense:
            return 50.0
        
        # For defense, lower points/goals allowed = higher rating
        if sport in ["americanfootball_nfl", "nfl"]:
            papg = defense.get("points_allowed_per_game", 22.0)
            # NFL average ~22 PAPG, so scale: (22 / papg) * 50
            return min(100.0, max(0.0, (22.0 / max(papg, 1.0)) * 50.0))
        elif sport in ["basketball_nba", "nba"]:
            papg = defense.get("points_allowed_per_game", 112.0)
            return min(100.0, max(0.0, (112.0 / max(papg, 1.0)) * 50.0))
        elif sport in ["icehockey_nhl", "nhl"]:
            gapg = defense.get("goals_against_per_game", 3.0)
            return min(100.0, max(0.0, (3.0 / max(gapg, 0.1)) * 50.0))
        elif sport in ["baseball_mlb", "mlb"]:
            era = defense.get("era", 4.5)
            # Lower ERA = better, so invert: (4.5 / era) * 50
            return min(100.0, max(0.0, (4.5 / max(era, 0.1)) * 50.0))
        elif sport == "football":
            gapg = defense.get("goals_against_per_game", 1.5)
            return min(100.0, max(0.0, (1.5 / max(gapg, 0.1)) * 50.0))
        
        return 50.0
    
    @staticmethod
    def result_to_game_result(result: dict, sport: str) -> Optional[Dict[str, Any]]:
        """
        Convert API-Sports result to internal game result format.
        
        Args:
            result: API-Sports result dict (from payload_json)
            sport: Sport key
        
        Returns:
            Dict with: fixture_id, home_team_id, away_team_id, home_score, away_score, finished_at
        """
        if not result:
            return None
        
        fixture_obj = result.get("fixture", {}) if isinstance(result.get("fixture"), dict) else {}
        teams_obj = result.get("teams", {}) if isinstance(result.get("teams"), dict) else {}
        score_obj = result.get("score", {}) if isinstance(result.get("score"), dict) else {}
        
        fixture_id = fixture_obj.get("id")
        if not fixture_id:
            return None
        
        # Extract teams
        home_team_obj = teams_obj.get("home", {}) if isinstance(teams_obj.get("home"), dict) else {}
        away_team_obj = teams_obj.get("away", {}) if isinstance(teams_obj.get("away"), dict) else {}
        
        home_team_id = home_team_obj.get("id")
        away_team_id = away_team_obj.get("id")
        
        # Extract scores
        fulltime_score = score_obj.get("fulltime", {}) if isinstance(score_obj.get("fulltime"), dict) else {}
        home_score = fulltime_score.get("home") or score_obj.get("home", None)
        away_score = fulltime_score.get("away") or score_obj.get("away", None)
        
        # Extract finish time
        date_str = fixture_obj.get("date")
        finished_at = None
        if date_str:
            try:
                finished_at = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            except Exception as e:
                logger.warning(f"Failed to parse result date '{date_str}': {e}")
        
        return {
            "fixture_id": fixture_id,
            "home_team_id": home_team_id,
            "away_team_id": away_team_id,
            "home_score": home_score,
            "away_score": away_score,
            "finished_at": finished_at,
            "sport": sport,
        }
