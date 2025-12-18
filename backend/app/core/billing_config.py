"""
Billing Configuration for Parlay Gorilla

Central configuration for:
- Subscription plans (monthly/yearly)
- Credit packs (per-use purchases)
- Parlay generation costs
- Affiliate tiers and commission rates

All pricing in USD.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from decimal import Decimal
from enum import Enum


# =============================================================================
# ENUMS
# =============================================================================

class SubscriptionPlanId(str, Enum):
    """Subscription plan identifiers"""
    STARTER_MONTHLY = "starter_monthly"
    ELITE_MONTHLY = "elite_monthly"
    ELITE_YEARLY = "elite_yearly"


class CreditPackId(str, Enum):
    """Credit pack identifiers"""
    CREDITS_10 = "credits_10"
    CREDITS_25 = "credits_25"
    CREDITS_50 = "credits_50"
    CREDITS_100 = "credits_100"


class AffiliateTier(str, Enum):
    """Affiliate tier levels"""
    ROOKIE = "rookie"
    PRO = "pro"
    ALL_STAR = "all_star"
    HALL_OF_FAME = "hall_of_fame"


class ParlayType(str, Enum):
    """Parlay types for credit cost calculation"""
    STANDARD = "standard"
    ELITE = "elite"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class SubscriptionPlanConfig:
    """Configuration for a subscription plan"""
    id: str
    name: str
    description: str
    price: Decimal
    currency: str = "USD"
    period: str = "monthly"  # monthly, yearly
    daily_parlay_limit: int = 5
    features: List[str] = field(default_factory=list)
    is_featured: bool = False
    lemonsqueezy_variant_id: Optional[str] = None
    coinbase_product_id: Optional[str] = None
    
    @property
    def price_cents(self) -> int:
        return int(self.price * 100)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": float(self.price),
            "price_cents": self.price_cents,
            "currency": self.currency,
            "period": self.period,
            "daily_parlay_limit": self.daily_parlay_limit,
            "features": self.features,
            "is_featured": self.is_featured,
        }


@dataclass
class CreditPackConfig:
    """Configuration for a credit pack"""
    id: str
    name: str
    credits: int
    price: Decimal
    currency: str = "USD"
    bonus_credits: int = 0
    is_featured: bool = False
    lemonsqueezy_variant_id: Optional[str] = None
    coinbase_product_id: Optional[str] = None
    
    @property
    def price_cents(self) -> int:
        return int(self.price * 100)
    
    @property
    def total_credits(self) -> int:
        return self.credits + self.bonus_credits
    
    @property
    def price_per_credit(self) -> Decimal:
        return self.price / self.total_credits
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "credits": self.credits,
            "bonus_credits": self.bonus_credits,
            "total_credits": self.total_credits,
            "price": float(self.price),
            "price_cents": self.price_cents,
            "currency": self.currency,
            "price_per_credit": float(self.price_per_credit),
            "is_featured": self.is_featured,
        }


@dataclass
class AffiliateTierConfig:
    """Configuration for an affiliate tier"""
    tier: AffiliateTier
    name: str
    revenue_threshold: Decimal  # Minimum total_referred_revenue to reach this tier
    commission_rate_sub_first: Decimal  # First subscription payment commission
    commission_rate_sub_recurring: Decimal  # Recurring subscription commission
    commission_rate_credits: Decimal  # Credit pack commission
    badge_color: str = "#666666"
    
    def to_dict(self) -> dict:
        return {
            "tier": self.tier.value,
            "name": self.name,
            "revenue_threshold": float(self.revenue_threshold),
            "commission_rate_sub_first": float(self.commission_rate_sub_first),
            "commission_rate_sub_recurring": float(self.commission_rate_sub_recurring),
            "commission_rate_credits": float(self.commission_rate_credits),
            "badge_color": self.badge_color,
        }


# =============================================================================
# SUBSCRIPTION PLANS CONFIGURATION
# =============================================================================

SUBSCRIPTION_PLANS: Dict[str, SubscriptionPlanConfig] = {
    SubscriptionPlanId.STARTER_MONTHLY.value: SubscriptionPlanConfig(
        id=SubscriptionPlanId.STARTER_MONTHLY.value,
        name="Starter Monthly",
        description="Perfect for casual bettors. Get AI-powered parlay analysis with daily limits.",
        price=Decimal("19.99"),
        period="monthly",
        daily_parlay_limit=5,
        features=[
            "5 AI parlays per day",
            "Standard analysis depth",
            "Basic confidence metrics",
            "Parlay history (30 days)",
            "Email support",
        ],
        is_featured=False,
    ),
    SubscriptionPlanId.ELITE_MONTHLY.value: SubscriptionPlanConfig(
        id=SubscriptionPlanId.ELITE_MONTHLY.value,
        name="Elite Monthly",
        description="For serious bettors. Deeper analysis, more parlays, premium features.",
        price=Decimal("39.99"),
        period="monthly",
        daily_parlay_limit=15,
        features=[
            "15 AI parlays per day",
            "Deep analysis with insights",
            "Full confidence breakdowns",
            "Multi-book odds comparison",
            "Live game insights",
            "Telegram alerts",
            "Unlimited parlay history",
            "ROI tracking",
            "Priority support",
            "Ad-free experience",
        ],
        is_featured=True,
    ),
    SubscriptionPlanId.ELITE_YEARLY.value: SubscriptionPlanConfig(
        id=SubscriptionPlanId.ELITE_YEARLY.value,
        name="Elite Yearly",
        description="Best value! Get 2 months free with annual billing.",
        price=Decimal("399.99"),
        period="yearly",
        daily_parlay_limit=15,
        features=[
            "All Elite Monthly features",
            "2 months FREE (save $80)",
            "15 AI parlays per day",
            "Deep analysis with insights",
            "Full confidence breakdowns",
            "Multi-book odds comparison",
            "Live game insights",
            "Telegram alerts",
            "Unlimited parlay history",
            "ROI tracking",
            "Priority support",
            "Ad-free experience",
        ],
        is_featured=False,
    ),
}


# =============================================================================
# CREDIT PACKS CONFIGURATION
# =============================================================================

CREDIT_PACKS: Dict[str, CreditPackConfig] = {
    CreditPackId.CREDITS_10.value: CreditPackConfig(
        id=CreditPackId.CREDITS_10.value,
        name="10 Credits",
        credits=10,
        price=Decimal("9.99"),
        bonus_credits=0,
        is_featured=False,
    ),
    CreditPackId.CREDITS_25.value: CreditPackConfig(
        id=CreditPackId.CREDITS_25.value,
        name="25 Credits",
        credits=25,
        price=Decimal("19.99"),
        bonus_credits=0,
        is_featured=True,  # Best value for most users
    ),
    CreditPackId.CREDITS_50.value: CreditPackConfig(
        id=CreditPackId.CREDITS_50.value,
        name="50 Credits",
        credits=50,
        price=Decimal("34.99"),
        bonus_credits=5,  # 10% bonus
        is_featured=False,
    ),
    CreditPackId.CREDITS_100.value: CreditPackConfig(
        id=CreditPackId.CREDITS_100.value,
        name="100 Credits",
        credits=100,
        price=Decimal("59.99"),
        bonus_credits=15,  # 15% bonus
        is_featured=False,
    ),
}


# =============================================================================
# PARLAY CREDIT COSTS
# =============================================================================

# Cost in credits for generating a parlay
PARLAY_CREDIT_COSTS: Dict[str, int] = {
    ParlayType.STANDARD.value: 1,  # Standard single-sport parlay
    ParlayType.ELITE.value: 3,     # Elite/multi-sport parlay with deep analysis
}


# =============================================================================
# FREE TIER CONFIGURATION
# =============================================================================

# Number of free parlays for new users (lifetime, not daily)
FREE_PARLAYS_TOTAL = 2


# =============================================================================
# AFFILIATE TIERS CONFIGURATION
# =============================================================================

AFFILIATE_TIERS: Dict[str, AffiliateTierConfig] = {
    AffiliateTier.ROOKIE.value: AffiliateTierConfig(
        tier=AffiliateTier.ROOKIE,
        name="Rookie",
        revenue_threshold=Decimal("0"),
        commission_rate_sub_first=Decimal("0.20"),      # 20% first sub payment
        commission_rate_sub_recurring=Decimal("0.00"),  # 0% recurring
        commission_rate_credits=Decimal("0.20"),        # 20% credits
        badge_color="#9ca3af",  # Gray
    ),
    AffiliateTier.PRO.value: AffiliateTierConfig(
        tier=AffiliateTier.PRO,
        name="Pro",
        revenue_threshold=Decimal("200"),
        commission_rate_sub_first=Decimal("0.20"),      # 20% first sub payment
        commission_rate_sub_recurring=Decimal("0.10"),  # 10% recurring
        commission_rate_credits=Decimal("0.25"),        # 25% credits
        badge_color="#3b82f6",  # Blue
    ),
    AffiliateTier.ALL_STAR.value: AffiliateTierConfig(
        tier=AffiliateTier.ALL_STAR,
        name="All-Star",
        revenue_threshold=Decimal("1000"),
        commission_rate_sub_first=Decimal("0.20"),      # 20% first sub payment
        commission_rate_sub_recurring=Decimal("0.10"),  # 10% recurring
        commission_rate_credits=Decimal("0.30"),        # 30% credits
        badge_color="#8b5cf6",  # Purple
    ),
    AffiliateTier.HALL_OF_FAME.value: AffiliateTierConfig(
        tier=AffiliateTier.HALL_OF_FAME,
        name="Hall of Fame",
        revenue_threshold=Decimal("5000"),
        commission_rate_sub_first=Decimal("0.40"),      # 40% first sub payment
        commission_rate_sub_recurring=Decimal("0.10"),  # 10% recurring
        commission_rate_credits=Decimal("0.35"),        # 35% credits
        badge_color="#f59e0b",  # Gold
    ),
}


# Commission hold period in days (before commission becomes ready for payout)
COMMISSION_HOLD_DAYS = 30


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_subscription_plan(plan_id: str) -> Optional[SubscriptionPlanConfig]:
    """Get subscription plan by ID"""
    return SUBSCRIPTION_PLANS.get(plan_id)


def get_credit_pack(pack_id: str) -> Optional[CreditPackConfig]:
    """Get credit pack by ID"""
    return CREDIT_PACKS.get(pack_id)


def get_affiliate_tier(tier: str) -> Optional[AffiliateTierConfig]:
    """Get affiliate tier configuration"""
    return AFFILIATE_TIERS.get(tier)


def get_parlay_credit_cost(parlay_type: str) -> int:
    """Get the credit cost for a parlay type"""
    return PARLAY_CREDIT_COSTS.get(parlay_type, PARLAY_CREDIT_COSTS[ParlayType.STANDARD.value])


def calculate_tier_for_revenue(total_revenue: Decimal) -> AffiliateTierConfig:
    """Calculate the appropriate tier based on total referred revenue"""
    # Sort tiers by revenue threshold descending
    sorted_tiers = sorted(
        AFFILIATE_TIERS.values(),
        key=lambda t: t.revenue_threshold,
        reverse=True
    )
    
    for tier_config in sorted_tiers:
        if total_revenue >= tier_config.revenue_threshold:
            return tier_config
    
    # Default to Rookie
    return AFFILIATE_TIERS[AffiliateTier.ROOKIE.value]


def get_all_subscription_plans() -> List[dict]:
    """Get all subscription plans as dictionaries"""
    return [plan.to_dict() for plan in SUBSCRIPTION_PLANS.values()]


def get_all_credit_packs() -> List[dict]:
    """Get all credit packs as dictionaries"""
    return [pack.to_dict() for pack in CREDIT_PACKS.values()]


def get_all_affiliate_tiers() -> List[dict]:
    """Get all affiliate tiers as dictionaries"""
    return [tier.to_dict() for tier in AFFILIATE_TIERS.values()]



