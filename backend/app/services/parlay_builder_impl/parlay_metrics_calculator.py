from __future__ import annotations

from typing import Dict, List


class ParlayMetricsCalculator:
    """Computes secondary parlay metrics (EV, upset count, etc.)."""

    def count_upsets(self, legs_data: List[Dict]) -> int:
        """Count plus-money picks (rough proxy for underdogs)."""
        upset_count = 0
        for leg in legs_data:
            odds_str = str(leg.get("odds", "") or "").strip()
            if not odds_str:
                continue
            if odds_str.startswith("+"):
                upset_count += 1
                continue
            # Handles "150" or "-150"
            try:
                odds_val = int(odds_str.replace("+", ""))
                if odds_val > 0:
                    upset_count += 1
            except Exception:
                # Non-fatal: ignore malformed odds strings.
                continue
        return upset_count

    def calculate_parlay_ev(self, legs_data: List[Dict], parlay_prob: float) -> float:
        """
        Calculate expected value (EV) for the parlay.

        EV = (model_prob * decimal_payout) - 1
        """
        if not legs_data or parlay_prob <= 0:
            return 0.0

        combined_decimal_odds = 1.0
        for leg in legs_data:
            combined_decimal_odds *= self._american_to_decimal(str(leg.get("odds", "-110")))

        ev = (parlay_prob * combined_decimal_odds) - 1
        return round(ev, 4)

    @staticmethod
    def _american_to_decimal(odds_str: str) -> float:
        """Convert American odds string to decimal odds (best-effort)."""
        try:
            value = int(str(odds_str).strip().replace("+", ""))
            if value > 0:
                return (value / 100) + 1
            return (100 / abs(value)) + 1
        except Exception:
            # Default to -110 (1.909 decimal)
            return 1.909


