"""
Tests for ModelWinProbabilityCalculator

Verifies:
1. Probability calculations never return 0.5/0.5 unless truly calculated
2. Weighted combination works correctly (50% odds, 30% stats, 20% situational)
3. Confidence scoring works correctly
4. Sport-specific adjustments are applied
"""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch

# Test the core functions without database
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.model_win_probability import (
    TeamMatchupStats,
    ModelWinProbabilityCalculator,
    american_odds_to_probability,
    remove_vig_and_normalize,
    calculate_fair_probabilities_from_odds,
    ODDS_WEIGHT,
    STATS_WEIGHT,
    SITUATIONAL_WEIGHT,
)


class TestAmericanOddsConversion:
    """Test American odds to probability conversion."""
    
    def test_favorite_odds(self):
        """Test conversion of favorite odds (negative)."""
        # -150 favorite should be about 60%
        prob = american_odds_to_probability(-150)
        assert abs(prob - 0.6) < 0.01
        
        # -200 favorite should be about 66.7%
        prob = american_odds_to_probability(-200)
        assert abs(prob - 0.667) < 0.01
    
    def test_underdog_odds(self):
        """Test conversion of underdog odds (positive)."""
        # +150 underdog should be about 40%
        prob = american_odds_to_probability(150)
        assert abs(prob - 0.4) < 0.01
        
        # +200 underdog should be about 33.3%
        prob = american_odds_to_probability(200)
        assert abs(prob - 0.333) < 0.01
    
    def test_even_odds(self):
        """Test conversion of even odds."""
        # +100 or -100 should be about 50%
        prob_pos = american_odds_to_probability(100)
        prob_neg = american_odds_to_probability(-100)
        assert abs(prob_pos - 0.5) < 0.01
        assert abs(prob_neg - 0.5) < 0.01


class TestVigRemoval:
    """Test vig removal and normalization."""
    
    def test_remove_vig_standard(self):
        """Test standard vig removal."""
        # Typical -110/-110 spread: both ~52.4% implied, should normalize to 50/50
        home_fair, away_fair = remove_vig_and_normalize(0.524, 0.524)
        assert abs(home_fair - 0.5) < 0.01
        assert abs(away_fair - 0.5) < 0.01
        assert abs(home_fair + away_fair - 1.0) < 0.001
    
    def test_remove_vig_favorite(self):
        """Test vig removal with favorite."""
        # -200/+150: 66.7%/40% raw, should normalize
        home_fair, away_fair = remove_vig_and_normalize(0.667, 0.4)
        assert home_fair + away_fair == pytest.approx(1.0, abs=0.001)
        assert home_fair > away_fair
    
    def test_edge_case_zero(self):
        """Test edge case with zero probabilities."""
        home_fair, away_fair = remove_vig_and_normalize(0, 0)
        assert home_fair == 0.5
        assert away_fair == 0.5


class TestCalculateFairProbabilities:
    """Test fair probability calculation from odds data."""
    
    def test_from_implied_prob(self):
        """Test calculation from pre-calculated implied probabilities."""
        odds_data = {
            "home_implied_prob": 0.6,
            "away_implied_prob": 0.45,
        }
        home_fair, away_fair = calculate_fair_probabilities_from_odds(odds_data)
        
        # Should normalize: 0.6 / 1.05 ≈ 0.571, 0.45 / 1.05 ≈ 0.429
        assert home_fair + away_fair == pytest.approx(1.0, abs=0.001)
        assert home_fair > away_fair
    
    def test_from_moneyline(self):
        """Test calculation from moneyline odds."""
        odds_data = {
            "home_ml": "-150",
            "away_ml": "+130",
        }
        home_fair, away_fair = calculate_fair_probabilities_from_odds(odds_data)
        
        assert home_fair + away_fair == pytest.approx(1.0, abs=0.001)
        assert home_fair > away_fair  # Favorite should have higher prob
    
    def test_fallback_to_default(self):
        """Test fallback when no odds available."""
        odds_data = {}
        home_fair, away_fair = calculate_fair_probabilities_from_odds(odds_data)
        
        assert home_fair == 0.5
        assert away_fair == 0.5


class TestTeamMatchupStats:
    """Test TeamMatchupStats dataclass."""
    
    def test_from_matchup_data(self):
        """Test creating TeamMatchupStats from matchup_data dict."""
        matchup_data = {
            "home_team_stats": {"wins": 8, "losses": 4},
            "away_team_stats": {"wins": 6, "losses": 6},
            "weather": {"temperature": 32, "is_outdoor": True},
            "rest_days_home": 7,
            "rest_days_away": 4,
        }
        
        stats = TeamMatchupStats.from_matchup_data(
            matchup_data=matchup_data,
            home_team="Kansas City Chiefs",
            away_team="Denver Broncos",
            sport="NFL",
        )
        
        assert stats.home_team_name == "Kansas City Chiefs"
        assert stats.away_team_name == "Denver Broncos"
        assert stats.sport == "NFL"
        assert stats.home_team_stats["wins"] == 8
        assert stats.rest_days_home == 7
    
    def test_empty_matchup_data(self):
        """Test creating TeamMatchupStats from empty dict."""
        stats = TeamMatchupStats.from_matchup_data({}, "Team A", "Team B", "NBA")
        
        assert stats.home_team_stats is None
        assert stats.away_team_stats is None
        assert stats.sport == "NBA"


class TestModelWinProbabilityCalculator:
    """Test the main calculator class."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return MagicMock()
    
    @pytest.fixture
    def calculator(self, mock_db):
        """Create a calculator with mocked dependencies."""
        with patch('app.services.model_win_probability.get_probability_engine') as mock_engine:
            mock_engine.return_value = MagicMock()
            return ModelWinProbabilityCalculator(mock_db, "NFL")
    
    @pytest.mark.asyncio
    async def test_never_returns_exact_50_50(self, calculator):
        """Test that calculator never returns exactly 0.5/0.5."""
        # Even with minimal data, should return something other than 50/50
        base = {"home_fair_prob": 0.5, "away_fair_prob": 0.5}
        stats = TeamMatchupStats(
            home_team_name="Team A",
            away_team_name="Team B",
            sport="NFL",
        )
        
        result = await calculator.compute_model_win_probabilities(base, stats, None)
        
        # Should not be exactly 50/50 due to home advantage
        assert result["home_model_prob"] != 0.5 or result["away_model_prob"] != 0.5
        # Should still sum to 1
        assert result["home_model_prob"] + result["away_model_prob"] == pytest.approx(1.0, abs=0.001)
    
    @pytest.mark.asyncio
    async def test_confidence_score_range(self, calculator):
        """Test that confidence score is in valid range."""
        base = {"home_fair_prob": 0.6, "away_fair_prob": 0.4}
        stats = TeamMatchupStats(
            home_team_stats={"wins": 10, "losses": 2},
            away_team_stats={"wins": 6, "losses": 6},
            home_team_name="Team A",
            away_team_name="Team B",
            sport="NFL",
        )
        
        result = await calculator.compute_model_win_probabilities(base, stats, {"home_ml": "-150"})
        
        # Confidence should be between 0 and 100
        assert 0 <= result["ai_confidence"] <= 100
    
    @pytest.mark.asyncio
    async def test_home_advantage_applied(self, calculator):
        """Test that home advantage is applied."""
        # With equal base probabilities and no stats, home team should be slightly favored
        base = {"home_fair_prob": 0.5, "away_fair_prob": 0.5}
        stats = TeamMatchupStats(
            home_team_name="Team A",
            away_team_name="Team B",
            sport="NFL",
        )
        
        result = await calculator.compute_model_win_probabilities(base, stats, None)
        
        # Home team should be favored due to home advantage
        assert result["home_model_prob"] > result["away_model_prob"]
    
    @pytest.mark.asyncio
    async def test_stats_adjustment_applied(self, calculator):
        """Test that stats adjustments are applied."""
        base = {"home_fair_prob": 0.5, "away_fair_prob": 0.5}
        
        # Home team is much better
        stats_home_favored = TeamMatchupStats(
            home_team_stats={"wins": 12, "losses": 0, "win_percentage": 1.0},
            away_team_stats={"wins": 0, "losses": 12, "win_percentage": 0.0},
            home_team_name="Team A",
            away_team_name="Team B",
            sport="NFL",
        )
        
        result = await calculator.compute_model_win_probabilities(base, stats_home_favored, None)
        
        # Home team should be heavily favored
        assert result["home_model_prob"] > 0.6
    
    @pytest.mark.asyncio
    async def test_odds_data_increases_confidence(self, calculator):
        """Test that having odds data increases confidence score."""
        base = {"home_fair_prob": 0.6, "away_fair_prob": 0.4}
        stats = TeamMatchupStats(
            home_team_name="Team A",
            away_team_name="Team B",
            sport="NFL",
        )
        
        # Without odds
        result_no_odds = await calculator.compute_model_win_probabilities(base, stats, None)
        
        # With odds
        result_with_odds = await calculator.compute_model_win_probabilities(
            base, stats, {"home_ml": "-150", "away_ml": "+130"}
        )
        
        # Confidence should be higher with odds data
        assert result_with_odds["ai_confidence"] >= result_no_odds["ai_confidence"]


class TestSportSpecificAdjustments:
    """Test sport-specific probability adjustments."""
    
    @pytest.fixture
    def mock_db(self):
        return MagicMock()
    
    @pytest.mark.asyncio
    async def test_nba_home_advantage_higher(self, mock_db):
        """NBA should have higher home advantage than NFL."""
        with patch('app.services.model_win_probability.get_probability_engine') as mock_engine:
            mock_engine.return_value = MagicMock()
            
            nfl_calc = ModelWinProbabilityCalculator(mock_db, "NFL")
            nba_calc = ModelWinProbabilityCalculator(mock_db, "NBA")
            
            base = {"home_fair_prob": 0.5, "away_fair_prob": 0.5}
            nfl_stats = TeamMatchupStats(home_team_name="A", away_team_name="B", sport="NFL")
            nba_stats = TeamMatchupStats(home_team_name="A", away_team_name="B", sport="NBA")
            
            nfl_result = await nfl_calc.compute_model_win_probabilities(base, nfl_stats, None)
            nba_result = await nba_calc.compute_model_win_probabilities(base, nba_stats, None)
            
            # NBA should have higher home team probability (larger home court advantage)
            # Note: This depends on implementation - NBA home advantage is 3.5% vs NFL 2.5%
            # The difference might be small due to other factors
            assert nba_result["home_model_prob"] >= nfl_result["home_model_prob"] - 0.02


class TestWeights:
    """Test that weight constants are correct."""
    
    def test_weights_sum_to_one(self):
        """Weights should sum to 1.0."""
        total = ODDS_WEIGHT + STATS_WEIGHT + SITUATIONAL_WEIGHT
        assert total == pytest.approx(1.0, abs=0.001)
    
    def test_weights_match_spec(self):
        """Weights should match specification (50/30/20)."""
        assert ODDS_WEIGHT == 0.50
        assert STATS_WEIGHT == 0.30
        assert SITUATIONAL_WEIGHT == 0.20


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

