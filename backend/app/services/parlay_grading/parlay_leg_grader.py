from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from app.models.game_results import GameResult
from app.services.parlay_grading.types import ParlayLegStatus, ParsedLeg


@dataclass(frozen=True)
class GradedLeg:
    status: ParlayLegStatus
    hit: Optional[bool]  # True/False for hit/missed, None for push/pending
    notes: str

    # Helpful for UI/debug: always include final score when available.
    home_score: Optional[int]
    away_score: Optional[int]

    # Optional line info
    line: Optional[float]
    selection: str

    def as_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "hit": self.hit,
            "notes": self.notes,
            "home_score": self.home_score,
            "away_score": self.away_score,
            "line": self.line,
            "selection": self.selection,
        }


class ParlayLegGrader:
    """Grades a single leg using a final `GameResult` (hit/missed/push/pending)."""

    def grade(self, *, parsed_leg: ParsedLeg, game_result: Optional[GameResult]) -> GradedLeg:
        if game_result is None:
            return self._pending(parsed_leg, reason="game_result_missing")
        if game_result.home_score is None or game_result.away_score is None:
            return self._pending(parsed_leg, reason="score_missing")

        market_type = (parsed_leg.market_type or "").lower().strip()
        if market_type == "h2h":
            return self._grade_h2h(parsed_leg, game_result)
        if market_type == "spreads":
            return self._grade_spreads(parsed_leg, game_result)
        if market_type == "totals":
            return self._grade_totals(parsed_leg, game_result)
        return self._pending(parsed_leg, reason="unsupported_market_type")

    def _grade_h2h(self, parsed_leg: ParsedLeg, game_result: GameResult) -> GradedLeg:
        selection = (parsed_leg.selection or "").lower().strip()
        home = int(game_result.home_score or 0)
        away = int(game_result.away_score or 0)

        if home == away:
            if selection == "draw":
                return self._hit(parsed_leg, game_result, notes="draw")
            return self._push(parsed_leg, game_result, notes="tie_game")

        winner = "home" if home > away else "away"
        if selection == winner:
            return self._hit(parsed_leg, game_result, notes="winner_correct")
        if selection == "draw":
            return self._miss(parsed_leg, game_result, notes="not_a_draw")
        return self._miss(parsed_leg, game_result, notes="winner_incorrect")

    def _grade_spreads(self, parsed_leg: ParsedLeg, game_result: GameResult) -> GradedLeg:
        selection = (parsed_leg.selection or "").lower().strip()
        line = parsed_leg.line
        if selection not in {"home", "away"} or line is None:
            return self._pending(parsed_leg, reason="spread_parse_failed", game_result=game_result)

        home = float(game_result.home_score or 0)
        away = float(game_result.away_score or 0)

        if selection == "home":
            adjusted = home + float(line)
            opponent = away
        else:
            adjusted = away + float(line)
            opponent = home

        if adjusted > opponent:
            return self._hit(parsed_leg, game_result, notes="covered")
        if adjusted < opponent:
            return self._miss(parsed_leg, game_result, notes="did_not_cover")
        return self._push(parsed_leg, game_result, notes="push")

    def _grade_totals(self, parsed_leg: ParsedLeg, game_result: GameResult) -> GradedLeg:
        selection = (parsed_leg.selection or "").lower().strip()
        line = parsed_leg.line
        if selection not in {"over", "under"} or line is None:
            return self._pending(parsed_leg, reason="total_parse_failed", game_result=game_result)

        home = float(game_result.home_score or 0)
        away = float(game_result.away_score or 0)
        total = home + away

        if total > float(line):
            outcome = "over"
        elif total < float(line):
            outcome = "under"
        else:
            outcome = "push"

        if outcome == "push":
            return self._push(parsed_leg, game_result, notes="push")
        if selection == outcome:
            return self._hit(parsed_leg, game_result, notes="total_correct")
        return self._miss(parsed_leg, game_result, notes="total_incorrect")

    def _pending(
        self,
        parsed_leg: ParsedLeg,
        *,
        reason: str,
        game_result: Optional[GameResult] = None,
    ) -> GradedLeg:
        home_score = int(game_result.home_score) if game_result and game_result.home_score is not None else None
        away_score = int(game_result.away_score) if game_result and game_result.away_score is not None else None
        return GradedLeg(
            status=ParlayLegStatus.pending,
            hit=None,
            notes=reason,
            home_score=home_score,
            away_score=away_score,
            line=parsed_leg.line,
            selection=parsed_leg.selection,
        )

    def _hit(self, parsed_leg: ParsedLeg, game_result: GameResult, *, notes: str) -> GradedLeg:
        return GradedLeg(
            status=ParlayLegStatus.hit,
            hit=True,
            notes=notes,
            home_score=int(game_result.home_score) if game_result.home_score is not None else None,
            away_score=int(game_result.away_score) if game_result.away_score is not None else None,
            line=parsed_leg.line,
            selection=parsed_leg.selection,
        )

    def _miss(self, parsed_leg: ParsedLeg, game_result: GameResult, *, notes: str) -> GradedLeg:
        return GradedLeg(
            status=ParlayLegStatus.missed,
            hit=False,
            notes=notes,
            home_score=int(game_result.home_score) if game_result.home_score is not None else None,
            away_score=int(game_result.away_score) if game_result.away_score is not None else None,
            line=parsed_leg.line,
            selection=parsed_leg.selection,
        )

    def _push(self, parsed_leg: ParsedLeg, game_result: GameResult, *, notes: str) -> GradedLeg:
        return GradedLeg(
            status=ParlayLegStatus.push,
            hit=None,
            notes=notes,
            home_score=int(game_result.home_score) if game_result.home_score is not None else None,
            away_score=int(game_result.away_score) if game_result.away_score is not None else None,
            line=parsed_leg.line,
            selection=parsed_leg.selection,
        )


