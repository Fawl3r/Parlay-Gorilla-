from unittest.mock import MagicMock, patch

import pytest

from app.services.model_win_probability import ModelWinProbabilityCalculator, TeamMatchupStats


@pytest.fixture
def calculator():
    with patch("app.services.model_win_probability.get_probability_engine") as mock_engine:
        mock_engine.return_value = MagicMock()
        yield ModelWinProbabilityCalculator(MagicMock(), "NFL")


@pytest.mark.asyncio
async def test_weather_adjustment_infers_impact_when_flag_missing(calculator):
    base = {"home_fair_prob": 0.5, "away_fair_prob": 0.5}

    baseline = await calculator.compute_model_win_probabilities(
        base,
        TeamMatchupStats(home_team_name="Home", away_team_name="Away", sport="NFL"),
        None,
    )
    weather_heavy = await calculator.compute_model_win_probabilities(
        base,
        TeamMatchupStats(
            weather={
                "is_outdoor": True,
                "temperature": 24,
                "wind_speed": 26,
                "precipitation": 1.2,
            },
            home_team_name="Home",
            away_team_name="Away",
            sport="NFL",
        ),
        None,
    )

    assert weather_heavy["home_model_prob"] > baseline["home_model_prob"]


@pytest.mark.asyncio
async def test_weather_adjustment_respects_explicit_no_impact_flag(calculator):
    base = {"home_fair_prob": 0.5, "away_fair_prob": 0.5}

    baseline = await calculator.compute_model_win_probabilities(
        base,
        TeamMatchupStats(home_team_name="Home", away_team_name="Away", sport="NFL"),
        None,
    )
    weather_flagged_none = await calculator.compute_model_win_probabilities(
        base,
        TeamMatchupStats(
            weather={
                "is_outdoor": True,
                "affects_game": False,
                "temperature": 20,
                "wind_speed": 30,
                "precipitation": 2.0,
            },
            home_team_name="Home",
            away_team_name="Away",
            sport="NFL",
        ),
        None,
    )

    assert weather_flagged_none["home_model_prob"] == pytest.approx(
        baseline["home_model_prob"], abs=0.0001
    )


@pytest.mark.asyncio
async def test_travel_over_2000_miles_has_larger_penalty(calculator):
    short_travel = await calculator._calculate_situational_adjustment(
        TeamMatchupStats(
            travel_distance=1200,
            home_team_name="Home",
            away_team_name="Away",
            sport="NFL",
        )
    )
    long_travel = await calculator._calculate_situational_adjustment(
        TeamMatchupStats(
            travel_distance=2400,
            home_team_name="Home",
            away_team_name="Away",
            sport="NFL",
        )
    )

    assert long_travel > short_travel
