"""Unit tests for LegResultCalculator settlement logic."""

from __future__ import annotations

import pytest
from decimal import Decimal
from datetime import datetime, timezone

from app.models.game import Game
from app.models.parlay_leg import ParlayLeg
from app.services.settlement.leg_result_calculator import LegResultCalculator


def _create_game(
    home_team: str = "Home Team",
    away_team: str = "Away Team",
    home_score: int | None = None,
    away_score: int | None = None,
    status: str = "FINAL",
) -> Game:
    """Helper to create a Game object for testing."""
    game = Game(
        external_game_id="test_game_1",
        sport="NFL",
        home_team=home_team,
        away_team=away_team,
        start_time=datetime.now(timezone.utc),
        status=status,
        home_score=home_score,
        away_score=away_score,
    )
    return game


def _create_leg(
    market_type: str,
    selection: str,
    line: Decimal | float | None = None,
) -> ParlayLeg:
    """Helper to create a ParlayLeg object for testing."""
    leg = ParlayLeg(
        market_type=market_type,
        selection=selection,
        line=Decimal(str(line)) if line is not None else None,
    )
    return leg


class TestMoneylineCalculator:
    """Tests for moneyline (h2h) leg calculations."""

    def test_home_team_wins(self):
        """Home team selection wins when home score > away score."""
        game = _create_game(home_score=28, away_score=14)
        leg = _create_leg("h2h", "Home Team")
        
        result = LegResultCalculator.calculate_moneyline_result(leg, game)
        assert result == "WON"

    def test_home_team_loses(self):
        """Home team selection loses when home score < away score."""
        game = _create_game(home_score=14, away_score=28)
        leg = _create_leg("h2h", "Home Team")
        
        result = LegResultCalculator.calculate_moneyline_result(leg, game)
        assert result == "LOST"

    def test_away_team_wins(self):
        """Away team selection wins when away score > home score."""
        game = _create_game(home_score=14, away_score=28)
        leg = _create_leg("h2h", "Away Team")
        
        result = LegResultCalculator.calculate_moneyline_result(leg, game)
        assert result == "WON"

    def test_away_team_loses(self):
        """Away team selection loses when away score < home score."""
        game = _create_game(home_score=28, away_score=14)
        leg = _create_leg("h2h", "Away Team")
        
        result = LegResultCalculator.calculate_moneyline_result(leg, game)
        assert result == "LOST"

    def test_tie_home_selection_loses(self):
        """Tie game results in LOST for moneyline (per current business rules)."""
        game = _create_game(home_score=21, away_score=21)
        leg = _create_leg("h2h", "Home Team")
        
        result = LegResultCalculator.calculate_moneyline_result(leg, game)
        assert result == "LOST"

    def test_tie_away_selection_loses(self):
        """Tie game results in LOST for away team selection."""
        game = _create_game(home_score=21, away_score=21)
        leg = _create_leg("h2h", "Away Team")
        
        result = LegResultCalculator.calculate_moneyline_result(leg, game)
        assert result == "LOST"

    def test_home_keyword_selection(self):
        """Selection "home" keyword matches home team."""
        game = _create_game(home_score=28, away_score=14)
        leg = _create_leg("h2h", "home")
        
        result = LegResultCalculator.calculate_moneyline_result(leg, game)
        assert result == "WON"

    def test_away_keyword_selection(self):
        """Selection "away" keyword matches away team."""
        game = _create_game(home_score=14, away_score=28)
        leg = _create_leg("h2h", "away")
        
        result = LegResultCalculator.calculate_moneyline_result(leg, game)
        assert result == "WON"

    def test_case_insensitive_team_matching(self):
        """Team name matching is case-insensitive."""
        game = _create_game(home_team="Kansas City Chiefs", away_team="Buffalo Bills", home_score=28, away_score=14)
        leg = _create_leg("h2h", "kansas city chiefs")
        
        result = LegResultCalculator.calculate_moneyline_result(leg, game)
        assert result == "WON"

    def test_non_final_game_returns_pending(self):
        """Non-FINAL game status returns PENDING."""
        game = _create_game(home_score=28, away_score=14, status="LIVE")
        leg = _create_leg("h2h", "Home Team")
        
        result = LegResultCalculator.calculate_moneyline_result(leg, game)
        assert result == "PENDING"

    def test_null_home_score_returns_void(self):
        """Missing home score returns VOID."""
        game = _create_game(home_score=None, away_score=14)
        leg = _create_leg("h2h", "Home Team")
        
        result = LegResultCalculator.calculate_moneyline_result(leg, game)
        assert result == "VOID"

    def test_null_away_score_returns_void(self):
        """Missing away score returns VOID."""
        game = _create_game(home_score=28, away_score=None)
        leg = _create_leg("h2h", "Home Team")
        
        result = LegResultCalculator.calculate_moneyline_result(leg, game)
        assert result == "VOID"

    def test_unmatched_selection_returns_void(self):
        """Selection that doesn't match either team returns VOID."""
        game = _create_game(home_score=28, away_score=14)
        leg = _create_leg("h2h", "Unknown Team")
        
        result = LegResultCalculator.calculate_moneyline_result(leg, game)
        assert result == "VOID"


class TestSpreadCalculator:
    """Tests for spread leg calculations."""

    def test_home_team_covers_negative_spread(self):
        """Home team covers when margin > spread line."""
        game = _create_game(home_score=28, away_score=14)  # Margin: +14
        leg = _create_leg("spreads", "Home Team", line=-3.5)
        
        result = LegResultCalculator.calculate_spread_result(leg, game)
        assert result == "WON"

    def test_home_team_fails_to_cover_negative_spread(self):
        """Home team fails to cover when margin < spread line."""
        game = _create_game(home_score=21, away_score=20)  # Margin: +1
        leg = _create_leg("spreads", "Home Team", line=-3.5)
        
        result = LegResultCalculator.calculate_spread_result(leg, game)
        assert result == "LOST"

    def test_home_team_spread_push(self):
        """Home team spread pushes when margin exactly equals line."""
        game = _create_game(home_score=24, away_score=20)  # Margin: +4
        leg = _create_leg("spreads", "Home Team", line=-4.0)
        
        result = LegResultCalculator.calculate_spread_result(leg, game)
        assert result == "PUSH"

    def test_away_team_covers_positive_spread(self):
        """Away team covers when away_score + spread > home_score."""
        game = _create_game(home_score=21, away_score=20)  # Margin: -1, but away +3.5 = +2.5
        leg = _create_leg("spreads", "Away Team", line=3.5)
        
        result = LegResultCalculator.calculate_spread_result(leg, game)
        assert result == "WON"

    def test_away_team_fails_to_cover_positive_spread(self):
        """Away team fails to cover when away_score + spread < home_score."""
        game = _create_game(home_score=28, away_score=14)  # Margin: +14, away +3.5 = +17.5 < 28
        leg = _create_leg("spreads", "Away Team", line=3.5)
        
        result = LegResultCalculator.calculate_spread_result(leg, game)
        assert result == "LOST"

    def test_away_team_spread_push(self):
        """Away team spread pushes when result exactly equals line."""
        game = _create_game(home_score=24, away_score=20)  # Margin: -4, away +4 = 0
        leg = _create_leg("spreads", "Away Team", line=4.0)
        
        result = LegResultCalculator.calculate_spread_result(leg, game)
        assert result == "PUSH"

    def test_spread_non_final_returns_pending(self):
        """Non-FINAL game returns PENDING for spread."""
        game = _create_game(home_score=28, away_score=14, status="LIVE")
        leg = _create_leg("spreads", "Home Team", line=-3.5)
        
        result = LegResultCalculator.calculate_spread_result(leg, game)
        assert result == "PENDING"

    def test_spread_null_scores_returns_void(self):
        """Missing scores return VOID for spread."""
        game = _create_game(home_score=None, away_score=14)
        leg = _create_leg("spreads", "Home Team", line=-3.5)
        
        result = LegResultCalculator.calculate_spread_result(leg, game)
        assert result == "VOID"

    def test_spread_missing_line_returns_void(self):
        """Missing line returns VOID for spread."""
        game = _create_game(home_score=28, away_score=14)
        leg = _create_leg("spreads", "Home Team", line=None)
        
        result = LegResultCalculator.calculate_spread_result(leg, game)
        assert result == "VOID"

    def test_spread_home_keyword_selection(self):
        """Spread selection with "home" keyword works."""
        game = _create_game(home_score=28, away_score=14)
        leg = _create_leg("spreads", "home", line=-3.5)
        
        result = LegResultCalculator.calculate_spread_result(leg, game)
        assert result == "WON"

    def test_spread_away_keyword_selection(self):
        """Spread selection with "away" keyword works."""
        game = _create_game(home_score=14, away_score=28)
        leg = _create_leg("spreads", "away", line=3.5)
        
        result = LegResultCalculator.calculate_spread_result(leg, game)
        assert result == "WON"


class TestTotalsCalculator:
    """Tests for totals (over/under) leg calculations."""

    def test_over_wins(self):
        """Over selection wins when total points > line."""
        game = _create_game(home_score=28, away_score=24)  # Total: 52
        leg = _create_leg("totals", "over 46.5", line=46.5)
        
        result = LegResultCalculator.calculate_total_result(leg, game)
        assert result == "WON"

    def test_over_loses(self):
        """Over selection loses when total points < line."""
        game = _create_game(home_score=14, away_score=10)  # Total: 24
        leg = _create_leg("totals", "over 46.5", line=46.5)
        
        result = LegResultCalculator.calculate_total_result(leg, game)
        assert result == "LOST"

    def test_over_push(self):
        """Over selection pushes when total points exactly equals line."""
        game = _create_game(home_score=24, away_score=22)  # Total: 46
        leg = _create_leg("totals", "over 46.0", line=46.0)
        
        result = LegResultCalculator.calculate_total_result(leg, game)
        assert result == "PUSH"

    def test_under_wins(self):
        """Under selection wins when total points < line."""
        game = _create_game(home_score=14, away_score=10)  # Total: 24
        leg = _create_leg("totals", "under 46.5", line=46.5)
        
        result = LegResultCalculator.calculate_total_result(leg, game)
        assert result == "WON"

    def test_under_loses(self):
        """Under selection loses when total points > line."""
        game = _create_game(home_score=28, away_score=24)  # Total: 52
        leg = _create_leg("totals", "under 46.5", line=46.5)
        
        result = LegResultCalculator.calculate_total_result(leg, game)
        assert result == "LOST"

    def test_under_push(self):
        """Under selection pushes when total points exactly equals line."""
        game = _create_game(home_score=24, away_score=22)  # Total: 46
        leg = _create_leg("totals", "under 46.0", line=46.0)
        
        result = LegResultCalculator.calculate_total_result(leg, game)
        assert result == "PUSH"

    def test_totals_non_final_returns_pending(self):
        """Non-FINAL game returns PENDING for totals."""
        game = _create_game(home_score=28, away_score=24, status="LIVE")
        leg = _create_leg("totals", "over 46.5", line=46.5)
        
        result = LegResultCalculator.calculate_total_result(leg, game)
        assert result == "PENDING"

    def test_totals_null_scores_returns_void(self):
        """Missing scores return VOID for totals."""
        game = _create_game(home_score=None, away_score=24)
        leg = _create_leg("totals", "over 46.5", line=46.5)
        
        result = LegResultCalculator.calculate_total_result(leg, game)
        assert result == "VOID"

    def test_totals_missing_line_returns_void(self):
        """Missing line returns VOID for totals."""
        game = _create_game(home_score=28, away_score=24)
        leg = _create_leg("totals", "over 46.5", line=None)
        
        result = LegResultCalculator.calculate_total_result(leg, game)
        assert result == "VOID"

    def test_totals_case_insensitive_selection(self):
        """Totals selection matching is case-insensitive."""
        game = _create_game(home_score=28, away_score=24)  # Total: 52
        leg = _create_leg("totals", "OVER 46.5", line=46.5)
        
        result = LegResultCalculator.calculate_total_result(leg, game)
        assert result == "WON"

    def test_totals_invalid_selection_returns_void(self):
        """Selection without 'over' or 'under' returns VOID."""
        game = _create_game(home_score=28, away_score=24)
        leg = _create_leg("totals", "total 46.5", line=46.5)
        
        result = LegResultCalculator.calculate_total_result(leg, game)
        assert result == "VOID"


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_decimal_line_values(self):
        """Line values as Decimal type work correctly."""
        game = _create_game(home_score=28, away_score=14)
        leg = _create_leg("spreads", "Home Team", line=Decimal("-3.5"))
        
        result = LegResultCalculator.calculate_spread_result(leg, game)
        assert result == "WON"

    def test_float_line_values(self):
        """Line values as float type work correctly."""
        game = _create_game(home_score=28, away_score=24)
        leg = _create_leg("totals", "over 46.5", line=46.5)
        
        result = LegResultCalculator.calculate_total_result(leg, game)
        assert result == "WON"

    def test_zero_scores(self):
        """Zero scores are handled correctly."""
        game = _create_game(home_score=0, away_score=0)
        leg = _create_leg("h2h", "Home Team")
        
        result = LegResultCalculator.calculate_moneyline_result(leg, game)
        assert result == "LOST"  # Tie = LOST per business rules

    def test_very_large_scores(self):
        """Very large scores are handled correctly."""
        game = _create_game(home_score=150, away_score=120)
        leg = _create_leg("h2h", "Home Team")
        
        result = LegResultCalculator.calculate_moneyline_result(leg, game)
        assert result == "WON"

    def test_negative_spread_away_team(self):
        """Away team with negative spread (favorite) works."""
        game = _create_game(home_score=14, away_score=28)  # Away wins by 14
        leg = _create_leg("spreads", "Away Team", line=-7.0)  # Away -7
        
        result = LegResultCalculator.calculate_spread_result(leg, game)
        assert result == "WON"  # Away wins by 14, covers -7

    def test_whitespace_in_selection(self):
        """Selections with whitespace are handled correctly."""
        game = _create_game(home_team="Kansas City Chiefs", home_score=28, away_score=14)
        leg = _create_leg("h2h", "  Kansas City Chiefs  ")
        
        result = LegResultCalculator.calculate_moneyline_result(leg, game)
        assert result == "WON"
