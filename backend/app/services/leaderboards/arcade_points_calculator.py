"""Arcade points calculator - pure business logic for tiered scoring.

Tiered arcade points system:
- 5 legs = 100 points
- 6 legs = 140 points
- 7 legs = 200 points
- 8 legs = 280 points
- 9 legs = 400 points
- 10 legs = 560 points
- 11+ legs = +25% per extra leg (rounded, capped per win)
"""

from __future__ import annotations


class ArcadePointsCalculator:
    """Calculate arcade points for verified winning parlays."""

    # Tiered base points
    TIER_POINTS = {
        5: 100,
        6: 140,
        7: 200,
        8: 280,
        9: 400,
        10: 560,
    }

    # Multiplier for 11+ legs
    MULTIPLIER_11_PLUS = 1.25

    # Cap per win (safety limit)
    MAX_POINTS_PER_WIN = 10000

    @classmethod
    def calculate_points(cls, num_legs: int) -> int:
        """
        Calculate points for a parlay with the given number of legs.

        Args:
            num_legs: Number of legs in the parlay (must be >= 5)

        Returns:
            Points awarded (0 if < 5 legs)
        """
        if num_legs < 5:
            return 0

        # Use tiered points for 5-10 legs
        if num_legs in cls.TIER_POINTS:
            return cls.TIER_POINTS[num_legs]

        # For 11+ legs: start from 10-leg base, multiply by 1.25 for each extra leg
        base_points = cls.TIER_POINTS[10]
        extra_legs = num_legs - 10
        points = base_points

        for _ in range(extra_legs):
            points = int(points * cls.MULTIPLIER_11_PLUS)

        # Apply cap
        return min(points, cls.MAX_POINTS_PER_WIN)

    @classmethod
    def is_eligible(cls, num_legs: int) -> bool:
        """Check if a parlay is eligible for points (5+ legs)."""
        return num_legs >= 5

