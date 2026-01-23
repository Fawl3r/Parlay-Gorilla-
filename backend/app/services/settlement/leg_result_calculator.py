"""Leg result calculator for settlement rules."""

from __future__ import annotations

from typing import Literal
from decimal import Decimal

from app.models.game import Game
from app.models.parlay_leg import ParlayLeg


LegResult = Literal["WON", "LOST", "PUSH", "VOID"]


class LegResultCalculator:
    """Calculate leg results based on game outcomes."""
    
    @staticmethod
    def calculate_moneyline_result(leg: ParlayLeg, game: Game) -> LegResult:
        """Calculate moneyline (h2h) leg result.
        
        Rules:
        - If selected team score > opponent at FINAL → WON
        - Otherwise → LOST
        """
        if game.status != "FINAL":
            return "PENDING"
        
        if game.home_score is None or game.away_score is None:
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
        """
        if game.status != "FINAL":
            return "PENDING"
        
        if game.home_score is None or game.away_score is None:
            return "VOID"
        
        if leg.line is None:
            return "VOID"
        
        line = float(leg.line)
        margin = game.home_score - game.away_score
        
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
            # Home team with spread (e.g., -3.5)
            result = margin - line
            if result > 0:
                return "WON"
            elif result < 0:
                return "LOST"
            else:
                return "PUSH"
        
        elif is_away:
            # Away team with spread (e.g., +3.5)
            result = -margin + line  # Equivalent to away_score + line - home_score
            if result > 0:
                return "WON"
            elif result < 0:
                return "LOST"
            else:
                return "PUSH"
        
        return "VOID"
    
    @staticmethod
    def calculate_total_result(leg: ParlayLeg, game: Game) -> LegResult:
        """Calculate total (over/under) leg result.
        
        Rules:
        - total_points = home_score + away_score
        - If selection = over 46.5: total_points > 46.5 → WON
        - If selection = under 46.5: total_points < 46.5 → WON
        - Equals → PUSH
        """
        if game.status != "FINAL":
            return "PENDING"
        
        if game.home_score is None or game.away_score is None:
            return "VOID"
        
        if leg.line is None:
            return "VOID"
        
        total_points = game.home_score + game.away_score
        line = float(leg.line)
        
        selection_lower = leg.selection.lower().strip()
        
        if "over" in selection_lower:
            if total_points > line:
                return "WON"
            elif total_points < line:
                return "LOST"
            else:
                return "PUSH"
        
        elif "under" in selection_lower:
            if total_points < line:
                return "WON"
            elif total_points > line:
                return "LOST"
            else:
                return "PUSH"
        
        return "VOID"
