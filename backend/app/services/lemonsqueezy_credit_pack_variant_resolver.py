"""
Resolve LemonSqueezy variant IDs for credit packs.

Credit pack definitions (price/credits) live in `app.core.billing_config`.
Provider-specific wiring (variant IDs) is configured via environment variables
and surfaced through `app.core.config.settings`.
"""

from dataclasses import dataclass

from app.core.config import Settings


@dataclass(frozen=True)
class LemonSqueezyCreditPackVariantResolver:
    settings: Settings

    def get_variant_id(self, credit_pack_id: str) -> str | None:
        credit_pack_id = (credit_pack_id or "").strip()
        if not credit_pack_id:
            return None

        mapping: dict[str, str | None] = {
            "credits_10": self.settings.lemonsqueezy_credits_10_variant_id,
            "credits_25": self.settings.lemonsqueezy_credits_25_variant_id,
            "credits_50": self.settings.lemonsqueezy_credits_50_variant_id,
            "credits_100": self.settings.lemonsqueezy_credits_100_variant_id,
        }
        variant_id = mapping.get(credit_pack_id)
        return (variant_id or "").strip() or None


