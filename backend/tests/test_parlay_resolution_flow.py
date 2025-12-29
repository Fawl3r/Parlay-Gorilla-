from __future__ import annotations

from datetime import datetime, timedelta, timezone
import pytest

from app.models.game import Game
from app.models.game_results import GameResult
from app.models.market import Market
from app.models.odds import Odds
from app.models.parlay import Parlay
from app.models.parlay_results import ParlayResult
from app.services.parlay_tracker import ParlayTrackerService
from sqlalchemy import select


@pytest.mark.asyncio
async def test_auto_resolve_parlays_creates_parlay_result_with_leg_status(db):
    now = datetime.now(tz=timezone.utc)

    # Create a game with a market + odds
    game = Game(
        external_game_id="evt_parlay_resolve_1",
        sport="NFL",
        home_team="Home Team",
        away_team="Away Team",
        start_time=now - timedelta(hours=6),
        status="scheduled",
    )
    db.add(game)
    await db.flush()

    market = Market(game_id=game.id, market_type="h2h", book="draftkings")
    db.add(market)
    await db.flush()

    db.add_all(
        [
            Odds(market_id=market.id, outcome="home", price="-110", decimal_price=1.909, implied_prob=0.524),
            Odds(market_id=market.id, outcome="away", price="-110", decimal_price=1.909, implied_prob=0.524),
        ]
    )

    # Insert final result (home wins)
    gr = GameResult(
        game_id=game.id,
        external_game_id="evt_parlay_resolve_1",
        sport="NFL",
        home_team="Home Team",
        away_team="Away Team",
        game_date=now - timedelta(hours=6),
        home_score=24,
        away_score=17,
        winner="home",
        status="final",
        completed="true",
    )
    db.add(gr)

    # Create an AI-generated parlay older than 4h so auto_resolve picks it up
    parlay = Parlay(
        user_id=None,
        legs=[
            {
                "market_id": str(market.id),
                "outcome": "home",
                "game": "Away Team @ Home Team",
                "home_team": "Home Team",
                "away_team": "Away Team",
                "market_type": "h2h",
                "odds": "-110",
                "probability": 0.55,
                "confidence": 60,
                "sport": "NFL",
            }
        ],
        num_legs=1,
        model_version="v1.0",
        parlay_hit_prob=0.55,
        risk_profile="balanced",
        ai_summary="",
        ai_risk_notes="",
        created_at=now - timedelta(hours=6),
    )
    db.add(parlay)
    await db.commit()

    tracker = ParlayTrackerService(db)
    resolved = await tracker.auto_resolve_parlays()
    assert resolved >= 1

    res = await db.execute(select(ParlayResult).where(ParlayResult.parlay_id == parlay.id))
    pr = res.scalar_one_or_none()
    assert pr is not None
    assert pr.hit is True
    assert isinstance(pr.leg_results, list)
    assert pr.leg_results[0]["status"] == "hit"


