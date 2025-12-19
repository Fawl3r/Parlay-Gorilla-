"""Add crypto monthly/annual (time-based) plans + card lifetime plan.

Revision ID: 018_add_crypto_time_based_and_card_lifetime_plans
Revises: 017_add_promo_codes
Create Date: 2025-12-19
"""

from __future__ import annotations

from alembic import op


# revision identifiers, used by Alembic.
revision = "018_add_crypto_time_based_and_card_lifetime_plans"
down_revision = "017_add_promo_codes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # NOTE: We use Postgres' ON CONFLICT to safely upsert plan rows by code.
    op.execute(
        """
        INSERT INTO subscription_plans (
            id, code, name, description, price_cents, currency, billing_cycle, provider,
            provider_product_id, provider_price_id,
            is_active, is_featured, max_ai_parlays_per_day, can_use_custom_builder,
            can_use_upset_finder, can_use_multi_sport, can_save_parlays, ad_free, display_order
        ) VALUES
        (
            gen_random_uuid(), 'PG_PREMIUM_MONTHLY_CRYPTO', 'Gorilla Premium Monthly (Crypto)',
            'Monthly premium access paid with crypto. Does not auto-renew — renew manually each month.',
            1999, 'USD', 'monthly', 'coinbase',
            NULL, NULL,
            true, false, -1, true, true, true, true, true, 4
        ),
        (
            gen_random_uuid(), 'PG_PREMIUM_ANNUAL_CRYPTO', 'Gorilla Premium Annual (Crypto)',
            'Annual premium access paid with crypto. Does not auto-renew — renew manually each year.',
            19999, 'USD', 'annual', 'coinbase',
            NULL, NULL,
            true, false, -1, true, true, true, true, true, 5
        ),
        (
            gen_random_uuid(), 'PG_LIFETIME_CARD', 'Gorilla Lifetime (Card)',
            'One-time payment for lifetime access to all premium features. Pay with card. Never pay again!',
            50000, 'USD', 'lifetime', 'lemonsqueezy',
            NULL, NULL,
            true, true, -1, true, true, true, true, true, 6
        )
        ON CONFLICT (code) DO UPDATE SET
            name = EXCLUDED.name,
            description = EXCLUDED.description,
            price_cents = EXCLUDED.price_cents,
            currency = EXCLUDED.currency,
            billing_cycle = EXCLUDED.billing_cycle,
            provider = EXCLUDED.provider,
            is_active = EXCLUDED.is_active,
            is_featured = EXCLUDED.is_featured,
            max_ai_parlays_per_day = EXCLUDED.max_ai_parlays_per_day,
            can_use_custom_builder = EXCLUDED.can_use_custom_builder,
            can_use_upset_finder = EXCLUDED.can_use_upset_finder,
            can_use_multi_sport = EXCLUDED.can_use_multi_sport,
            can_save_parlays = EXCLUDED.can_save_parlays,
            ad_free = EXCLUDED.ad_free,
            display_order = EXCLUDED.display_order;
        """
    )

    # Ensure crypto lifetime plan is aligned to $500 when present.
    op.execute(
        """
        UPDATE subscription_plans
        SET price_cents = 50000
        WHERE code = 'PG_LIFETIME';
        """
    )


def downgrade() -> None:
    op.execute("DELETE FROM subscription_plans WHERE code IN ('PG_PREMIUM_MONTHLY_CRYPTO', 'PG_PREMIUM_ANNUAL_CRYPTO', 'PG_LIFETIME_CARD');")


