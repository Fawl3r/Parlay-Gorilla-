from __future__ import annotations

import uuid
from dataclasses import dataclass

import pytest

from app.schemas.parlay import (
    CounterParlayRequest,
    CustomParlayAnalysisResponse,
    CustomParlayLeg,
    CustomParlayLegAnalysis,
)
from app.services.custom_parlay.counter_service import CounterParlayService


@dataclass
class _FakeGame:
    id: uuid.UUID
    home_team: str
    away_team: str
    sport: str = "NFL"
    start_time: object | None = None


class _FakeAnalysisService:
    def __init__(self, games_by_id: dict[str, _FakeGame], metrics_by_game_id: dict[str, dict]):
        self._games_by_id = games_by_id
        self._metrics_by_game_id = metrics_by_game_id

    async def load_games(self, legs):
        return self._games_by_id

    async def analyze_with_loaded_games(self, legs, games_by_id):
        leg_analyses = []
        for leg in legs:
            gid = str(uuid.UUID(str(leg.game_id)))
            game = games_by_id[gid]
            m = self._metrics_by_game_id[gid]
            leg_analyses.append(
                CustomParlayLegAnalysis(
                    game_id=gid,
                    game=f"{game.away_team} @ {game.home_team}",
                    home_team=game.home_team,
                    away_team=game.away_team,
                    sport=game.sport,
                    market_type=str(leg.market_type),
                    pick=str(leg.pick),
                    pick_display=str(leg.pick),
                    odds=str(m.get("odds", "+100")),
                    decimal_odds=float(m.get("decimal_odds", 2.0)),
                    implied_probability=float(m.get("implied_probability", 50.0)),
                    ai_probability=float(m.get("ai_probability", 50.0)),
                    confidence=float(m.get("confidence", 50.0)),
                    edge=float(m.get("edge", 0.0)),
                    recommendation="moderate",
                )
            )

        return CustomParlayAnalysisResponse(
            legs=leg_analyses,
            num_legs=len(leg_analyses),
            combined_implied_probability=0.0,
            combined_ai_probability=0.0,
            overall_confidence=50.0,
            confidence_color="yellow",
            parlay_odds="+100",
            parlay_decimal_odds=2.0,
            ai_summary="",
            ai_risk_notes="",
            ai_recommendation="solid_play",
            weak_legs=[],
            strong_legs=[],
        )


@pytest.mark.asyncio
async def test_counter_parlay_selects_top_edges_best_edges_mode():
    games = {}
    legs = []
    metrics = {}

    # Build 5 games, user picks home ML on each.
    for i in range(5):
        gid = uuid.uuid4()
        games[str(gid)] = _FakeGame(id=gid, home_team=f"Home{i}", away_team=f"Away{i}")
        legs.append(CustomParlayLeg(game_id=str(gid), market_type="h2h", pick=f"Home{i}"))

    # Flipped picks are away ML. Assign metrics by game_id (higher score on 0, then 3).
    # Keep constants so edge/ai_prob drive ordering.
    order = [
        {"ai_probability": 60.0, "edge": 10.0, "confidence": 70.0, "decimal_odds": 2.0, "odds": "+100"},
        {"ai_probability": 55.0, "edge": 5.0, "confidence": 60.0, "decimal_odds": 2.0, "odds": "+100"},
        {"ai_probability": 48.0, "edge": -2.0, "confidence": 50.0, "decimal_odds": 2.0, "odds": "+100"},
        {"ai_probability": 58.0, "edge": 8.0, "confidence": 65.0, "decimal_odds": 2.0, "odds": "+100"},
        {"ai_probability": 51.0, "edge": 1.0, "confidence": 55.0, "decimal_odds": 2.0, "odds": "+100"},
    ]
    for idx, leg in enumerate(legs):
        gid = str(uuid.UUID(str(leg.game_id)))
        metrics[gid] = order[idx]

    analysis = _FakeAnalysisService(games_by_id=games, metrics_by_game_id=metrics)
    service = CounterParlayService(analysis)

    req = CounterParlayRequest(legs=legs, target_legs=2, mode="best_edges", min_edge=0.0)
    resp = await service.generate(req)

    assert len(resp.counter_legs) == 2
    selected_ids = {str(uuid.UUID(str(l.game_id))) for l in resp.counter_legs}
    expected_ids = {list(games.keys())[0], list(games.keys())[3]}
    assert selected_ids == expected_ids

    included_flags = {idx: c.included for idx, c in enumerate(resp.candidates)}
    assert included_flags[0] is True
    assert included_flags[3] is True
    assert included_flags[1] is False
    assert included_flags[2] is False
    assert included_flags[4] is False


@pytest.mark.asyncio
async def test_counter_parlay_min_edge_filters_candidates():
    games = {}
    legs = []
    metrics = {}

    for i in range(3):
        gid = uuid.uuid4()
        games[str(gid)] = _FakeGame(id=gid, home_team=f"Home{i}", away_team=f"Away{i}")
        legs.append(CustomParlayLeg(game_id=str(gid), market_type="h2h", pick=f"Home{i}"))

    # Only leg 0 has edge >= 6%
    edges = [10.0, 5.0, 1.0]
    for idx, leg in enumerate(legs):
        gid = str(uuid.UUID(str(leg.game_id)))
        metrics[gid] = {
            "ai_probability": 55.0,
            "edge": edges[idx],
            "confidence": 60.0,
            "decimal_odds": 2.0,
            "odds": "+100",
        }

    analysis = _FakeAnalysisService(games_by_id=games, metrics_by_game_id=metrics)
    service = CounterParlayService(analysis)

    req = CounterParlayRequest(legs=legs, target_legs=1, mode="best_edges", min_edge=0.06)
    resp = await service.generate(req)
    assert len(resp.counter_legs) == 1
    assert resp.candidates[0].included is True
    assert resp.candidates[1].included is False
    assert resp.candidates[2].included is False


def test_flip_leg_h2h_spreads_totals():
    gid = uuid.uuid4()
    game = _FakeGame(id=gid, home_team="Bengals", away_team="Ravens")

    flipped = CounterParlayService._flip_leg(game, CustomParlayLeg(game_id=str(gid), market_type="h2h", pick="Bengals", market_id="m1"))
    assert flipped.pick == "Ravens"
    assert flipped.market_id == "m1"

    flipped_spread = CounterParlayService._flip_leg(
        game, CustomParlayLeg(game_id=str(gid), market_type="spreads", pick="home", point=3.5, market_id="m2")
    )
    assert flipped_spread.pick == "away"
    assert flipped_spread.point == -3.5
    assert flipped_spread.market_id == "m2"

    flipped_total = CounterParlayService._flip_leg(
        game, CustomParlayLeg(game_id=str(gid), market_type="totals", pick="over", point=44.5, market_id="m3")
    )
    assert flipped_total.pick == "under"
    assert flipped_total.point == 44.5
    assert flipped_total.market_id == "m3"




