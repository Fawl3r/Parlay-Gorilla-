from __future__ import annotations

import logging
import re
from typing import Dict, List

logger = logging.getLogger(__name__)


class MixedParlayConflictResolver:
    """
    Detects mutually exclusive legs within the same game.

    This is used as a lightweight guardrail to avoid impossible parlays like:
    - Moneyline: home vs away
    - Totals: over vs under (same line)
    - Spreads: same team with opposite spread directions
    - Player props: same player/prop over vs under
    """

    def conflicts_with_selected(self, leg: Dict, selected: List[Dict]) -> bool:
        leg_game_id = leg.get("game_id")
        leg_market_type = str(leg.get("market_type", "") or "").lower()
        leg_outcome = str(leg.get("outcome", "") or "").lower()
        leg_home_team = str(leg.get("home_team", "") or "").lower()
        leg_away_team = str(leg.get("away_team", "") or "").lower()

        for selected_leg in selected:
            if selected_leg.get("game_id") != leg_game_id:
                continue

            selected_market_type = str(selected_leg.get("market_type", "") or "").lower()
            selected_outcome = str(selected_leg.get("outcome", "") or "").lower()
            selected_home_team = str(selected_leg.get("home_team", "") or "").lower()
            selected_away_team = str(selected_leg.get("away_team", "") or "").lower()

            if self._moneyline_conflict(
                leg_market_type,
                selected_market_type,
                leg_outcome,
                selected_outcome,
                leg_home_team,
                selected_home_team,
                leg_away_team,
                selected_away_team,
            ):
                return True

            if self._totals_conflict(leg_market_type, selected_market_type, leg_outcome, selected_outcome):
                return True

            if self._spread_conflict(leg_market_type, selected_market_type, leg_outcome, selected_outcome):
                return True

            if self._player_prop_conflict(leg_market_type, selected_market_type, leg_outcome, selected_outcome):
                return True

        return False

    def remove_conflicting_legs(self, legs: List[Dict]) -> List[Dict]:
        """Remove conflicts by keeping higher-confidence legs first."""
        if len(legs) <= 1:
            return legs

        sorted_legs = sorted(legs, key=lambda x: x.get("confidence_score", 0), reverse=True)
        filtered: List[Dict] = []
        for leg in sorted_legs:
            if not self.conflicts_with_selected(leg, filtered):
                filtered.append(leg)
        return filtered

    @staticmethod
    def _moneyline_conflict(
        leg_market_type: str,
        selected_market_type: str,
        leg_outcome: str,
        selected_outcome: str,
        leg_home_team: str,
        selected_home_team: str,
        leg_away_team: str,
        selected_away_team: str,
    ) -> bool:
        if leg_market_type != "h2h" or selected_market_type != "h2h":
            return False

        opposite = ("home" in leg_outcome and "away" in selected_outcome) or ("away" in leg_outcome and "home" in selected_outcome)
        same_matchup = leg_home_team == selected_home_team and leg_away_team == selected_away_team
        if opposite and same_matchup:
            logger.debug("MixedParlay conflict (moneyline): %s vs %s", leg_outcome, selected_outcome)
            return True
        return False

    @staticmethod
    def _totals_conflict(
        leg_market_type: str,
        selected_market_type: str,
        leg_outcome: str,
        selected_outcome: str,
    ) -> bool:
        totals_types = {"total", "totals", "over_under"}
        if leg_market_type not in totals_types or selected_market_type not in totals_types:
            return False

        leg_is_over = "over" in leg_outcome
        selected_is_over = "over" in selected_outcome
        if leg_is_over == selected_is_over:
            return False

        leg_numbers = re.findall(r"\d+\.?\d*", leg_outcome)
        selected_numbers = re.findall(r"\d+\.?\d*", selected_outcome)
        if not leg_numbers or not selected_numbers:
            return False

        try:
            leg_total = float(leg_numbers[0])
            selected_total = float(selected_numbers[0])
        except Exception:
            return False

        # Allow small difference for different books (e.g., 44.5 vs 45).
        if abs(leg_total - selected_total) <= 1.0:
            logger.debug("MixedParlay conflict (totals): %s vs %s", leg_outcome, selected_outcome)
            return True
        return False

    @staticmethod
    def _spread_conflict(
        leg_market_type: str,
        selected_market_type: str,
        leg_outcome: str,
        selected_outcome: str,
    ) -> bool:
        spread_types = {"spread", "spreads"}
        if leg_market_type not in spread_types or selected_market_type not in spread_types:
            return False

        leg_match = re.search(r"(\w+)\s*([+-]?\d+\.?\d*)", leg_outcome)
        selected_match = re.search(r"(\w+)\s*([+-]?\d+\.?\d*)", selected_outcome)
        if not leg_match or not selected_match:
            return False

        leg_team = leg_match.group(1).lower()
        selected_team = selected_match.group(1).lower()
        try:
            leg_spread = float(leg_match.group(2))
            selected_spread = float(selected_match.group(2))
        except Exception:
            return False

        if leg_team == selected_team and (leg_spread * selected_spread) < 0:
            logger.debug("MixedParlay conflict (spread): %s vs %s", leg_outcome, selected_outcome)
            return True
        return False

    @staticmethod
    def _player_prop_conflict(
        leg_market_type: str,
        selected_market_type: str,
        leg_outcome: str,
        selected_outcome: str,
    ) -> bool:
        prop_types = {"player_prop", "player_props"}
        if leg_market_type not in prop_types or selected_market_type not in prop_types:
            return False

        leg_parts = leg_outcome.split()
        selected_parts = selected_outcome.split()
        if len(leg_parts) < 2 or len(selected_parts) < 2:
            return False

        leg_player = " ".join(leg_parts[:2]).lower()
        selected_player = " ".join(selected_parts[:2]).lower()
        if leg_player != selected_player:
            return False

        leg_is_over = "over" in leg_outcome
        selected_is_over = "over" in selected_outcome
        if leg_is_over == selected_is_over:
            return False

        prop_words = {"points", "rebounds", "assists", "goals", "yards", "tds"}
        leg_prop = next((w for w in leg_parts if w.lower() in prop_words), None)
        selected_prop = next((w for w in selected_parts if w.lower() in prop_words), None)
        if not leg_prop or not selected_prop:
            return False
        if leg_prop.lower() != selected_prop.lower():
            return False

        leg_numbers = re.findall(r"\d+\.?\d*", leg_outcome)
        selected_numbers = re.findall(r"\d+\.?\d*", selected_outcome)
        if not leg_numbers or not selected_numbers:
            return False

        try:
            leg_line = float(leg_numbers[-1])
            selected_line = float(selected_numbers[-1])
        except Exception:
            return False

        if abs(leg_line - selected_line) <= 1.0:
            logger.debug("MixedParlay conflict (player prop): %s vs %s", leg_outcome, selected_outcome)
            return True
        return False




