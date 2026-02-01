"""Database models"""

from app.models.game import Game
from app.models.market import Market
from app.models.odds import Odds
from app.models.parlay import Parlay
from app.models.parlay_leg import ParlayLeg
from app.models.parlay_feed_event import ParlayFeedEvent
from app.models.system_heartbeat import SystemHeartbeat
from app.models.saved_parlay import SavedParlay, SavedParlayType, InscriptionStatus
from app.models.saved_parlay_results import SavedParlayResult
from app.models.arcade_points_event import ArcadePointsEvent
from app.models.arcade_points_totals import ArcadePointsTotals
from app.models.user import User, UserRole, UserPlan, SubscriptionStatusEnum
from app.models.parlay_cache import ParlayCache
from app.models.shared_parlay import SharedParlay, ParlayLike
from app.models.team_stats import TeamStats
from app.models.game_results import GameResult
from app.models.parlay_results import ParlayResult
from app.models.market_efficiency import MarketEfficiency
from app.models.game_analysis import GameAnalysis
from app.models.push_subscription import PushSubscription
from app.models.analysis_page_views import AnalysisPageViews
from app.models.watched_game import WatchedGame
from app.models.model_prediction import ModelPrediction
from app.models.prediction_outcome import PredictionOutcome, TeamCalibration
from app.models.odds_history_snapshot import OddsHistorySnapshot
from app.models.bug_report import BugReport, BugSeverity
from app.models.gorilla_bot_conversation import GorillaBotConversation
from app.models.gorilla_bot_message import GorillaBotMessage
from app.models.gorilla_bot_kb_document import GorillaBotKnowledgeDocument
from app.models.gorilla_bot_kb_chunk import GorillaBotKnowledgeChunk

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
from app.models.parlay_purchase import ParlayPurchase, ParlayType, PurchaseStatus
from app.models.credit_pack_purchase import CreditPackPurchase, CreditPackPurchaseStatus

# Profile, Badges & Verification models
from app.models.verification_token import VerificationToken, TokenType
from app.models.verification_record import VerificationRecord, VerificationStatus
from app.models.badge import Badge, BadgeRequirementType, STARTER_BADGES
from app.models.user_badge import UserBadge

# Live Game & Drive models
from app.models.live_game import LiveGame, LiveGameStatus
from app.models.drive import Drive, DriveResult

# Affiliate models
from app.models.affiliate import Affiliate
from app.models.affiliate_click import AffiliateClick
from app.models.affiliate_referral import AffiliateReferral
from app.models.affiliate_commission import AffiliateCommission, CommissionStatus, CommissionSaleType
from app.models.affiliate_payout import AffiliatePayout, PayoutStatus, PayoutMethod
from app.models.promo_code import PromoCode, PromoRewardType
from app.models.promo_redemption import PromoRedemption
# API-Sports cache and quota
from app.models.apisports_fixture import ApisportsFixture
from app.models.apisports_result import ApisportsResult
from app.models.apisports_team_stat import ApisportsTeamStat
from app.models.apisports_team import ApisportsTeam
from app.models.apisports_team_roster import ApisportsTeamRoster
from app.models.apisports_standing import ApisportsStanding
from app.models.apisports_injury import ApisportsInjury
from app.models.apisports_feature import ApisportsFeature
from app.models.api_quota_usage import ApiQuotaUsage
from app.models.enums import SeasonState
from app.models.sport_season_state import SportSeasonState

__all__ = [
    # Core models
    "Game", "Market", "Odds", "Parlay",
    "ParlayLeg", "ParlayFeedEvent", "SystemHeartbeat",
    "SavedParlay", "SavedParlayType", "InscriptionStatus",
    "SavedParlayResult",
    "ArcadePointsEvent", "ArcadePointsTotals",
    "TeamStats", "GameResult", "ParlayResult", "MarketEfficiency",
    "User", "UserRole", "UserPlan", "SubscriptionStatusEnum",
    "ParlayCache", "SharedParlay", "ParlayLike",
    "GameAnalysis",
    "PushSubscription",
    "AnalysisPageViews",
    "WatchedGame",
    # Prediction tracking
    "ModelPrediction", "PredictionOutcome", "TeamCalibration",
    "OddsHistorySnapshot",
    "BugReport", "BugSeverity",
    "GorillaBotConversation", "GorillaBotMessage",
    "GorillaBotKnowledgeDocument", "GorillaBotKnowledgeChunk",
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
    "ParlayPurchase", "ParlayType", "PurchaseStatus",
    "CreditPackPurchase", "CreditPackPurchaseStatus",
    # Profile, Badges & Verification
    "VerificationToken", "TokenType",
    "VerificationRecord", "VerificationStatus",
    "Badge", "BadgeRequirementType", "STARTER_BADGES",
    "UserBadge",
    # Live Game & Drive
    "LiveGame", "LiveGameStatus",
    "Drive", "DriveResult",
    # Affiliate models
    "Affiliate", "AffiliateClick", "AffiliateReferral", 
    "AffiliateCommission", "CommissionStatus", "CommissionSaleType",
    "AffiliatePayout", "PayoutStatus", "PayoutMethod",
    # Promo codes
    "PromoCode", "PromoRewardType", "PromoRedemption",
    # API-Sports
    "ApisportsFixture", "ApisportsResult", "ApisportsTeamStat",
    "ApisportsStanding", "ApisportsInjury", "ApisportsFeature",
    "ApisportsTeam", "ApisportsTeamRoster",
    "ApiQuotaUsage",
    "SeasonState",
    "SportSeasonState",
]

