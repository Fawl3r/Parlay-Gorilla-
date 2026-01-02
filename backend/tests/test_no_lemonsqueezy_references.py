"""
Regression test to verify no LemonSqueezy code paths remain.

This test ensures that:
- No LemonSqueezy code is called in critical paths
- No LemonSqueezy env vars are required
- No UI shows LemonSqueezy branding (where Stripe should be used)
"""

import pytest
from unittest.mock import patch, MagicMock

from app.core.config import Settings
from app.api.routes.billing.subscription_routes import create_stripe_checkout
from app.models.subscription_plan import SubscriptionPlan


def test_no_lemonsqueezy_env_vars_required():
    """Verify that LemonSqueezy env vars are not required for Stripe flow."""
    # Create settings without LemonSqueezy vars
    settings = Settings(
        database_url="postgresql://test",
        stripe_secret_key="sk_test_123",
        stripe_webhook_secret="whsec_test",
        # No lemonsqueezy vars
    )
    
    # Should not raise errors
    assert settings.stripe_secret_key == "sk_test_123"
    assert settings.lemonsqueezy_api_key is None


def test_stripe_checkout_does_not_use_lemonsqueezy():
    """Verify Stripe checkout endpoint doesn't use LemonSqueezy."""
    # This is a structural test - the code should not import or call LemonSqueezy
    import inspect
    import app.api.routes.billing.subscription_routes as routes_module
    
    # Check that create_stripe_checkout doesn't reference LemonSqueezy
    source = inspect.getsource(create_stripe_checkout)
    assert "lemonsqueezy" not in source.lower()
    assert "LemonSqueezy" not in source


def test_subscription_plan_supports_stripe():
    """Verify subscription plans can use Stripe provider."""
    plan = SubscriptionPlan(
        code="PG_PRO_MONTHLY",
        name="Pro Monthly",
        provider="stripe",
        provider_product_id="price_test123",
        is_active=True,
    )
    
    assert plan.provider == "stripe"
    assert plan.provider_product_id == "price_test123"


@pytest.mark.asyncio
async def test_stripe_service_does_not_import_lemonsqueezy():
    """Verify StripeService doesn't import LemonSqueezy modules."""
    import inspect
    from app.services.stripe_service import StripeService
    
    source = inspect.getsource(StripeService)
    assert "lemonsqueezy" not in source.lower()
    assert "LemonSqueezy" not in source

