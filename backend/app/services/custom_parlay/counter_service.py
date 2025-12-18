from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import List, Optional, Set

from app.schemas.parlay import (
    CounterLegCandidate,
    CounterParlayRequest,
    CounterParlayResponse,
    CustomParlayLeg,
)

from .analysis_service import CustomParlayAnalysisService


@dataclass(frozen=True)
class _Selection:
    indices: List[int]
    selected: Set[int]


class CounterParlayService:
    """
    Builds a counter/hedge ticket from a user's selected games.

    Behavior:
    - Flips each input leg to its opposite side (same games).
    - Scores the flipped legs by model edge/EV and selects a subset if requested.
    """

    def __init__(self, analysis_service: CustomParlayAnalysisService):
        self._analysis = analysis_service

    async def generate(self, request: CounterParlayRequest) -> CounterParlayResponse:
        if not request.legs:
            raise ValueError("At least one leg is required")

        # Load games once so flips can resolve team names.
        games_by_id = await self._analysis.load_games(request.legs)

        flipped_legs: List[CustomParlayLeg] = []
        for leg in request.legs:
            game_id_norm = str(uuid.UUID(str(leg.game_id)))
            game = games_by_id.get(game_id_norm)
            if not game:
                raise ValueError(f"Game not found: {leg.game_id}")
            flipped_legs.append(self._flip_leg(game, leg))

        flipped_analysis = await self._analysis.analyze_with_loaded_games(flipped_legs, games_by_id)

        selection = self._select_indices(
            request=request,
            flipped_legs=flipped_legs,
            flipped_analysis=flipped_analysis,
        )

        selected_counter_legs = [flipped_legs[i] for i in selection.indices]
        selected_analysis = await self._analysis.analyze_with_loaded_games(selected_counter_legs, games_by_id)

        candidates: List[CounterLegCandidate] = []
        for idx, (orig, flipped, leg_analysis) in enumerate(
            zip(request.legs, flipped_legs, flipped_analysis.legs)
        ):
            score = self._score_leg(
                ai_probability_pct=float(leg_analysis.ai_probability),
                decimal_odds=float(leg_analysis.decimal_odds),
                confidence=float(leg_analysis.confidence),
                edge_pct=float(leg_analysis.edge),
            )
            candidates.append(
                CounterLegCandidate(
                    game_id=str(orig.game_id),
                    market_type=str(orig.market_type),
                    original_pick=str(orig.pick),
                    counter_pick=str(flipped.pick),
                    counter_odds=str(leg_analysis.odds),
                    counter_ai_probability=float(leg_analysis.ai_probability),
                    counter_confidence=float(leg_analysis.confidence),
                    counter_edge=float(leg_analysis.edge),
                    score=float(round(score, 6)),
                    included=idx in selection.selected,
                )
            )

        return CounterParlayResponse(
            counter_legs=selected_counter_legs,
            counter_analysis=selected_analysis,
            candidates=candidates,
        )

    # ------------------------------------------------------------------
    # Selection + scoring
    # ------------------------------------------------------------------

    def _select_indices(
        self,
        request: CounterParlayRequest,
        flipped_legs: List[CustomParlayLeg],
        flipped_analysis,
    ) -> _Selection:
        mode = str(request.mode or "best_edges").lower().strip()
        if mode == "flip_all":
            indices = list(range(len(flipped_legs)))
            return _Selection(indices=indices, selected=set(indices))

        target = request.target_legs if request.target_legs is not None else len(flipped_legs)
        target = max(1, min(len(flipped_legs), int(target)))

        min_edge = float(request.min_edge or 0.0) * 100.0  # request is 0-1; analysis edge is percent

        scored: List[tuple[int, float]] = []
        for idx, leg_analysis in enumerate(flipped_analysis.legs):
            # Filter by minimum edge (percent)
            if float(leg_analysis.edge) < min_edge:
                continue
            score = self._score_leg(
                ai_probability_pct=float(leg_analysis.ai_probability),
                decimal_odds=float(leg_analysis.decimal_odds),
                confidence=float(leg_analysis.confidence),
                edge_pct=float(leg_analysis.edge),
            )
            scored.append((idx, score))

        # If filtering is too strict, fall back to scoring all legs.
        if len(scored) < target:
            scored = []
            for idx, leg_analysis in enumerate(flipped_analysis.legs):
                score = self._score_leg(
                    ai_probability_pct=float(leg_analysis.ai_probability),
                    decimal_odds=float(leg_analysis.decimal_odds),
                    confidence=float(leg_analysis.confidence),
                    edge_pct=float(leg_analysis.edge),
                )
                scored.append((idx, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        indices = [idx for idx, _ in scored[:target]]

        return _Selection(indices=indices, selected=set(indices))

    @staticmethod
    def _score_leg(
        ai_probability_pct: float,
        decimal_odds: float,
        confidence: float,
        edge_pct: float,
    ) -> float:
        """
        Higher is better.

        Uses a stable, EV-ish score:
          EV = (p * dec_odds) - 1
          score = EV * (0.7 + 0.3 * confidence_norm) + edge * 0.5
        """
        p = max(0.0001, min(0.9999, float(ai_probability_pct) / 100.0))
        dec = max(1.01, float(decimal_odds))
        ev = (p * dec) - 1.0
        confidence_norm = max(0.0, min(1.0, float(confidence) / 100.0))
        edge = float(edge_pct) / 100.0
        return (ev * (0.7 + 0.3 * confidence_norm)) + (edge * 0.5)

    # ------------------------------------------------------------------
    # Flipping logic
    # ------------------------------------------------------------------

    @staticmethod
    def _flip_leg(game, leg: CustomParlayLeg) -> CustomParlayLeg:
        market_type = str(leg.market_type).lower().strip()
        pick = str(leg.pick).strip()

        if market_type == "h2h":
            pick_lower = pick.lower()
            home = str(game.home_team)
            away = str(game.away_team)

            # Accept team-name picks or "home"/"away"
            if pick_lower == "home" or pick_lower == home.lower():
                return CustomParlayLeg(
                    game_id=str(game.id),
                    market_type="h2h",
                    pick=away,
                    market_id=leg.market_id,
                )
            if pick_lower == "away" or pick_lower == away.lower():
                return CustomParlayLeg(
                    game_id=str(game.id),
                    market_type="h2h",
                    pick=home,
                    market_id=leg.market_id,
                )
            raise ValueError(f"Invalid moneyline pick '{pick}' for game {away} @ {home}")

        if market_type == "spreads":
            pick_lower = pick.lower()
            if pick_lower not in {"home", "away"}:
                # Best-effort: infer from team name
                if pick_lower == str(game.home_team).lower():
                    pick_lower = "home"
                elif pick_lower == str(game.away_team).lower():
                    pick_lower = "away"
                else:
                    raise ValueError(f"Invalid spread pick '{pick}' (expected home/away) for game {game.away_team} @ {game.home_team}")

            flipped_pick = "away" if pick_lower == "home" else "home"
            flipped_point: Optional[float] = None
            if leg.point is not None:
                try:
                    flipped_point = -float(leg.point)
                except Exception:
                    flipped_point = None

            return CustomParlayLeg(
                game_id=str(game.id),
                market_type="spreads",
                pick=flipped_pick,
                point=flipped_point,
                market_id=leg.market_id,
            )

        if market_type == "totals":
            pick_lower = pick.lower()
            if pick_lower not in {"over", "under"}:
                raise ValueError(f"Invalid totals pick '{pick}' (expected over/under) for game {game.away_team} @ {game.home_team}")
            flipped_pick = "under" if pick_lower == "over" else "over"
            return CustomParlayLeg(
                game_id=str(game.id),
                market_type="totals",
                pick=flipped_pick,
                point=leg.point,
                market_id=leg.market_id,
            )

        raise ValueError(f"Unsupported market_type '{leg.market_type}' (expected h2h/spreads/totals)")


