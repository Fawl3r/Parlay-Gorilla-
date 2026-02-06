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

    market = Market(game_id=game.id, market_type="h2h", book="draftkings")
    db.add(market)
    await db.flush()

    odds = Odds(market_id=market.id, outcome="home", price="-110", decimal_price=1.91, implied_prob=0.523)
    db.add(odds)
    await db.commit()

    service = CandidateLegService(engine=_EngineStub(db), repo=_RepoStub())
    legs = await service.get_candidate_legs(sport="NFL", min_confidence=0.0, max_legs=50, week=None)

    assert len(legs) >= 1
    assert legs[0].get("game_id") == str(game.id)


def _cache_miss_cache():
    """Cache that always misses (for tests that need full pipeline)."""
    from unittest.mock import AsyncMock, MagicMock
    c = MagicMock()
    c.get = AsyncMock(return_value=None)
    c.set = AsyncMock()
    return c


@pytest.mark.asyncio
async def test_candidate_leg_service_returns_early_when_total_odds_zero(db: AsyncSession):
    """
    When games exist but have no odds (total_odds=0), service returns [] without
    calling prefetch_for_games to avoid heavy work/OOM.
    """
    from unittest.mock import patch

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

    with patch("app.services.probability_engine_impl.candidate_leg_service.get_candidate_leg_cache", return_value=_cache_miss_cache()):
        repo = _RepoStub(record_prefetch=True)
        service = CandidateLegService(engine=_EngineStub(db), repo=repo)
        legs = await service.get_candidate_legs(sport="NFL", min_confidence=0.0, max_legs=50, week=None)

    assert legs == []
    assert repo.prefetch_called is False


@pytest.mark.asyncio
async def test_candidate_leg_service_uses_minimal_queries_no_selectinload(db: AsyncSession):
    """Candidate leg flow uses fetch_minimal_game_rows and fetch_minimal_odds_rows (no ORM selectinload)."""
    from unittest.mock import AsyncMock, patch

    start_time = datetime.now(timezone.utc) + timedelta(hours=6)
    game = Game(
        external_game_id="espn:nfl:minimal-query-test",
        sport="NFL",
        home_team="Home",
        away_team="Away",
        start_time=start_time,
        status="scheduled",
    )
    db.add(game)
    await db.flush()
    market = Market(game_id=game.id, market_type="h2h", book="draftkings")
    db.add(market)
    await db.flush()
    db.add(Odds(market_id=market.id, outcome="home", price="-110", decimal_price=1.91, implied_prob=0.523))
    await db.commit()

    with patch("app.services.probability_engine_impl.candidate_leg_service.get_candidate_leg_cache", return_value=_cache_miss_cache()):
        with patch("app.services.probability_engine_impl.candidate_leg_service.fetch_minimal_game_rows", new_callable=AsyncMock) as mock_games:
            with patch("app.services.probability_engine_impl.candidate_leg_service.fetch_minimal_odds_rows", new_callable=AsyncMock) as mock_odds:
                mock_games.return_value = [
                    {"id": game.id, "sport": "NFL", "start_time": start_time, "status": "scheduled", "home_team": "Home", "away_team": "Away", "external_game_id": "espn:nfl:minimal-query-test"}
                ]
                mock_odds.return_value = [
                    {"game_id": game.id, "market_id": market.id, "market_type": "h2h", "book": "draftkings", "outcome": "home", "price": "-110", "decimal_price": 1.91, "implied_prob": 0.523, "created_at": None}
                ]
                service = CandidateLegService(engine=_EngineStub(db), repo=_RepoStub())
                legs = await service.get_candidate_legs(sport="NFL", min_confidence=0.0, max_legs=50, week=None)
    assert mock_games.called
    assert mock_odds.called
    assert len(legs) >= 1
    assert legs[0].get("game_id") == str(game.id)


@pytest.mark.asyncio
async def test_candidate_legs_truncated_emits_event(db: AsyncSession):
    """When candidate legs exceed max_legs_cap, parlay.candidates_truncated is emitted and final list is capped."""
    from unittest.mock import AsyncMock, patch

    from app.core.config import settings as real_settings

    start_time = datetime.now(timezone.utc) + timedelta(hours=6)
    game = Game(
        external_game_id="espn:nfl:truncate-test",
        sport="NFL",
        home_team="Home",
        away_team="Away",
        start_time=start_time,
        status="scheduled",
    )
    db.add(game)
    await db.flush()
    market = Market(game_id=game.id, market_type="h2h", book="draftkings")
    db.add(market)
    await db.flush()
    db.add(Odds(market_id=market.id, outcome="home", price="-110", decimal_price=1.91, implied_prob=0.523))
    db.add(Odds(market_id=market.id, outcome="away", price="-110", decimal_price=1.91, implied_prob=0.523))
    await db.commit()

    with patch("app.services.probability_engine_impl.candidate_leg_service.get_candidate_leg_cache", return_value=_cache_miss_cache()):
        with patch("app.services.probability_engine_impl.candidate_leg_service.fetch_minimal_game_rows", new_callable=AsyncMock) as mock_games:
            with patch("app.services.probability_engine_impl.candidate_leg_service.fetch_minimal_odds_rows", new_callable=AsyncMock) as mock_odds:
                with patch("app.services.probability_engine_impl.candidate_leg_service.log_event") as mock_log_event:
                    with patch.object(real_settings, "parlay_max_legs_considered", 1):
                        mock_games.return_value = [
                            {"id": game.id, "sport": "NFL", "start_time": start_time, "status": "scheduled", "home_team": "Home", "away_team": "Away", "external_game_id": "x"}
                        ]
                        mock_odds.return_value = [
                            {"game_id": game.id, "market_id": market.id, "market_type": "h2h", "book": "draftkings", "outcome": "home", "price": "-110", "decimal_price": 1.91, "implied_prob": 0.523, "created_at": None},
                            {"game_id": game.id, "market_id": market.id, "market_type": "h2h", "book": "draftkings", "outcome": "away", "price": "-110", "decimal_price": 1.91, "implied_prob": 0.523, "created_at": None},
                        ]
                        service = CandidateLegService(engine=_EngineStub(db), repo=_RepoStub())
                        legs = await service.get_candidate_legs(sport="NFL", min_confidence=0.0, max_legs=50, week=None)
                    calls = [c for c in mock_log_event.call_args_list if len(c[0]) >= 2 and c[0][1] == "parlay.candidates_truncated"]
                    assert len(calls) >= 1, "expected parlay.candidates_truncated when legs exceed cap"
    assert len(legs) <= 1