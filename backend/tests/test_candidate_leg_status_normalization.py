from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.game import Game
from app.models.market import Market
from app.models.odds import Odds
from app.services.probability_engine_impl.candidate_leg_service import CandidateLegService


class _RepoStub:
    def __init__(self, record_prefetch: bool = False):
        self.prefetch_called = False
        self._record = record_prefetch

    async def prefetch_for_games(self, games: List[Any]) -> None:
        if self._record:
            self.prefetch_called = True
        return None


class _EngineStub:
    sport_code = "NFL"

    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_leg_probability_from_odds(
        self,
        odds_obj: Odds,
        market_id,
        outcome: str,
        home_team: str,
        away_team: str,
        game_start_time=None,
        market_type=None,
    ) -> Dict:
        # Return a deterministic leg probability payload (enough fields for candidate selection).
        return {
            "market_id": str(market_id),
            "outcome": outcome,
            "implied_prob": float(getattr(odds_obj, "implied_prob", 0.5) or 0.5),
            "adjusted_prob": 0.60,
            "edge": 0.10,
            "value_score": 0.10,
            "confidence_score": 60.0,
            "odds": getattr(odds_obj, "price", "-110"),
            "decimal_odds": float(getattr(odds_obj, "decimal_price", 1.91) or 1.91),
        }


@pytest.mark.asyncio
async def test_candidate_leg_service_includes_espn_status_scheduled(db: AsyncSession):
    """
    Regression: ESPN schedule rows often store `STATUS_SCHEDULED`.
    We must treat that as scheduled so candidate legs can be built when odds exist.
    """
    start_time = datetime.now(timezone.utc) + timedelta(hours=6)

    game = Game(
        external_game_id="espn:nfl:test-game",
        sport="NFL",
        home_team="Home Team",
        away_team="Away Team",
        start_time=start_time,
        status="STATUS_SCHEDULED",
    )
    db.add(game)
    await db.flush()

    market = Market(game_id=game.id, market_type="h2h", book="testbook")
    db.add(market)
    await db.flush()

    odds = Odds(market_id=market.id, outcome="home", price="-110", decimal_price=1.91, implied_prob=0.523)
    db.add(odds)
    await db.commit()

    service = CandidateLegService(engine=_EngineStub(db), repo=_RepoStub())
    legs = await service.get_candidate_legs(sport="NFL", min_confidence=0.0, max_legs=50, week=None)

    assert len(legs) >= 1
    assert legs[0].get("game_id") == str(game.id)


@pytest.mark.asyncio
async def test_candidate_leg_service_returns_early_when_total_odds_zero(db: AsyncSession):
    """
    When games exist but have no odds (total_odds=0), service returns [] without
    calling prefetch_for_games to avoid heavy work/OOM.
    """
    start_time = datetime.now(timezone.utc) + timedelta(hours=6)
    game = Game(
        external_game_id="nfl:no-odds-game",
        sport="NFL",
        home_team="Home",
        away_team="Away",
        start_time=start_time,
        status="scheduled",
    )
    db.add(game)
    await db.flush()
    # No Market/Odds added - so total_odds will be 0
    await db.commit()

    repo = _RepoStub(record_prefetch=True)
    service = CandidateLegService(engine=_EngineStub(db), repo=repo)
    legs = await service.get_candidate_legs(sport="NFL", min_confidence=0.0, max_legs=50, week=None)

    assert legs == []
    assert repo.prefetch_called is False


