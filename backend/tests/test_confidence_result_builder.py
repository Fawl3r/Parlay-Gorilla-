"""Tests for ConfidenceResultBuilder and availability rules."""

import pytest
from app.services.analysis.builders.confidence_result_builder import ConfidenceResultBuilder
from app.services.confidence.rules import is_weather_applicable


def test_confidence_available_when_has_stat_plus_quality_and_market_or_situational():
    """Availability requires (statistical + data_quality) and at least one of (market or situational)."""
    breakdown = {
        "market_agreement": 10.0,
        "statistical_edge": 15.0,
        "situational_edge": 5.0,
        "data_quality": 10.0,
        "confidence_total": 40.0,
    }
    result = ConfidenceResultBuilder.build(confidence_breakdown=breakdown, sport="nfl")
    assert result.confidence_available is True
    assert result.confidence_score == 40.0
    assert result.components is not None
    assert result.blockers == []


def test_confidence_unavailable_when_market_and_situational_both_zero():
    """When market and situational are both 0, confidence is unavailable."""
    breakdown = {
        "market_agreement": 0.0,
        "statistical_edge": 15.0,
        "situational_edge": 0.0,
        "data_quality": 10.0,
        "confidence_total": 25.0,
    }
    result = ConfidenceResultBuilder.build(confidence_breakdown=breakdown, sport="nba")
    assert result.confidence_available is False
    assert result.confidence_score is None
    assert "market_data_unavailable" in [b.value for b in result.blockers]
    assert "situational_data_unavailable" in [b.value for b in result.blockers]


def test_confidence_unavailable_when_stat_plus_quality_too_low():
    """When statistical + data_quality < 5, confidence is unavailable."""
    breakdown = {
        "market_agreement": 10.0,
        "statistical_edge": 2.0,
        "situational_edge": 2.0,
        "data_quality": 2.0,
        "confidence_total": 16.0,
    }
    result = ConfidenceResultBuilder.build(confidence_breakdown=breakdown)
    assert result.confidence_available is False
    assert result.confidence_score is None


def test_confidence_unavailable_when_data_quality_zero_quality_signals_missing():
    """When data_quality is 0 (quality signals missing), mark DATA_QUALITY_TOO_LOW and unavailable."""
    breakdown = {
        "market_agreement": 8.0,
        "statistical_edge": 6.0,
        "situational_edge": 2.0,
        "data_quality": 0.0,
        "confidence_total": 16.0,
    }
    result = ConfidenceResultBuilder.build(confidence_breakdown=breakdown)
    assert result.confidence_available is False
    assert result.confidence_score is None
    assert "data_quality_too_low" in [b.value for b in result.blockers]


def test_weather_blocker_added_but_availability_unchanged_when_only_weather_missing():
    """For outdoor sport, missing weather adds WEATHER_UNAVAILABLE blocker but does not fail availability."""
    breakdown = {
        "market_agreement": 10.0,
        "statistical_edge": 8.0,
        "situational_edge": 2.0,
        "data_quality": 5.0,
        "confidence_total": 25.0,
    }
    result = ConfidenceResultBuilder.build(
        confidence_breakdown=breakdown,
        sport="nfl",
        matchup_data={},  # no weather
    )
    assert result.confidence_available is True
    assert result.confidence_score == 25.0
    assert "weather_unavailable" in [b.value for b in result.blockers]


def test_weather_not_applicable_for_indoor_sports():
    """NBA, WNBA, NHL are indoor; weather not applicable."""
    assert is_weather_applicable("NBA") is False
    assert is_weather_applicable("WNBA") is False
    assert is_weather_applicable("NHL") is False


def test_weather_applicable_for_outdoor_sports():
    """NFL, MLB, MLS, EPL are outdoor; weather applicable."""
    assert is_weather_applicable("NFL") is True
    assert is_weather_applicable("MLB") is True
    assert is_weather_applicable("MLS") is True
    assert is_weather_applicable("EPL") is True


def test_weather_not_applicable_when_venue_is_dome():
    """When venue is dome, weather not applicable even for NFL."""
    assert is_weather_applicable("NFL", venue_is_dome=True) is False


def test_one_team_trust_does_not_zero_data_quality_in_breakdown():
    """Breakdown builder: one team with trust_score should not zero data_quality (avg over present only)."""
    from app.services.analysis.builders.confidence_breakdown_builder import ConfidenceBreakdownBuilder

    # Only home has trust_score; away missing
    matchup_data = {
        "home_data_quality": {"trust_score": 0.8, "warnings": []},
        "away_data_quality": None,
        "home_stats": {},
        "away_stats": {},
        "odds_snapshot": {},
        "home_injuries": {},
        "away_injuries": {},
    }
    market_probs = {"home_implied_prob": 0.52, "away_implied_prob": 0.48}
    model_probs = {"home_win_prob": 0.55, "away_win_prob": 0.45}
    odds_snapshot = {"home_ml": -110, "away_ml": -110}

    breakdown = ConfidenceBreakdownBuilder.build(
        market_probs=market_probs,
        model_probs=model_probs,
        matchup_data=matchup_data,
        odds_snapshot=odds_snapshot,
    )
    dq = breakdown.get("data_quality", 0)
    assert dq >= 1.0, "data_quality should not be 0 when one team has trust_score (use present-only average)"
