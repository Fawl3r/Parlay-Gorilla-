"""
Entitlement service: parlay suggest access and entitlements payload for UI.

Single source of truth for:
- get_parlay_suggest_access(user, mix_sports) -> allowed, reason, features, credits_remaining
- get_entitlements_for_user(user_or_none) -> EntitlementsResponse for GET /api/me/entitlements
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import User
from app.schemas.entitlements import (
    EntitlementsCredits,
    EntitlementsFeatures,
    EntitlementsResponse,
)
from app.services.subscription_service import SubscriptionService

logger = logging.getLogger(__name__)


@dataclass
class ParlaySuggestAccess:
    """Result of get_parlay_suggest_access."""
    allowed: bool
    reason: Optional[str]  # login_required | premium_required | credits_required | None
    features: dict
    credits_remaining: int


class EntitlementService:
    """
    Service for resolving user entitlements and parlay-suggest access.

    Rules:
    - No user => not allowed, reason=login_required
    - Mix sports requested and user not premium => not allowed, reason=premium_required
    - User has no free quota and no credits => not allowed, reason=credits_required
    - Else allowed (subject to existing check_parlay_access_with_purchase for limits)
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self._subscription = SubscriptionService(db)

    async def get_parlay_suggest_access(
        self,
        user: Optional[User],
        mix_sports_requested: bool,
    ) -> ParlaySuggestAccess:
        """
        Determine if user can call POST /api/parlay/suggest.

        Returns allowed=True if they can attempt generation (limit check is done separately).
        """
        if user is None:
            return ParlaySuggestAccess(
                allowed=False,
                reason="login_required",
                features={"mix_sports": False, "max_legs": 5, "player_props": False},
                credits_remaining=0,
            )

        user_id = str(user.id)
        is_premium = await self._subscription.is_user_premium(user_id)
        credits_balance = int(getattr(user, "credit_balance", 0) or 0)
        remaining_free = await self._subscription.get_remaining_free_parlays(user_id)
        credits_cost = int(getattr(settings, "credits_cost_ai_parlay", 3))

        features = {
            "mix_sports": is_premium,
            "max_legs": 20 if is_premium else 5,
            "player_props": is_premium,
        }

        if mix_sports_requested and not is_premium:
            return ParlaySuggestAccess(
                allowed=False,
                reason="premium_required",
                features=features,
                credits_remaining=credits_balance,
            )

        if remaining_free <= 0 and credits_balance < credits_cost:
            return ParlaySuggestAccess(
                allowed=False,
                reason="credits_required",
                features=features,
                credits_remaining=credits_balance,
            )

        return ParlaySuggestAccess(
            allowed=True,
            reason=None,
            features=features,
            credits_remaining=credits_balance,
        )

    async def get_entitlements_for_user(self, user: Optional[User]) -> EntitlementsResponse:
        """
        Build entitlements payload for GET /api/me/entitlements.

        Anon: is_authenticated=False, plan=anon, default features/credits.
        """
        if user is None:
            return EntitlementsResponse(
                is_authenticated=False,
                plan="anon",
                credits=EntitlementsCredits(ai_picks_remaining=0, gorilla_builder_remaining=0),
                features=EntitlementsFeatures(mix_sports=False, max_legs=5, player_props=False),
            )

        user_id = str(user.id)
        try:
            is_premium = await self._subscription.is_user_premium(user_id)
        except Exception:
            is_premium = False
        plan = "premium" if is_premium else "free"
        try:
            remaining_ai = await self._subscription.get_remaining_free_parlays(user_id)
        except Exception:
            remaining_ai = 0
        try:
            remaining_custom = (
                await self._subscription.get_remaining_custom_parlays(user_id)
                if is_premium
                else await self._subscription.get_remaining_free_custom_parlays(user_id)
            )
        except Exception:
            remaining_custom = 0

        return EntitlementsResponse(
            is_authenticated=True,
            plan=plan,
            credits=EntitlementsCredits(
                ai_picks_remaining=max(0, remaining_ai),
                gorilla_builder_remaining=max(0, remaining_custom),
            ),
            features=EntitlementsFeatures(
                mix_sports=is_premium,
                max_legs=20 if is_premium else 5,
                player_props=is_premium,
            ),
        )


def get_entitlement_service(db: AsyncSession) -> EntitlementService:
    """Factory for dependency injection."""
    return EntitlementService(db)
