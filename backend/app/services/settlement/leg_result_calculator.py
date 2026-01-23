"""Leg result calculator for settlement rules."""

from __future__ import annotations

import logging
from typing import Literal
from decimal import Decimal

from app.models.game import Game
from app.models.parlay_leg import ParlayLeg


logger = logging.getLogger(__name__)

LegResult = Literal["WON", "LOST", "PUSH", "VOID", "PENDING"]


class LegResultCalculator:
    """Calculate leg results based on game outcomes."""
    
    @staticmethod
    def _normalize_score(score) -> int | None:
        """Normalize score to int, handling None, int, float, Decimal."""
        if score is None:
            return None
        if isinstance(score, (int, float, Decimal)):
            return int(score)
        try:
            return int(float(score))
        except (ValueError, TypeError):
            logger.warning(f"Invalid score type: {type(score)}, value: {score}")
            return None
    
    @staticmethod
    def _normalize_line(line) -> float | None:
        """Normalize line to float, handling None, int, float, Decimal, string."""
        if line is None:
            return None
        if isinstance(line, (int, float, Decimal)):
            return float(line)
        if isinstance(line, str):
            try:
                return float(line)
            except ValueError:
                logger.warning(f"Invalid line string: {line}")
                return None
        try:
            return float(line)
        except (ValueError, TypeError):
            logger.warning(f"Invalid line type: {type(line)}, value: {line}")
            return None
    
    @staticmethod
    def _normalize_team_name(name: str | None) -> str:
        """Normalize team name for comparison."""
        if name is None:
            return ""
        return name.lower().strip()
    
    @staticmethod
    def _match_team_selection(selection: str, home_team: str, away_team: str) -> tuple[bool, bool]:
        """Match selection to home/away team.
        
        Returns:
            (is_home, is_away) tuple
        """
        if not selection:
            return (False, False)
        
        selection_norm = LegResultCalculator._normalize_team_name(selection)
        home_norm = LegResultCalculator._normalize_team_name(home_team)
        away_norm = LegResultCalculator._normalize_team_name(away_team)
        
        is_home = (
            selection_norm == "home" or
            selection_norm == home_norm or
            selection == home_team  # Exact match (case-sensitive)
        )
        is_away = (
            selection_norm == "away" or
            selection_norm == away_norm or
            selection == away_team  # Exact match (case-sensitive)
        )
        
        return (is_home, is_away)
    
    @staticmethod
    def calculate_moneyline_result(leg: ParlayLeg, game: Game) -> LegResult:
        """Calculate moneyline (h2h) leg result.
        
        Rules:
        - If selected team score > opponent at FINAL → WON
        - Otherwise → LOST
        
        Args:
            leg: ParlayLeg with market_type="h2h"
            game: Game with status="FINAL" and scores
            
        Returns:
            "WON", "LOST", "PUSH", "VOID", or "PENDING"
        """
        # Input validation
        if not leg or not game:
            logger.warning("calculate_moneyline_result: Missing leg or game")
            return "VOID"
        
        if game.status != "FINAL":
            return "PENDING"
        
        # Normalize and validate scores
        home_score = LegResultCalculator._normalize_score(game.home_score)
        away_score = LegResultCalculator._normalize_score(game.away_score)
        
        if home_score is None or away_score is None:
            logger.warning(
                f"calculate_moneyline_result: Missing scores for game {game.id}, "
                f"home_score={game.home_score}, away_score={game.away_score}"
            )
            return "VOID"
        
        # Match selection to team
        is_home, is_away = LegResultCalculator._match_team_selection(
            leg.selection, game.home_team, game.away_team
        )
        
        if is_home:
            if home_score > away_score:
                return "WON"
            elif home_score < away_score:
                return "LOST"
            else:
                # Tie - typically LOST for moneyline, but could be PUSH depending on rules
                logger.info(f"calculate_moneyline_result: Tie game for home selection, game {game.id}")
                return "LOST"
        
        elif is_away:
            if away_score > home_score:
                return "WON"
            elif away_score < home_score:
                return "LOST"
            else:
                logger.info(f"calculate_moneyline_result: Tie game for away selection, game {game.id}")
                return "LOST"
        
        # Selection doesn't match either team
        logger.warning(
            f"calculate_moneyline_result: Unmatched selection '{leg.selection}' "
            f"for game {game.id} (home: {game.home_team}, away: {game.away_team})"
        )
        return "VOID"
        
        # Normalize selection to home/away
        selection_lower = leg.selection.lower().strip()
        home_team_lower = game.home_team.lower()
        away_team_lower = game.away_team.lower()
        
        is_home = (
            selection_lower == "home" or
            selection_lower == home_team_lower or
            leg.selection == game.home_team
        )
        is_away = (
            selection_lower == "away" or
            selection_lower == away_team_lower or
            leg.selection == game.away_team
        )
        
        if is_home:
            if game.home_score > game.away_score:
                return "WON"
            elif game.home_score < game.away_score:
                return "LOST"
            else:
                # Tie - typically LOST for moneyline, but could be PUSH depending on rules
                return "LOST"
        
        elif is_away:
            if game.away_score > game.home_score:
                return "WON"
            elif game.away_score < game.home_score:
                return "LOST"
            else:
                return "LOST"
        
        return "VOID"
    
    @staticmethod
    def calculate_spread_result(leg: ParlayLeg, game: Game) -> LegResult:
        """Calculate spread leg result.
        
        Rules:
        - Compute final margin: (home_score - away_score)
        - Apply line based on selection:
          - If selection = home -3.5: home_score - away_score - 3.5 > 0 → WON
          - If selection = away +3.5: away_score + 3.5 - home_score > 0 → WON
        - Equals 0 → PUSH
        
        Args:
            leg: ParlayLeg with market_type="spreads" and line
            game: Game with status="FINAL" and scores
            
        Returns:
            "WON", "LOST", "PUSH", "VOID", or "PENDING"
        """
        # Input validation
        if not leg or not game:
            logger.warning("calculate_spread_result: Missing leg or game")
            return "VOID"
        
        if game.status != "FINAL":
            return "PENDING"
        
        # Normalize and validate scores
        home_score = LegResultCalculator._normalize_score(game.home_score)
        away_score = LegResultCalculator._normalize_score(game.away_score)
        
        if home_score is None or away_score is None:
            logger.warning(
                f"calculate_spread_result: Missing scores for game {game.id}, "
                f"home_score={game.home_score}, away_score={game.away_score}"
            )
            return "VOID"
        
        # Normalize and validate line
        line = LegResultCalculator._normalize_line(leg.line)
        if line is None:
            logger.warning(
                f"calculate_spread_result: Missing or invalid line for leg {leg.id}, "
                f"line={leg.line}"
            )
            return "VOID"
        
        margin = home_score - away_score
        
        # Match selection to team
        is_home, is_away = LegResultCalculator._match_team_selection(
            leg.selection, game.home_team, game.away_team
        )
        
        if is_home:
            # Home team with spread (e.g., -3.5)
            result = margin - line
            if result > 0:
                return "WON"
            elif result < 0:
                return "LOST"
            else:
                logger.info(f"calculate_spread_result: Push for home spread, game {game.id}, line={line}")
                return "PUSH"
        
        elif is_away:
            # Away team with spread (e.g., +3.5)
            result = -margin + line  # Equivalent to away_score + line - home_score
            if result > 0:
                return "WON"
            elif result < 0:
                return "LOST"
            else:
                logger.info(f"calculate_spread_result: Push for away spread, game {game.id}, line={line}")
                return "PUSH"
        
        # Selection doesn't match either team
        logger.warning(
            f"calculate_spread_result: Unmatched selection '{leg.selection}' "
            f"for game {game.id} (home: {game.home_team}, away: {game.away_team})"
        )
        return "VOID"
    
    @staticmethod
    def calculate_total_result(leg: ParlayLeg, game: Game) -> LegResult:
        """Calculate total (over/under) leg result.
        
        Rules:
        - total_points = home_score + away_score
        - If selection = over 46.5: total_points > 46.5 → WON
        - If selection = under 46.5: total_points < 46.5 → WON
        - Equals → PUSH
        
        Args:
            leg: ParlayLeg with market_type="totals" and line
            game: Game with status="FINAL" and scores
            
        Returns:
            "WON", "LOST", "PUSH", "VOID", or "PENDING"
        """
        # Input validation
        if not leg or not game:
            logger.warning("calculate_total_result: Missing leg or game")
            return "VOID"
        
        if game.status != "FINAL":
            return "PENDING"
        
        # Normalize and validate scores
        home_score = LegResultCalculator._normalize_score(game.home_score)
        away_score = LegResultCalculator._normalize_score(game.away_score)
        
        if home_score is None or away_score is None:
            logger.warning(
                f"calculate_total_result: Missing scores for game {game.id}, "
                f"home_score={game.home_score}, away_score={game.away_score}"
            )
            return "VOID"
        
        # Normalize and validate line
        line = LegResultCalculator._normalize_line(leg.line)
        if line is None:
            logger.warning(
                f"calculate_total_result: Missing or invalid line for leg {leg.id}, "
                f"line={leg.line}"
            )
            return "VOID"
        
        total_points = home_score + away_score
        
        if not leg.selection:
            logger.warning(f"calculate_total_result: Missing selection for leg {leg.id}")
            return "VOID"
        
        selection_lower = leg.selection.lower().strip()
        
        if "over" in selection_lower:
            if total_points > line:
                return "WON"
            elif total_points < line:
                return "LOST"
            else:
                logger.info(f"calculate_total_result: Push for over, game {game.id}, line={line}, total={total_points}")
                return "PUSH"
        
        elif "under" in selection_lower:
            if total_points < line:
                return "WON"
            elif total_points > line:
                return "LOST"
            else:
                logger.info(f"calculate_total_result: Push for under, game {game.id}, line={line}, total={total_points}")
                return "PUSH"
        
        # Selection doesn't contain "over" or "under"
        logger.warning(
            f"calculate_total_result: Invalid selection '{leg.selection}' "
            f"for leg {leg.id} (must contain 'over' or 'under')"
        )
        return "VOID"
