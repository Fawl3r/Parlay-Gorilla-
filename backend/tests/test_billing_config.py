"""
Tests for the Billing Configuration.

Tests the configuration system for:
- Subscription plans
- Credit packs
- Parlay credit costs
- Helper functions
"""

import pytest
from decimal import Decimal

from app.core.billing_config import (
    # Enums
    SubscriptionPlanId,
    CreditPackId,
    AffiliateTier,
    ParlayType,
    # Data classes
    SubscriptionPlanConfig,
    CreditPackConfig,
    AffiliateTierConfig,
    # Config dictionaries
    SUBSCRIPTION_PLANS,
    CREDIT_PACKS,
    AFFILIATE_TIERS,
    PARLAY_CREDIT_COSTS,
    FREE_PARLAYS_TOTAL,
    COMMISSION_HOLD_DAYS,
    # Helper functions
    get_subscription_plan,
    get_credit_pack,
    get_affiliate_tier,
    get_parlay_credit_cost,
    calculate_tier_for_revenue,
    get_all_subscription_plans,
    get_all_credit_packs,
    get_all_affiliate_tiers,
)


class TestSubscriptionPlans:
    """Tests for subscription plan configuration."""
    
    def test_all_plans_exist(self):
        """Test that all expected plans are defined."""
        assert SubscriptionPlanId.STARTER_MONTHLY.value in SUBSCRIPTION_PLANS
        assert SubscriptionPlanId.ELITE_MONTHLY.value in SUBSCRIPTION_PLANS
        assert SubscriptionPlanId.ELITE_YEARLY.value in SUBSCRIPTION_PLANS
    
    def test_starter_monthly_config(self):
        """Test Starter Monthly plan configuration."""
        plan = SUBSCRIPTION_PLANS[SubscriptionPlanId.STARTER_MONTHLY.value]
        
        assert plan.price == Decimal("19.99")
        assert plan.period == "monthly"
        assert plan.daily_parlay_limit == 5
        assert len(plan.features) > 0
    
    def test_elite_monthly_config(self):
        """Test Elite Monthly plan configuration."""
        plan = SUBSCRIPTION_PLANS[SubscriptionPlanId.ELITE_MONTHLY.value]
        
        assert plan.price == Decimal("39.99")
        assert plan.period == "monthly"
        assert plan.daily_parlay_limit == 15
        assert plan.is_featured is True
    
    def test_elite_yearly_config(self):
        """Test Elite Yearly plan configuration."""
        plan = SUBSCRIPTION_PLANS[SubscriptionPlanId.ELITE_YEARLY.value]
        
        assert plan.price == Decimal("399.99")
        assert plan.period == "yearly"
        assert plan.daily_parlay_limit == 15
        # Yearly should be less than 12 * monthly
        elite_monthly = SUBSCRIPTION_PLANS[SubscriptionPlanId.ELITE_MONTHLY.value]
        assert plan.price < elite_monthly.price * 12
    
    def test_get_subscription_plan(self):
        """Test get_subscription_plan helper function."""
        plan = get_subscription_plan(SubscriptionPlanId.ELITE_MONTHLY.value)
        
        assert plan is not None
        assert plan.id == SubscriptionPlanId.ELITE_MONTHLY.value
    
    def test_get_nonexistent_plan(self):
        """Test get_subscription_plan with invalid ID."""
        plan = get_subscription_plan("nonexistent_plan")
        
        assert plan is None
    
    def test_plan_to_dict(self):
        """Test SubscriptionPlanConfig.to_dict()."""
        plan = SUBSCRIPTION_PLANS[SubscriptionPlanId.STARTER_MONTHLY.value]
        d = plan.to_dict()
        
        assert d["id"] == "starter_monthly"
        assert d["price"] == 19.99
        assert d["price_cents"] == 1999
        assert "features" in d
    
    def test_get_all_subscription_plans(self):
        """Test get_all_subscription_plans helper function."""
        plans = get_all_subscription_plans()
        
        assert len(plans) == 3
        assert all(isinstance(p, dict) for p in plans)


class TestCreditPacks:
    """Tests for credit pack configuration."""
    
    def test_all_packs_exist(self):
        """Test that all expected credit packs are defined."""
        assert CreditPackId.CREDITS_10.value in CREDIT_PACKS
        assert CreditPackId.CREDITS_25.value in CREDIT_PACKS
        assert CreditPackId.CREDITS_50.value in CREDIT_PACKS
        assert CreditPackId.CREDITS_100.value in CREDIT_PACKS
    
    def test_10_credits_pack(self):
        """Test 10 credits pack configuration."""
        pack = CREDIT_PACKS[CreditPackId.CREDITS_10.value]
        
        assert pack.credits == 10
        assert pack.price == Decimal("9.99")
        assert pack.bonus_credits == 0
        assert pack.total_credits == 10
    
    def test_25_credits_pack_is_featured(self):
        """Test that 25 credits pack is featured."""
        pack = CREDIT_PACKS[CreditPackId.CREDITS_25.value]
        
        assert pack.is_featured is True
    
    def test_larger_packs_have_bonuses(self):
        """Test that larger packs have bonus credits."""
        pack_50 = CREDIT_PACKS[CreditPackId.CREDITS_50.value]
        pack_100 = CREDIT_PACKS[CreditPackId.CREDITS_100.value]
        
        assert pack_50.bonus_credits > 0
        assert pack_100.bonus_credits > 0
        # 100 pack should have bigger bonus
        assert pack_100.bonus_credits > pack_50.bonus_credits
    
    def test_price_per_credit_decreases_with_size(self):
        """Test that larger packs have better value."""
        pack_10 = CREDIT_PACKS[CreditPackId.CREDITS_10.value]
        pack_100 = CREDIT_PACKS[CreditPackId.CREDITS_100.value]
        
        assert pack_100.price_per_credit < pack_10.price_per_credit
    
    def test_get_credit_pack(self):
        """Test get_credit_pack helper function."""
        pack = get_credit_pack(CreditPackId.CREDITS_25.value)
        
        assert pack is not None
        assert pack.id == CreditPackId.CREDITS_25.value
    
    def test_get_nonexistent_pack(self):
        """Test get_credit_pack with invalid ID."""
        pack = get_credit_pack("nonexistent_pack")
        
        assert pack is None
    
    def test_pack_to_dict(self):
        """Test CreditPackConfig.to_dict()."""
        pack = CREDIT_PACKS[CreditPackId.CREDITS_50.value]
        d = pack.to_dict()
        
        assert d["id"] == "credits_50"
        assert d["credits"] == 50
        assert d["bonus_credits"] == 5
        assert d["total_credits"] == 55
        assert "price_per_credit" in d
    
    def test_get_all_credit_packs(self):
        """Test get_all_credit_packs helper function."""
        packs = get_all_credit_packs()
        
        assert len(packs) == 4
        assert all(isinstance(p, dict) for p in packs)


class TestParlayCreditCosts:
    """Tests for parlay credit costs."""
    
    def test_standard_parlay_cost(self):
        """Test standard parlay credit cost."""
        cost = PARLAY_CREDIT_COSTS[ParlayType.STANDARD.value]
        assert cost == 1
    
    def test_elite_parlay_cost(self):
        """Test elite parlay credit cost."""
        cost = PARLAY_CREDIT_COSTS[ParlayType.ELITE.value]
        assert cost == 3
    
    def test_get_parlay_credit_cost(self):
        """Test get_parlay_credit_cost helper function."""
        standard = get_parlay_credit_cost(ParlayType.STANDARD.value)
        elite = get_parlay_credit_cost(ParlayType.ELITE.value)
        
        assert standard == 1
        assert elite == 3
    
    def test_get_unknown_parlay_type_defaults_to_standard(self):
        """Test that unknown parlay types default to standard cost."""
        cost = get_parlay_credit_cost("unknown_type")
        
        assert cost == 1  # Default to standard


class TestAffiliateTiers:
    """Tests for affiliate tier configuration."""
    
    def test_all_tiers_exist(self):
        """Test that all expected tiers are defined."""
        assert AffiliateTier.ROOKIE.value in AFFILIATE_TIERS
        assert AffiliateTier.PRO.value in AFFILIATE_TIERS
        assert AffiliateTier.ALL_STAR.value in AFFILIATE_TIERS
        assert AffiliateTier.HALL_OF_FAME.value in AFFILIATE_TIERS
    
    def test_rookie_tier_config(self):
        """Test Rookie tier configuration."""
        tier = AFFILIATE_TIERS[AffiliateTier.ROOKIE.value]
        
        assert tier.revenue_threshold == Decimal("0")
        assert tier.commission_rate_sub_first == Decimal("0.20")
        assert tier.commission_rate_sub_recurring == Decimal("0.00")
        assert tier.commission_rate_credits == Decimal("0.20")

    def test_hall_of_fame_first_sub_rate_is_40_percent(self):
        """Hall of Fame earns 40% on first-ever subscription payments."""
        tier = AFFILIATE_TIERS[AffiliateTier.HALL_OF_FAME.value]
        assert tier.commission_rate_sub_first == Decimal("0.40")
    
    def test_tier_thresholds_increase(self):
        """Test that tier revenue thresholds increase."""
        rookie = AFFILIATE_TIERS[AffiliateTier.ROOKIE.value]
        pro = AFFILIATE_TIERS[AffiliateTier.PRO.value]
        all_star = AFFILIATE_TIERS[AffiliateTier.ALL_STAR.value]
        hall_of_fame = AFFILIATE_TIERS[AffiliateTier.HALL_OF_FAME.value]
        
        assert rookie.revenue_threshold < pro.revenue_threshold
        assert pro.revenue_threshold < all_star.revenue_threshold
        assert all_star.revenue_threshold < hall_of_fame.revenue_threshold
    
    def test_credit_rates_increase_with_tier(self):
        """Test that credit commission rates increase with tier."""
        rookie = AFFILIATE_TIERS[AffiliateTier.ROOKIE.value]
        hall_of_fame = AFFILIATE_TIERS[AffiliateTier.HALL_OF_FAME.value]
        
        assert hall_of_fame.commission_rate_credits > rookie.commission_rate_credits
    
    def test_get_affiliate_tier(self):
        """Test get_affiliate_tier helper function."""
        tier = get_affiliate_tier(AffiliateTier.PRO.value)
        
        assert tier is not None
        assert tier.tier == AffiliateTier.PRO
    
    def test_tier_to_dict(self):
        """Test AffiliateTierConfig.to_dict()."""
        tier = AFFILIATE_TIERS[AffiliateTier.ALL_STAR.value]
        d = tier.to_dict()
        
        assert d["tier"] == "all_star"
        assert d["name"] == "All-Star"
        assert d["revenue_threshold"] == 1000.0
        assert "badge_color" in d
    
    def test_get_all_affiliate_tiers(self):
        """Test get_all_affiliate_tiers helper function."""
        tiers = get_all_affiliate_tiers()
        
        assert len(tiers) == 4
        assert all(isinstance(t, dict) for t in tiers)


class TestGlobalConfig:
    """Tests for global configuration values."""
    
    def test_free_parlays_total(self):
        """Test free parlays total configuration."""
        assert FREE_PARLAYS_TOTAL == 2
    
    def test_commission_hold_days(self):
        """Test commission hold period configuration."""
        assert COMMISSION_HOLD_DAYS == 30


class TestCalculateTierForRevenue:
    """Tests for calculate_tier_for_revenue function."""
    
    def test_zero_revenue_returns_rookie(self):
        """Test $0 revenue returns Rookie tier."""
        tier = calculate_tier_for_revenue(Decimal("0"))
        assert tier.tier == AffiliateTier.ROOKIE
    
    def test_199_revenue_returns_rookie(self):
        """Test $199 revenue returns Rookie tier."""
        tier = calculate_tier_for_revenue(Decimal("199.99"))
        assert tier.tier == AffiliateTier.ROOKIE
    
    def test_200_revenue_returns_pro(self):
        """Test $200 revenue returns Pro tier."""
        tier = calculate_tier_for_revenue(Decimal("200"))
        assert tier.tier == AffiliateTier.PRO
    
    def test_999_revenue_returns_pro(self):
        """Test $999 revenue returns Pro tier."""
        tier = calculate_tier_for_revenue(Decimal("999.99"))
        assert tier.tier == AffiliateTier.PRO
    
    def test_1000_revenue_returns_all_star(self):
        """Test $1000 revenue returns All-Star tier."""
        tier = calculate_tier_for_revenue(Decimal("1000"))
        assert tier.tier == AffiliateTier.ALL_STAR
    
    def test_4999_revenue_returns_all_star(self):
        """Test $4999 revenue returns All-Star tier."""
        tier = calculate_tier_for_revenue(Decimal("4999.99"))
        assert tier.tier == AffiliateTier.ALL_STAR
    
    def test_5000_revenue_returns_hall_of_fame(self):
        """Test $5000 revenue returns Hall of Fame tier."""
        tier = calculate_tier_for_revenue(Decimal("5000"))
        assert tier.tier == AffiliateTier.HALL_OF_FAME
    
    def test_large_revenue_returns_hall_of_fame(self):
        """Test large revenue returns Hall of Fame tier."""
        tier = calculate_tier_for_revenue(Decimal("100000"))
        assert tier.tier == AffiliateTier.HALL_OF_FAME



