from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from app.services.team_name_normalizer import TeamNameNormalizer
from app.services.parlay_grading.types import ParsedLeg


@dataclass(frozen=True)
class ParsedLegOrError:
    parsed: Optional[ParsedLeg]
    error: Optional[str]


class AiLegInputParser:
    """Parse an AI-generated leg (from `Parlay.legs`) into a grading-ready shape."""

    def __init__(self, normalizer: Optional[TeamNameNormalizer] = None):
        self._normalizer = normalizer or TeamNameNormalizer()

    def parse(self, leg: Dict[str, Any], *, home_team: str, away_team: str) -> ParsedLegOrError:
        market_type = str(leg.get("market_type") or "").lower().strip()
        outcome = str(leg.get("outcome") or "").strip()

        if not market_type:
            return ParsedLegOrError(parsed=None, error="missing_market_type")

        if market_type == "h2h":
            selection = self._parse_h2h_selection(outcome, home_team=home_team, away_team=away_team)
            if not selection:
                return ParsedLegOrError(parsed=None, error="unrecognized_h2h_outcome")
            return ParsedLegOrError(
                parsed=ParsedLeg(market_type="h2h", selection=selection, line=None, raw=leg),
                error=None,
            )

        if market_type == "spreads":
            selection, line = self._parse_spread_outcome(outcome, home_team=home_team, away_team=away_team)
            if not selection or line is None:
                return ParsedLegOrError(parsed=None, error="unrecognized_spread_outcome")
            return ParsedLegOrError(
                parsed=ParsedLeg(market_type="spreads", selection=selection, line=line, raw=leg),
                error=None,
            )

        if market_type == "totals":
            selection, line = self._parse_total_outcome(outcome)
            if not selection or line is None:
                return ParsedLegOrError(parsed=None, error="unrecognized_total_outcome")
            return ParsedLegOrError(
                parsed=ParsedLeg(market_type="totals", selection=selection, line=line, raw=leg),
                error=None,
            )

        return ParsedLegOrError(parsed=None, error="unsupported_market_type")

    def _parse_h2h_selection(self, outcome: str, *, home_team: str, away_team: str) -> Optional[str]:
        o = (outcome or "").strip().lower()
        if o in {"home", "away", "draw"}:
            return o

        # Some legacy/seed data may store actual team names as the outcome.
        out_norm = self._normalizer.normalize(outcome)
        home_norm = self._normalizer.normalize(home_team)
        away_norm = self._normalizer.normalize(away_team)
        if out_norm and out_norm == home_norm:
            return "home"
        if out_norm and out_norm == away_norm:
            return "away"
        if out_norm in {"draw", "tie"}:
            return "draw"
        return None

    def _parse_spread_outcome(self, outcome: str, *, home_team: str, away_team: str) -> Tuple[Optional[str], Optional[float]]:
        line = _extract_first_float(outcome)
        if line is None:
            return None, None

        # Odds API stores outcome like: "{Team Name} -3.5" or "{Team Name} +3.5"
        out_norm = self._normalizer.normalize(outcome)
        home_norm = self._normalizer.normalize(home_team)
        away_norm = self._normalizer.normalize(away_team)

        # Prefer prefix match (matches existing usage in CandidateLegService).
        if out_norm.startswith(home_norm) and home_norm:
            return "home", float(line)
        if out_norm.startswith(away_norm) and away_norm:
            return "away", float(line)

        # Fallback: contains match.
        if home_norm and home_norm in out_norm:
            return "home", float(line)
        if away_norm and away_norm in out_norm:
            return "away", float(line)

        return None, None

    @staticmethod
    def _parse_total_outcome(outcome: str) -> Tuple[Optional[str], Optional[float]]:
        s = (outcome or "").strip().lower()
        if s.startswith("over"):
            return "over", _extract_first_float(s)
        if s.startswith("under"):
            return "under", _extract_first_float(s)
        # Fallback if Odds API used uppercase.
        if s.startswith("o"):
            return "over", _extract_first_float(s)
        if s.startswith("u"):
            return "under", _extract_first_float(s)
        return None, None


class CustomLegInputParser:
    """Parse a custom parlay leg (from `SavedParlay.legs`) into a grading-ready shape."""

    def __init__(self, normalizer: Optional[TeamNameNormalizer] = None):
        self._normalizer = normalizer or TeamNameNormalizer()

    def parse(self, leg: Dict[str, Any], *, home_team: str, away_team: str) -> ParsedLegOrError:
        market_type = str(leg.get("market_type") or "").lower().strip()
        pick = str(leg.get("pick") or "").strip()
        point = leg.get("point", None)

        if market_type not in {"h2h", "spreads", "totals"}:
            return ParsedLegOrError(parsed=None, error="unsupported_market_type")

        if market_type == "h2h":
            selection = self._parse_team_side(pick, home_team=home_team, away_team=away_team, allow_draw=True)
            if not selection:
                return ParsedLegOrError(parsed=None, error="unrecognized_h2h_pick")
            return ParsedLegOrError(
                parsed=ParsedLeg(market_type="h2h", selection=selection, line=None, raw=leg),
                error=None,
            )

        if market_type == "spreads":
            selection = self._parse_team_side(pick, home_team=home_team, away_team=away_team, allow_draw=False)
            line = _coerce_float(point) if point is not None else _extract_first_float(pick)
            if not selection or line is None:
                return ParsedLegOrError(parsed=None, error="unrecognized_spread_pick")
            return ParsedLegOrError(
                parsed=ParsedLeg(market_type="spreads", selection=selection, line=float(line), raw=leg),
                error=None,
            )

        # totals
        sel = (pick or "").strip().lower()
        if sel not in {"over", "under"}:
            # allow strings like "Over 44.5"
            if sel.startswith("over"):
                sel = "over"
            elif sel.startswith("under"):
                sel = "under"
        line = _coerce_float(point) if point is not None else _extract_first_float(pick)
        if sel not in {"over", "under"} or line is None:
            return ParsedLegOrError(parsed=None, error="unrecognized_total_pick")
        return ParsedLegOrError(
            parsed=ParsedLeg(market_type="totals", selection=sel, line=float(line), raw=leg),
            error=None,
        )

    def _parse_team_side(self, pick: str, *, home_team: str, away_team: str, allow_draw: bool) -> Optional[str]:
        p = (pick or "").strip().lower()
        if p in {"home", "away"}:
            return p
        if allow_draw and p in {"draw", "tie"}:
            return "draw"

        p_norm = self._normalizer.normalize(pick)
        home_norm = self._normalizer.normalize(home_team)
        away_norm = self._normalizer.normalize(away_team)
        if p_norm and p_norm == home_norm:
            return "home"
        if p_norm and p_norm == away_norm:
            return "away"
        return None


_FLOAT_RE = re.compile(r"[+-]?\d+(?:\.\d+)?")


def _extract_first_float(text: str) -> Optional[float]:
    if not text:
        return None
    match = _FLOAT_RE.search(str(text))
    if not match:
        return None
    try:
        return float(match.group(0))
    except Exception:
        return None


def _coerce_float(value: Any) -> Optional[float]:
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


