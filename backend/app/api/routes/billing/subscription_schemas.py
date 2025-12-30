"""
Pydantic schemas for subscription/billing routes.

Kept separate from `subscription_routes.py` to keep route modules smaller and
easier to maintain.
"""

from __future__ import annotations

from pydantic import BaseModel
from typing import Optional


class CheckoutRequest(BaseModel):
    plan_code: str


class CheckoutResponse(BaseModel):
    checkout_url: str
    provider: str
    plan_code: str


class AiParlaysBalance(BaseModel):
    """AI parlay allowance balance (rolling period for premium; daily for free tier)."""

    monthly_limit: int
    used: int
    remaining: int


class CustomAiParlaysBalance(BaseModel):
    """Custom AI allowance balance (rolling period for premium; unavailable for free tier)."""

    monthly_limit: int
    used: int
    remaining: int
    inscription_cost_usd: float
    requires_manual_opt_in: bool


class SubscriptionBalancesResponse(BaseModel):
    credit_balance: int

    free_parlays_total: int
    free_parlays_used: int
    free_parlays_remaining: int

    # Legacy naming retained for backwards compatibility. For premium, these represent
    # the rolling-period limit/remaining.
    daily_ai_limit: int
    daily_ai_used: int
    daily_ai_remaining: int

    premium_ai_parlays_used: int
    premium_ai_period_start: Optional[str]

    # Premium custom builder (rolling period)
    premium_custom_builder_used: int
    premium_custom_builder_limit: int
    premium_custom_builder_remaining: int
    premium_custom_builder_period_start: Optional[str]

    # Premium inscriptions (rolling period)
    premium_inscriptions_used: int
    premium_inscriptions_limit: int
    premium_inscriptions_remaining: int
    premium_inscriptions_period_start: Optional[str]

    # New explicit balances (preferred by UI).
    ai_parlays: AiParlaysBalance
    custom_ai_parlays: CustomAiParlaysBalance


class SubscriptionStatusResponse(BaseModel):
    tier: str
    plan_code: Optional[str]
    can_use_custom_builder: bool
    can_use_upset_finder: bool
    can_use_multi_sport: bool
    can_save_parlays: bool
    max_ai_parlays_per_day: int
    remaining_ai_parlays_today: int
    unlimited_ai_parlays: bool
    credit_balance: int
    is_lifetime: bool
    subscription_end: Optional[str]
    balances: SubscriptionBalancesResponse


class PlanResponse(BaseModel):
    id: str
    code: str
    name: str
    description: Optional[str]
    price_cents: int
    price_dollars: float
    currency: str
    billing_cycle: str
    provider: str
    is_active: bool
    is_featured: bool
    is_free: bool
    is_lifetime: bool
    features: dict


