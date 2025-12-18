from __future__ import annotations

import uuid
from dataclasses import dataclass

import pytest

from app.schemas.parlay import CustomParlayAnalysisResponse, CustomParlayLeg, CustomParlayLegAnalysis, ParlayCoverageRequest
from app.services.custom_parlay.coverage_service import ParlayCoverageService


@dataclass
class _FakeGame:
    id: uuid.UUID
    home_team: str
    away_team: str
    sport: str = "NFL"
    start_time: object | None = None


class _FakeAnalysisService:
    """
    Minimal analysis service for coverage tests.

    Provides per-game probabilities for home vs away moneyline picks.
    """

    def __init__(self, games_by_id: dict[str, _FakeGame], probs_by_game_id: dict[str, tuple[float, float]]):
        self._games_by_id = games_by_id
        self._probs_by_game_id = probs_by_game_id

    async def load_games(self, legs):
        return self._games_by_id

    async def analyze_with_loaded_games(self, legs, games_by_id):
        leg_analyses = []
        combined_ai = 1.0
        combined_implied = 1.0
        parlay_decimal = 1.0

        for leg in legs:
            gid = str(uuid.UUID(str(leg.game_id)))
            game = games_by_id[gid]
            home_prob, away_prob = self._probs_by_game_id[gid]
            is_home = str(leg.pick).lower() == str(game.home_team).lower()
            ai_prob = home_prob if is_home else away_prob

            implied_prob = 0.5
            edge = (ai_prob - implied_prob) * 100.0
            conf = 60.0

            combined_ai *= ai_prob
            combined_implied *= implied_prob
            parlay_decimal *= 2.0

            leg_analyses.append(
                CustomParlayLegAnalysis(
                    game_id=gid,
                    game=f"{game.away_team} @ {game.home_team}",
                    home_team=game.home_team,
                    away_team=game.away_team,
                    sport=game.sport,
                    market_type=str(leg.market_type),
                    pick=str(leg.pick),
                    pick_display=f"{leg.pick} ML",
                    odds="+100",
                    decimal_odds=2.0,
                    implied_probability=implied_prob * 100.0,
                    ai_probability=ai_prob * 100.0,
                    confidence=conf,
                    edge=edge,
                    recommendation="moderate",
                )
            )

        return CustomParlayAnalysisResponse(
            legs=leg_analyses,
            num_legs=len(leg_analyses),
            combined_implied_probability=combined_implied * 100.0,
            combined_ai_probability=combined_ai * 100.0,
            overall_confidence=50.0,
            confidence_color="yellow",
            parlay_odds="+100",
            parlay_decimal_odds=parlay_decimal,
            ai_summary="",
            ai_risk_notes="",
            ai_recommendation="solid_play",
            weak_legs=[],
            strong_legs=[],
        )


@pytest.mark.asyncio
async def test_coverage_pack_counts_and_top_scenarios():
    games = {}
    probs = {}
    legs = []

    # 3 games, user picks HOME for each.
    for i, (home_p, away_p) in enumerate([(0.80, 0.20), (0.60, 0.40), (0.55, 0.45)]):
        gid = uuid.uuid4()
        games[str(gid)] = _FakeGame(id=gid, home_team=f"Home{i}", away_team=f"Away{i}")
        probs[str(gid)] = (home_p, away_p)
        legs.append(CustomParlayLeg(game_id=str(gid), market_type="h2h", pick=f"Home{i}"))

    service = ParlayCoverageService(_FakeAnalysisService(games_by_id=games, probs_by_game_id=probs))
    req = ParlayCoverageRequest(legs=legs, max_total_parlays=20, scenario_max=2, round_robin_max=0, round_robin_size=2)
    resp = await service.build_coverage_pack(req)

    assert resp.num_games == 3
    assert resp.total_scenarios == 8  # 2^3
    assert sum(resp.by_upset_count.values()) == 8

    assert len(resp.scenario_tickets) == 2
    assert resp.scenario_tickets[0].num_upsets == 0
    assert resp.scenario_tickets[1].num_upsets == 1

    # Second-best scenario should flip the game with the highest away probability (closest to home): game index 2.
    second_ticket_picks = [l.pick for l in resp.scenario_tickets[1].legs]
    assert second_ticket_picks[0] == "Home0"
    assert second_ticket_picks[1] == "Home1"
    assert second_ticket_picks[2] == "Away2"


@pytest.mark.asyncio
async def test_coverage_pack_total_cap_applies_across_sections():
    games = {}
    probs = {}
    legs = []

    for i, (home_p, away_p) in enumerate([(0.70, 0.30), (0.65, 0.35), (0.60, 0.40), (0.55, 0.45)]):
        gid = uuid.uuid4()
        games[str(gid)] = _FakeGame(id=gid, home_team=f"Home{i}", away_team=f"Away{i}")
        probs[str(gid)] = (home_p, away_p)
        legs.append(CustomParlayLeg(game_id=str(gid), market_type="h2h", pick=f"Home{i}"))

    service = ParlayCoverageService(_FakeAnalysisService(games_by_id=games, probs_by_game_id=probs))
    # Cap total at 5; request 4 scenarios + 1 RR (sum <= cap).
    req = ParlayCoverageRequest(
        legs=legs,
        max_total_parlays=5,
        scenario_max=4,
        round_robin_max=1,
        round_robin_size=2,
    )
    resp = await service.build_coverage_pack(req)

    assert len(resp.scenario_tickets) <= 4
    assert len(resp.round_robin_tickets) <= 1
    assert len(resp.scenario_tickets) + len(resp.round_robin_tickets) <= 5
    assert all(t.analysis.num_legs == len(t.legs) for t in resp.scenario_tickets)
    assert all(t.analysis.num_legs == len(t.legs) for t in resp.round_robin_tickets)


