"""
User context builder for Gorilla Bot.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.subscription_service import SubscriptionService


@dataclass(frozen=True)
class GorillaBotUserContext:
    plan_tier: str
    credits: int
    ai_parlays_remaining: int
    custom_parlays_remaining: int
    email_verified: bool
    profile_completed: bool
    default_risk_profile: str
    favorite_sports: List[str]

    def to_prompt_lines(self) -> List[str]:
        return [
            f"plan_tier: {self.plan_tier}",
            f"credits: {self.credits}",
            f"ai_parlays_remaining: {self.ai_parlays_remaining}",
            f"custom_parlays_remaining: {self.custom_parlays_remaining}",
            f"email_verified: {self.email_verified}",
            f"profile_completed: {self.profile_completed}",
            f"default_risk_profile: {self.default_risk_profile}",
            f"favorite_sports: {', '.join(self.favorite_sports) if self.favorite_sports else 'none'}",
        ]


class GorillaBotUserContextBuilder:
    """Builds a minimal, privacy-safe user context for Gorilla Bot prompts."""

    def __init__(self, db: AsyncSession):
        self._db = db
        self._subscription_service = SubscriptionService(db)

    async def build(self, user: User) -> GorillaBotUserContext:
        access_level = await self._subscription_service.get_user_access_level(str(user.id))
        ai_remaining = int(access_level.remaining_ai_parlays_today or 0)
        custom_remaining = int(access_level.remaining_custom_parlays_today or 0)
        return GorillaBotUserContext(
            plan_tier=str(access_level.tier or "free"),
            credits=int(getattr(user, "credit_balance", 0) or 0),
            ai_parlays_remaining=ai_remaining,
            custom_parlays_remaining=custom_remaining,
            email_verified=bool(getattr(user, "email_verified", False)),
            profile_completed=bool(getattr(user, "profile_completed", False)),
            default_risk_profile=str(getattr(user, "default_risk_profile", "balanced") or "balanced"),
            favorite_sports=list(getattr(user, "favorite_sports", []) or []),
        )
