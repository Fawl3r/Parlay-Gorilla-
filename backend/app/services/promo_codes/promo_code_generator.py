"""Promo code generation utilities."""

from __future__ import annotations

import secrets

from app.models.promo_code import PromoRewardType


class PromoCodeGenerator:
    """
    Generates human-shareable, case-insensitive promo codes.

    Format:
    - Premium month: PG1M-XXXX-XXXX
    - 3 credits:     PG3C-XXXX-XXXX
    """

    _ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # Avoid 0/O and 1/I

    def generate(self, reward_type: PromoRewardType) -> str:
        prefix = self._prefix_for_reward(reward_type)
        return f"{prefix}-{self._segment(4)}-{self._segment(4)}"

    @classmethod
    def normalize(cls, code: str) -> str:
        return (code or "").strip().upper()

    def _segment(self, length: int) -> str:
        return "".join(secrets.choice(self._ALPHABET) for _ in range(length))

    @staticmethod
    def _prefix_for_reward(reward_type: PromoRewardType) -> str:
        if reward_type == PromoRewardType.premium_month:
            return "PG1M"
        return "PG3C"


