from __future__ import annotations

import pytest

from app.models.game_results import GameResult
from app.services.parlay_grading.leg_input_parsers import AiLegInputParser
from app.services.parlay_grading.parlay_leg_grader import ParlayLegGrader
from app.services.parlay_grading.types import ParlayLegStatus


def _game_result(home: int, away: int) -> GameResult:
    gr = GameResult(
        sport="NFL",
        home_team="Home Team",
        away_team="Away Team",
        game_date=None,  # overwritten below; not used by grader directly
        home_score=home,
        away_score=away,
        completed="true",
        status="final",
    )
    # GameResult.game_date is non-nullable in the DB model; set a safe value for object creation.
    from datetime import datetime, timezone

    gr.game_date = datetime.now(tz=timezone.utc)
    return gr


@pytest.mark.asyncio
async def test_grade_h2h_hit_and_miss():
    parser = AiLegInputParser()
    grader = ParlayLegGrader()

    leg_home = {"market_type": "h2h", "outcome": "home"}
    parsed = parser.parse(leg_home, home_team="Home Team", away_team="Away Team").parsed
    assert parsed is not None
    graded = grader.grade(parsed_leg=parsed, game_result=_game_result(21, 17))
    assert graded.status == ParlayLegStatus.hit

    leg_away = {"market_type": "h2h", "outcome": "away"}
    parsed2 = parser.parse(leg_away, home_team="Home Team", away_team="Away Team").parsed
    assert parsed2 is not None
    graded2 = grader.grade(parsed_leg=parsed2, game_result=_game_result(21, 17))
    assert graded2.status == ParlayLegStatus.missed


@pytest.mark.asyncio
async def test_grade_spread_push_and_cover():
    parser = AiLegInputParser()
    grader = ParlayLegGrader()

    # Home -3.0 wins by exactly 3 => push
    leg = {"market_type": "spreads", "outcome": "Home Team -3.0"}
    parsed = parser.parse(leg, home_team="Home Team", away_team="Away Team").parsed
    assert parsed is not None
    graded = grader.grade(parsed_leg=parsed, game_result=_game_result(24, 21))
    assert graded.status == ParlayLegStatus.push

    # Away +3.5 loses by 3 => cover
    leg2 = {"market_type": "spreads", "outcome": "Away Team +3.5"}
    parsed2 = parser.parse(leg2, home_team="Home Team", away_team="Away Team").parsed
    assert parsed2 is not None
    graded2 = grader.grade(parsed_leg=parsed2, game_result=_game_result(24, 21))
    assert graded2.status == ParlayLegStatus.hit


@pytest.mark.asyncio
async def test_grade_totals_over_under_push():
    parser = AiLegInputParser()
    grader = ParlayLegGrader()

    # Total 44.5, score 27-20 => 47 => over
    leg_over = {"market_type": "totals", "outcome": "Over 44.5"}
    parsed = parser.parse(leg_over, home_team="Home Team", away_team="Away Team").parsed
    assert parsed is not None
    graded = grader.grade(parsed_leg=parsed, game_result=_game_result(27, 20))
    assert graded.status == ParlayLegStatus.hit

    # Total 47.0, score 27-20 => 47 => push
    leg_push = {"market_type": "totals", "outcome": "Under 47.0"}
    parsed2 = parser.parse(leg_push, home_team="Home Team", away_team="Away Team").parsed
    assert parsed2 is not None
    graded2 = grader.grade(parsed_leg=parsed2, game_result=_game_result(27, 20))
    assert graded2.status == ParlayLegStatus.push


