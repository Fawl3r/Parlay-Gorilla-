"""Test FREE-mode core analysis builders."""

import pytest
from app.services.analysis.builders.outcome_paths_builder import OutcomePathsBuilder
from app.services.analysis.builders.confidence_breakdown_builder import ConfidenceBreakdownBuilder
from app.services.analysis.builders.market_disagreement_builder import MarketDisagreementBuilder
from app.services.analysis.builders.portfolio_guidance_builder import PortfolioGuidanceBuilder


def test_outcome_paths_builder():
    """Test outcome paths builder produces valid probabilities."""
    odds_snapshot = {
        "home_implied_prob": 0.55,
        "away_implied_prob": 0.45,
        "home_spread_point": -3.5,
        "total_line": 44.5,
    }
    model_probs = {
        "home_win_prob": 0.55,
        "away_win_prob": 0.45,
    }
    
    result = OutcomePathsBuilder.build(
        odds_snapshot=odds_snapshot,
        model_probs=model_probs,
        spread=-3.5,
        total=44.5,
    )
    
    assert "home_control_script" in result
    assert "shootout_script" in result
    assert "variance_upset_script" in result
    
    # Probabilities should sum to ~1.0
    total_prob = (
        result["home_control_script"]["probability"] +
        result["shootout_script"]["probability"] +
        result["variance_upset_script"]["probability"]
    )
    assert abs(total_prob - 1.0) < 0.01, f"Probabilities sum to {total_prob}, expected ~1.0"
    
    # Each script dict (not the "explanation" string) should have required fields
    script_keys = ("home_control_script", "shootout_script", "variance_upset_script")
    for key in script_keys:
        script = result[key]
        assert "probability" in script
        assert "description" in script
        assert "recommended_angles" in script
        assert isinstance(script["recommended_angles"], list)


def test_confidence_breakdown_builder():
    """Test confidence breakdown builder produces valid scores."""
    market_probs = {
        "home_implied_prob": 0.55,
        "away_implied_prob": 0.45,
    }
    model_probs = {
        "home_win_prob": 0.55,
        "away_win_prob": 0.45,
        "ai_confidence": 65.0,
    }
    matchup_data = {
        "home_team_stats": {"offense": {"points_per_game": 24.5}},
        "away_team_stats": {"offense": {"points_per_game": 22.0}},
        "rest_days_home": 7,
        "rest_days_away": 6,
        "weather": {"affects_game": True},
    }
    odds_snapshot = {
        "home_ml": "-150",
        "away_ml": "+130",
    }
    
    result = ConfidenceBreakdownBuilder.build(
        market_probs=market_probs,
        model_probs=model_probs,
        matchup_data=matchup_data,
        odds_snapshot=odds_snapshot,
    )
    
    assert "market_agreement" in result
    assert "statistical_edge" in result
    assert "situational_edge" in result
    assert "data_quality" in result
    assert "confidence_total" in result
    
    # Check ranges
    assert 0 <= result["market_agreement"] <= 30
    assert 0 <= result["statistical_edge"] <= 30
    assert 0 <= result["situational_edge"] <= 20
    assert 0 <= result["data_quality"] <= 20
    assert 0 <= result["confidence_total"] <= 100
    
    # Total should be sum of components
    expected_total = (
        result["market_agreement"] +
        result["statistical_edge"] +
        result["situational_edge"] +
        result["data_quality"]
    )
    assert abs(result["confidence_total"] - expected_total) < 0.1


def test_confidence_breakdown_builder_with_canonical_stats_and_features():
    """Canonical/v2 stats + features should count as valid confidence inputs."""
    market_probs = {
        "home_implied_prob": 0.56,
        "away_implied_prob": 0.44,
    }
    model_probs = {
        "home_win_prob": 0.60,
        "away_win_prob": 0.40,
        "ai_confidence": 66.0,
    }
    matchup_data = {
        "home_team_stats": {
            "record": {"wins": 38, "losses": 22},
            "scoring": {"points_for_avg": 116.4, "points_against_avg": 109.5},
        },
        "away_team_stats": {
            "record": {"wins": 24, "losses": 36},
            "scoring": {"points_for_avg": 108.3, "points_against_avg": 115.9},
        },
        "home_features": {
            "strength": {"net_strength": 2.2},
            "form": {"form_score_5": 0.45},
        },
        "away_features": {
            "strength": {"net_strength": -1.4},
            "form": {"form_score_5": -0.10},
        },
        "home_data_quality": {"trust_score": 0.75, "warnings": []},
        "away_data_quality": {"trust_score": 0.65, "warnings": []},
        "home_injuries": {"impact_scores": {"overall_impact": 0.15}},
        "away_injuries": {"impact_scores": {"overall_impact": 0.10}},
    }
    odds_snapshot = {
        "home_ml": "-145",
        "away_ml": "+125",
    }

    result = ConfidenceBreakdownBuilder.build(
        market_probs=market_probs,
        model_probs=model_probs,
        matchup_data=matchup_data,
        odds_snapshot=odds_snapshot,
    )

    assert result["statistical_edge"] > 10
    assert result["data_quality"] >= 10


def test_market_disagreement_builder():
    """Test market disagreement builder."""
    odds_snapshot = {
        "home_spread_point": -3.5,
        "total_line": 44.5,
        "home_implied_prob": 0.55,
        "away_implied_prob": 0.45,
    }
    model_probs = {
        "home_win_prob": 0.60,  # Model disagrees with market
        "away_win_prob": 0.40,
    }
    
    result = MarketDisagreementBuilder.build(
        odds_snapshot=odds_snapshot,
        model_probs=model_probs,
        markets=None,  # No multiple books for this test
    )
    
    assert "spread_variance" in result
    assert "total_variance" in result
    assert "books_split_summary" in result
    assert "flag" in result
    
    assert result["spread_variance"] in ["low", "med", "high"]
    assert result["total_variance"] in ["low", "med", "high"]
    assert result["flag"] in ["consensus", "volatile", "sharp_vs_public"]


def test_portfolio_guidance_builder():
    """Test portfolio guidance builder."""
    spread_pick = {
        "pick": "Home Team -3.5",
        "confidence": 72.0,
        "rationale": "Test rationale",
    }
    total_pick = {
        "pick": "Over 44.5",
        "confidence": 68.0,
        "rationale": "Test rationale",
    }
    same_game_parlays = {
        "safe_3_leg": {
            "legs": [{"pick": "Test"}],
        },
        "balanced_6_leg": {
            "legs": [{"pick": "Test"}],
        },
    }
    
    result = PortfolioGuidanceBuilder.build(
        spread_pick=spread_pick,
        total_pick=total_pick,
        same_game_parlays=same_game_parlays,
        confidence_total=75.0,
    )
    
    assert "low_risk" in result
    assert "medium_risk" in result
    assert "high_risk" in result
    assert "exposure_note" in result
    
    assert isinstance(result["low_risk"], list)
    assert isinstance(result["medium_risk"], list)
    assert isinstance(result["high_risk"], list)
    assert "ai_spread_pick" in result["low_risk"]
    assert "ai_total_pick" in result["low_risk"]
