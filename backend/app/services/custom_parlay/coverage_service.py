from __future__ import annotations

import heapq
import math
import uuid
from dataclasses import dataclass
from itertools import combinations
from typing import Dict, List, Tuple

from app.schemas.parlay import (
    CoverageTicket,
    CustomParlayAnalysisResponse,
    CustomParlayLeg,
    CustomParlayLegAnalysis,
    ParlayCoverageRequest,
    ParlayCoverageResponse,
)
from app.services.custom_parlay.analysis_service import CustomParlayAnalysisService
from app.services.custom_parlay.counter_service import CounterParlayService
from app.services.custom_parlay.odds_utils import OddsConverter


@dataclass(frozen=True)
class _ScoredMask:
    probability: float
    mask: int


@dataclass(frozen=True)
class _ScoredCombo:
    probability: float
    indices: Tuple[int, ...]


class ParlayCoverageService:
    """
    Builds an upset coverage pack from a user's selected legs.

    Outputs:
    - Combinatorics counts (2^N and nCk breakdown)
    - Scenario tickets: full-slate outcomes (original vs flipped per game), top-K by probability
    - Round robin tickets: subsets of the original ticket, top-K by probability
    """

    def __init__(self, analysis_service: CustomParlayAnalysisService):
        self._analysis = analysis_service

    async def build_coverage_pack(self, request: ParlayCoverageRequest) -> ParlayCoverageResponse:
        legs = list(request.legs or [])
        if not legs:
            raise ValueError("At least one leg is required")

        games_by_id = await self._analysis.load_games(legs)

        original_analysis = await self._analysis.analyze_with_loaded_games(legs, games_by_id)
        flipped_legs = self._flip_legs(legs, games_by_id)
        flipped_analysis = await self._analysis.analyze_with_loaded_games(flipped_legs, games_by_id)

        n = len(legs)
        total_scenarios = 1 << n
        by_upset_count = {k: int(math.comb(n, k)) for k in range(n + 1)}

        scenario_tickets: List[CoverageTicket] = []
        if request.scenario_max > 0:
            top_masks = self._top_k_scenarios(
                original_leg_analyses=original_analysis.legs,
                flipped_leg_analyses=flipped_analysis.legs,
                k=min(int(request.scenario_max), int(request.max_total_parlays)),
            )
            scenario_tickets = [
                self._build_ticket_from_mask(
                    mask=sc.mask,
                    original_legs=legs,
                    flipped_legs=flipped_legs,
                    original_leg_analyses=original_analysis.legs,
                    flipped_leg_analyses=flipped_analysis.legs,
                )
                for sc in top_masks
            ]

        round_robin_tickets: List[CoverageTicket] = []
        if request.round_robin_max > 0:
            remaining = max(0, int(request.max_total_parlays) - len(scenario_tickets))
            if remaining > 0:
                top_combos = self._top_k_round_robins(
                    legs=legs,
                    leg_analyses=original_analysis.legs,
                    size=int(request.round_robin_size),
                    k=min(int(request.round_robin_max), remaining),
                )
                round_robin_tickets = [
                    self._build_round_robin_ticket(
                        indices=sc.indices,
                        legs=legs,
                        leg_analyses=original_analysis.legs,
                    )
                    for sc in top_combos
                ]

        return ParlayCoverageResponse(
            num_games=n,
            total_scenarios=int(total_scenarios),
            by_upset_count=by_upset_count,
            scenario_tickets=scenario_tickets,
            round_robin_tickets=round_robin_tickets,
        )

    # ------------------------------------------------------------------
    # Flipping and selection
    # ------------------------------------------------------------------

    def _flip_legs(self, legs: List[CustomParlayLeg], games_by_id) -> List[CustomParlayLeg]:
        flipped: List[CustomParlayLeg] = []
        for leg in legs:
            game_id_norm = str(uuid.UUID(str(leg.game_id)))
            game = games_by_id.get(game_id_norm)
            if not game:
                raise ValueError(f"Game not found: {leg.game_id}")
            flipped.append(CounterParlayService._flip_leg(game, leg))
        return flipped

    def _top_k_scenarios(
        self,
        original_leg_analyses: List[CustomParlayLegAnalysis],
        flipped_leg_analyses: List[CustomParlayLegAnalysis],
        k: int,
    ) -> List[_ScoredMask]:
        n = len(original_leg_analyses)
        if k <= 0 or n == 0:
            return []

        p_orig = [max(0.000001, min(0.999999, float(l.ai_probability) / 100.0)) for l in original_leg_analyses]
        p_flip = [max(0.000001, min(0.999999, float(l.ai_probability) / 100.0)) for l in flipped_leg_analyses]

        heap: List[Tuple[float, int]] = []
        for mask in range(1 << n):
            prob = 1.0
            for i in range(n):
                prob *= p_flip[i] if (mask & (1 << i)) else p_orig[i]
            if len(heap) < k:
                heapq.heappush(heap, (prob, mask))
            else:
                if prob > heap[0][0]:
                    heapq.heapreplace(heap, (prob, mask))

        heap.sort(key=lambda x: x[0], reverse=True)
        return [_ScoredMask(probability=p, mask=m) for p, m in heap]

    def _top_k_round_robins(
        self,
        legs: List[CustomParlayLeg],
        leg_analyses: List[CustomParlayLegAnalysis],
        size: int,
        k: int,
    ) -> List[_ScoredCombo]:
        n = len(legs)
        if k <= 0:
            return []
        if size < 2 or size > n:
            return []

        p = [max(0.000001, min(0.999999, float(l.ai_probability) / 100.0)) for l in leg_analyses]
        heap: List[Tuple[float, Tuple[int, ...]]] = []

        for combo in combinations(range(n), size):
            prob = 1.0
            for idx in combo:
                prob *= p[idx]
            if len(heap) < k:
                heapq.heappush(heap, (prob, combo))
            else:
                if prob > heap[0][0]:
                    heapq.heapreplace(heap, (prob, combo))

        heap.sort(key=lambda x: x[0], reverse=True)
        return [_ScoredCombo(probability=pv, indices=combo) for pv, combo in heap]

    # ------------------------------------------------------------------
    # Ticket builders
    # ------------------------------------------------------------------

    def _build_ticket_from_mask(
        self,
        mask: int,
        original_legs: List[CustomParlayLeg],
        flipped_legs: List[CustomParlayLeg],
        original_leg_analyses: List[CustomParlayLegAnalysis],
        flipped_leg_analyses: List[CustomParlayLegAnalysis],
    ) -> CoverageTicket:
        n = len(original_legs)
        chosen_legs: List[CustomParlayLeg] = []
        chosen_leg_analyses: List[CustomParlayLegAnalysis] = []

        for i in range(n):
            if mask & (1 << i):
                chosen_legs.append(flipped_legs[i])
                chosen_leg_analyses.append(flipped_leg_analyses[i])
            else:
                chosen_legs.append(original_legs[i])
                chosen_leg_analyses.append(original_leg_analyses[i])

        return CoverageTicket(
            legs=chosen_legs,
            num_upsets=int(mask.bit_count()),
            analysis=self._build_analysis(chosen_leg_analyses),
        )

    def _build_round_robin_ticket(
        self,
        indices: Tuple[int, ...],
        legs: List[CustomParlayLeg],
        leg_analyses: List[CustomParlayLegAnalysis],
    ) -> CoverageTicket:
        chosen_legs = [legs[i] for i in indices]
        chosen_leg_analyses = [leg_analyses[i] for i in indices]
        return CoverageTicket(
            legs=chosen_legs,
            num_upsets=0,
            analysis=self._build_analysis(chosen_leg_analyses),
        )

    # ------------------------------------------------------------------
    # Aggregate analysis builder (no extra engine calls)
    # ------------------------------------------------------------------

    def _build_analysis(self, leg_analyses: List[CustomParlayLegAnalysis]) -> CustomParlayAnalysisResponse:
        num_legs = len(leg_analyses)
        if num_legs == 0:
            raise ValueError("Cannot build analysis for empty ticket")

        combined_implied = 1.0
        combined_ai = 1.0
        parlay_decimal = 1.0

        weak_legs: List[str] = []
        strong_legs: List[str] = []
        for leg in leg_analyses:
            combined_implied *= max(0.000001, min(0.999999, float(leg.implied_probability) / 100.0))
            combined_ai *= max(0.000001, min(0.999999, float(leg.ai_probability) / 100.0))
            parlay_decimal *= max(1.01, float(leg.decimal_odds))

            if leg.recommendation in {"avoid", "weak"}:
                weak_legs.append(f"{leg.game}: {leg.pick_display}")
            elif leg.recommendation == "strong":
                strong_legs.append(f"{leg.game}: {leg.pick_display}")

        avg_confidence = sum(float(l.confidence) for l in leg_analyses) / num_legs
        leg_penalty = max(0.0, float(num_legs - 3) * 2.0)
        overall_confidence = max(10.0, avg_confidence - leg_penalty)

        confidence_color = CustomParlayAnalysisService._get_confidence_color(overall_confidence)
        overall_recommendation = CustomParlayAnalysisService._get_overall_recommendation(
            overall_confidence, len(weak_legs), num_legs
        )
        summary, risk_notes = CustomParlayAnalysisService._build_deterministic_ai_text(
            legs=leg_analyses,
            combined_ai_probability=combined_ai * 100.0,
            overall_confidence=overall_confidence,
            weak_legs=weak_legs,
            strong_legs=strong_legs,
        )

        return CustomParlayAnalysisResponse(
            legs=leg_analyses,
            num_legs=num_legs,
            combined_implied_probability=round(combined_implied * 100.0, 2),
            combined_ai_probability=round(combined_ai * 100.0, 2),
            overall_confidence=round(overall_confidence, 1),
            confidence_color=confidence_color,
            parlay_odds=OddsConverter.decimal_to_american(parlay_decimal),
            parlay_decimal_odds=round(parlay_decimal, 2),
            ai_summary=summary,
            ai_risk_notes=risk_notes,
            ai_recommendation=overall_recommendation,
            weak_legs=weak_legs,
            strong_legs=strong_legs,
        )


