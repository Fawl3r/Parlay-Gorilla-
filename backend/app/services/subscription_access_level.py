"""
Types for subscription/access control.

This module exists to keep `subscription_service.py` small and focused on business logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class UserAccessLevel:
    """
    User's current access level and feature permissions.

    Returned by SubscriptionService.get_user_access_level() for use in access control decisions.
    """

    tier: str  # "free" or "premium"
    plan_code: Optional[str]  # e.g., "PG_PREMIUM_MONTHLY", None for free
    can_use_custom_builder: bool
    can_use_upset_finder: bool
    can_use_multi_sport: bool
    can_save_parlays: bool
    max_ai_parlays_per_day: int  # -1 for unlimited
    remaining_ai_parlays_today: int  # -1 for unlimited
    max_custom_parlays_per_day: int  # 0 for free, 15 for premium
    remaining_custom_parlays_today: int  # 0 for free, remaining for premium
    is_lifetime: bool
    subscription_end: Optional[datetime]

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "tier": self.tier,
            "plan_code": self.plan_code,
            "can_use_custom_builder": self.can_use_custom_builder,
            "can_use_upset_finder": self.can_use_upset_finder,
            "can_use_multi_sport": self.can_use_multi_sport,
            "can_save_parlays": self.can_save_parlays,
            "max_ai_parlays_per_day": self.max_ai_parlays_per_day,
            "remaining_ai_parlays_today": self.remaining_ai_parlays_today,
            "unlimited_ai_parlays": self.max_ai_parlays_per_day == -1,
            "max_custom_parlays_per_day": self.max_custom_parlays_per_day,
            "remaining_custom_parlays_today": self.remaining_custom_parlays_today,
            "is_lifetime": self.is_lifetime,
            "subscription_end": self.subscription_end.isoformat() if self.subscription_end else None,
        }


# Default free tier access (fallback-safe)
FREE_ACCESS = UserAccessLevel(
    tier="free",
    plan_code=None,
    can_use_custom_builder=False,
    can_use_upset_finder=False,
    can_use_multi_sport=False,
    can_save_parlays=False,
    max_ai_parlays_per_day=1,
    remaining_ai_parlays_today=1,  # Will be updated based on usage
    max_custom_parlays_per_day=0,
    remaining_custom_parlays_today=0,
    is_lifetime=False,
    subscription_end=None,
)


