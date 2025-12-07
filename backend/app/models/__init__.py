"""Database models"""

from app.models.game import Game
from app.models.market import Market
from app.models.odds import Odds
from app.models.parlay import Parlay
from app.models.user import User, UserRole, UserPlan
from app.models.parlay_cache import ParlayCache
from app.models.shared_parlay import SharedParlay, ParlayLike
from app.models.team_stats import TeamStats
from app.models.game_results import GameResult
from app.models.parlay_results import ParlayResult
from app.models.market_efficiency import MarketEfficiency
from app.models.game_analysis import GameAnalysis
from app.models.model_prediction import ModelPrediction
from app.models.prediction_outcome import PredictionOutcome, TeamCalibration

# Admin & Analytics models
from app.models.app_event import AppEvent
from app.models.parlay_event import ParlayEvent
from app.models.payment import Payment, PaymentStatus, PaymentProvider
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.feature_flag import FeatureFlag
from app.models.system_log import SystemLog, LogLevel, LogSource
from app.models.admin_session import AdminSession

# Subscription & Billing models
from app.models.subscription_plan import SubscriptionPlan, BillingCycle
from app.models.usage_limit import UsageLimit
from app.models.payment_event import PaymentEvent

# Profile, Badges & Verification models
from app.models.verification_token import VerificationToken, TokenType
from app.models.badge import Badge, BadgeRequirementType, STARTER_BADGES
from app.models.user_badge import UserBadge

__all__ = [
    # Core models
    "Game", "Market", "Odds", "Parlay",
    "TeamStats", "GameResult", "ParlayResult", "MarketEfficiency",
    "User", "UserRole", "UserPlan",
    "ParlayCache", "SharedParlay", "ParlayLike",
    "GameAnalysis",
    # Prediction tracking
    "ModelPrediction", "PredictionOutcome", "TeamCalibration",
    # Admin & Analytics
    "AppEvent", "ParlayEvent",
    "Payment", "PaymentStatus", "PaymentProvider",
    "Subscription", "SubscriptionStatus",
    "FeatureFlag",
    "SystemLog", "LogLevel", "LogSource",
    "AdminSession",
    # Subscription & Billing
    "SubscriptionPlan", "BillingCycle",
    "UsageLimit",
    "PaymentEvent",
    # Profile, Badges & Verification
    "VerificationToken", "TokenType",
    "Badge", "BadgeRequirementType", "STARTER_BADGES",
    "UserBadge",
]

