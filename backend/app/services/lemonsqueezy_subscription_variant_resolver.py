"""
Resolve LemonSqueezy variant IDs for subscription/lifetime plans.

Plan definitions live in the DB (`subscription_plans`), but for deployments that
prefer environment-based wiring (or when provider_product_id isn't populated),
we allow mapping plan codes → variant IDs via env vars.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.config import Settings


@dataclass(frozen=True)
class LemonSqueezySubscriptionVariantResolver:
    settings: Settings

    def get_variant_id(self, plan_code: str) -> str | None:
        plan_code = (plan_code or "").strip()
        if not plan_code:
            return None

        mapping: dict[str, str | None] = {
            "PG_PREMIUM_MONTHLY": self.settings.lemonsqueezy_premium_monthly_variant_id,
            "PG_PREMIUM_ANNUAL": self.settings.lemonsqueezy_premium_annual_variant_id,
            "PG_LIFETIME_CARD": self.settings.lemonsqueezy_lifetime_variant_id,
        }
        variant_id = mapping.get(plan_code)
        return (variant_id or "").strip() or None


