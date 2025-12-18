from __future__ import annotations

from app.services.probability_engine_impl.candidate_leg_service import CandidateLegService


def test_market_move_score_h2h_direction():
    score_home = CandidateLegService._score_market_move(
        market_type="h2h",
        outcome="home",
        home_team="A",
        away_team="B",
        movement={"home_implied_prob_delta": 0.03, "away_implied_prob_delta": -0.03},
    )
    assert score_home > 0

    score_away = CandidateLegService._score_market_move(
        market_type="h2h",
        outcome="away",
        home_team="A",
        away_team="B",
        movement={"home_implied_prob_delta": 0.03, "away_implied_prob_delta": -0.03},
    )
    assert score_away < 0


def test_market_move_score_spreads_home_alignment():
    # Negative delta_points => home spread moved more negative => aligned with home side.
    score_home = CandidateLegService._score_market_move(
        market_type="spreads",
        outcome="Seattle Seahawks -2.5",
        home_team="Seattle Seahawks",
        away_team="Los Angeles Rams",
        movement={"spread_delta_points": -1.0},
    )
    assert score_home > 0

    score_away = CandidateLegService._score_market_move(
        market_type="spreads",
        outcome="Los Angeles Rams +2.5",
        home_team="Seattle Seahawks",
        away_team="Los Angeles Rams",
        movement={"spread_delta_points": -1.0},
    )
    assert score_away < 0




