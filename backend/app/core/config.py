"""Application configuration management"""

from functools import lru_cache
from typing import Optional
from decimal import Decimal

from pydantic import field_validator, model_validator, ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Environment
    environment: str = "development"  # development, staging, production
    debug: bool = False
    
    # Database - supports multiple configurations
    database_url: str  # Primary database URL (PostgreSQL)
    use_sqlite: bool = False  # Fallback to SQLite for quick local testing
    
    # Redis for caching and job queues
    # NOTE: Redis is REQUIRED in production to enable:
    # - Distributed Odds API cache (credits protection across instances)
    # - Scheduler leader election (prevents duplicate jobs in multi-instance deploys)
    redis_url: str = ""
    # Odds API caching policy (credits protection)
    odds_api_cache_ttl_seconds: int = 172800  # 48 hours
    # Stats platform v2 TTLs (hours)
    stats_ttl_hours: int = 24
    injury_ttl_hours: int = 12
    features_ttl_hours: int = 24
    # Feature flag for stats platform v2
    use_stats_platform_v2: bool = False  # Set to True to enable v2 platform
    
    # External APIs
    the_odds_api_key: str
    the_odds_api_fallback_key: Optional[str] = None
    # OpenAI is used for generating natural-language explanations. It can be
    # disabled (e.g. for offline/CI test runs) to avoid external calls.
    openai_enabled: bool = True
    openai_api_key: Optional[str] = None
    # ------------------------------------------------------------------
    # Gorilla Bot (Account-aware Q&A)
    # ------------------------------------------------------------------
    gorilla_bot_enabled: bool = True
    gorilla_bot_model: str = "gpt-4o-mini"
    gorilla_bot_embedding_model: str = "text-embedding-3-small"
    gorilla_bot_embedding_batch_size: int = 48
    gorilla_bot_embedding_timeout_seconds: float = 30.0
    gorilla_bot_chat_timeout_seconds: float = 30.0
    gorilla_bot_kb_path: str = "docs/gorilla-bot/kb"
    gorilla_bot_max_context_chunks: int = 6
    gorilla_bot_max_response_tokens: int = 700
    # Optional APIs (for enhanced features)
    # NOTE: Sportsradar has been removed. API-Sports is now the primary sports data source.
    api_sports_api_key: Optional[str] = None  # API-Sports (api-sports.io) - PRIMARY sports data source (stats, results, form, standings)
    # API-Sports quota and rate limiting (100 requests/day free tier)
    apisports_base_url: str = "https://v3.football.api-sports.io"  # soccer (football) default
    # Per-sport base URLs (optional overrides; used by refresh job)
    apisports_base_url_nfl: Optional[str] = None  # default: v1 american-football
    apisports_base_url_nba: Optional[str] = None   # default: v1 basketball
    apisports_base_url_nhl: Optional[str] = None   # default: v1 hockey
    apisports_base_url_mlb: Optional[str] = None  # default: v1 baseball
    apisports_daily_quota: int = 100
    apisports_soft_rps_interval_seconds: int = 15
    apisports_burst: int = 2
    apisports_circuit_breaker_failures: int = 5
    apisports_circuit_breaker_cooldown_seconds: int = 1800
    # API-Sports cache TTLs (seconds)
    apisports_ttl_fixtures_seconds: int = 900
    apisports_ttl_team_stats_seconds: int = 86400
    apisports_ttl_standings_seconds: int = 86400
    apisports_ttl_injuries_seconds: int = 43200
    # Budget allocation (calls per day): fixtures, team_stats, standings, reserve
    apisports_budget_fixtures: int = 60
    apisports_budget_team_stats: int = 25
    apisports_budget_standings: int = 10
    apisports_budget_reserve: int = 5
    openweather_api_key: Optional[str] = None
    getty_images_api_key: Optional[str] = None  # For team action photos via Getty/Imagn (best quality, requires license)
    getty_images_api_secret: Optional[str] = None  # Getty Images API secret (required with API key for OAuth2)
    pexels_api_key: Optional[str] = None  # For team action photos (better quality, 200 req/hour free)
    unsplash_access_key: Optional[str] = None  # For team action photos (50 req/hour free)
    # Application URLs
    backend_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:3000"
    # App metadata (used in deterministic hashing payloads for verification records)
    app_version: str = "pg_backend_v1"
    # ------------------------------------------------------------------
    # Verification records (automatic integrity layer)
    # ------------------------------------------------------------------
    verification_enabled: bool = True  # Global kill switch (server-side)
    verification_network: str = "mainnet"  # mainnet | testnet | devnet (worker config)
    # Custom AI parlays are automatically verified (server-side, no user action).
    enable_custom_parlay_verification: bool = True
    # Fingerprint generation window (seconds); 5-10 min bucket recommended.
    custom_parlay_verification_window_seconds: int = 600
    # Optional safeguard (in addition to plan/rate limits). 0 disables.
    custom_parlay_verification_soft_max_per_hour: int = 0
    # Free tier limits (rolling 7-day window)
    free_parlays_per_week: int = 5  # Number of free AI parlays per rolling 7-day period
    free_custom_parlays_per_week: int = 5  # Number of free custom builder parlays per rolling 7-day period
    free_parlays_per_day: int = 3  # Deprecated: kept for backward compatibility, use free_parlays_per_week
    # Premium tier limits
    # NOTE: This is a rolling window (not calendar month). See `premium_ai_parlays_period_days`.
    premium_ai_parlays_per_month: int = 100  # Premium AI parlays per rolling period
    premium_ai_parlays_period_days: int = 30  # Reset period in days
    # Custom parlay builder (AI actions: analyze / counter / coverage)
    # NOTE: This is a rolling window (not calendar month). See `premium_custom_builder_period_days`.
    premium_custom_builder_per_month: int = 25  # Included custom builder actions per rolling period
    premium_custom_builder_period_days: int = 30  # Reset period in days
    # On-chain inscriptions (hash-only proof payload)
    # NOTE: This is a rolling window (not calendar month). See `premium_inscriptions_period_days`.
    premium_inscriptions_per_month: int = 15  # Included inscriptions per rolling period
    premium_inscriptions_period_days: int = 30  # Reset period in days
    # Cost control: each on-chain inscription costs us money. This is disclosed to users
    # (and used for internal cost tracking).
    inscription_cost_usd: float = 0.37

    # Credits (per-usage)
    # Credit users can spend credits for access to:
    # - AI Parlay Generator (per generated parlay)
    # - Custom Parlay Builder AI actions (analyze / counter / coverage)
    credits_cost_ai_parlay: int = 3
    credits_cost_custom_builder_action: int = 3
    # - On-chain inscriptions (premium overage)
    credits_cost_inscription: int = 1
    # Pay-per-use parlay pricing (after free limit)
    single_parlay_price_dollars: float = 3.00  # $3 for single-sport parlay
    multi_parlay_price_dollars: float = 5.00  # $5 for multi-sport parlay
    parlay_purchase_expiry_hours: int = 24  # Purchases expire after 24h if unused
    
    # JWT Settings
    jwt_secret: str = "your-super-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_period: int = 60  # seconds
    disable_rate_limits: bool = False  # Set to True to disable all rate limiting (for testing only)

    # ------------------------------------------------------------------
    # Probability Engine Performance Tuning
    # ------------------------------------------------------------------
    # These settings bound network work done during parlay generation and
    # analysis probability calculations (team stats, injuries, weather, etc.).
    probability_external_fetch_enabled: bool = True
    probability_external_fetch_timeout_seconds: float = 2.5
    probability_prefetch_enabled: bool = True
    probability_prefetch_concurrency: int = 8
    probability_prefetch_max_games: int = 50
    probability_prefetch_total_timeout_seconds: float = 12.0

    # Analysis detail endpoint should never hang while attempting probability refresh.
    analysis_probability_refresh_timeout_seconds: float = 8.0

    # ------------------------------------------------------------------
    # Analysis Generation Pipeline (Core + Full Article)
    # ------------------------------------------------------------------
    # Core analysis is generated quickly and returned immediately.
    analysis_core_timeout_seconds: float = 8.0
    # Optional: short OpenAI polishing pass for core copy (kept very small).
    analysis_core_ai_polish_timeout_seconds: float = 4.0
    # Long-form article generation runs in background (best-effort).
    analysis_full_article_enabled: bool = True
    analysis_full_article_timeout_seconds: float = 90.0
    # How long analysis core should be considered fresh before being regenerated
    # by background jobs. User traffic should not force regeneration.
    analysis_cache_ttl_hours: float = 48.0
    # Non-NFL leagues (NBA/NHL/MLB/etc.) have more frequent slates; keep analyses fresher.
    analysis_cache_ttl_hours_non_nfl: float = 24.0
    
    # Background Jobs
    enable_background_jobs: bool = True
    scraper_interval_minutes: int = 30
    # Keep odds in sync; cadence should align with Odds API cache TTL.
    # For Gorilla Bot, odds sync every 24 hours or when analytics update.
    odds_sync_interval_minutes: int = 1440  # 24 hours
    # Data source feature flags
    # API-Sports is the primary sports data source (stats, results, form, standings)
    # ESPN is used as fallback for stats/results when API-Sports data unavailable
    use_apisports_for_stats: bool = True  # Use API-Sports for team stats (default: True)
    use_apisports_for_results: bool = True  # Use API-Sports for completed game results (default: True)
    
    # ------------------------------------------------------------------
    # Feature Flags (Production Safety)
    # ------------------------------------------------------------------
    # Feature flags allow instant kill switches for risky features.
    # Set to False to disable a feature immediately without code changes.
    # All flags default to True except FEATURE_SETTLEMENT (risky, defaults OFF).
    feature_analytics: bool = True  # Enable analytics endpoints and pages
    feature_live_scores: bool = True  # Enable live scores and game updates
    feature_settlement: bool = False  # Enable parlay settlement system (RISKY - defaults OFF)
    feature_live_wall: bool = True  # Enable live marquee/wall features
    
    # Stripe (recurring subscriptions and one-time payments)
    stripe_secret_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None
    
    # Stripe Price IDs (subscription plans)
    # These map to SubscriptionPlan.code values for provider="stripe".
    # Used as a fallback when subscription_plans.provider_product_id is not set.
    stripe_price_id_pro_monthly: Optional[str] = None
    stripe_price_id_pro_annual: Optional[str] = None
    stripe_price_id_pro_lifetime: Optional[str] = None
    
    # Stripe Price IDs (credit packs)
    # These map to credit pack IDs: CREDITS_10, CREDITS_25, CREDITS_50, CREDITS_100
    # Used as a fallback when subscription_plans.provider_product_id is not set.
    stripe_price_id_credits_10: Optional[str] = None
    stripe_price_id_credits_25: Optional[str] = None
    stripe_price_id_credits_50: Optional[str] = None
    stripe_price_id_credits_100: Optional[str] = None
    
    # Stripe success/cancel URLs for checkout redirects
    stripe_success_url: str = "{app_url}/billing/success?provider=stripe"
    stripe_cancel_url: str = "{app_url}/billing?canceled=true"

    # LemonSqueezy (legacy / provider fallback)
    # NOTE: LemonSqueezy support is kept for existing integrations and webhooks.
    # If unset, LemonSqueezy routes should fail gracefully with "not configured"
    # rather than crashing due to missing config fields.
    lemonsqueezy_api_key: Optional[str] = None
    lemonsqueezy_store_id: Optional[str] = None
    lemonsqueezy_webhook_secret: Optional[str] = None

    # LemonSqueezy variant IDs (optional env-based wiring for checkouts)
    lemonsqueezy_premium_monthly_variant_id: Optional[str] = None
    lemonsqueezy_premium_annual_variant_id: Optional[str] = None
    lemonsqueezy_lifetime_variant_id: Optional[str] = None
    lemonsqueezy_credits_10_variant_id: Optional[str] = None
    lemonsqueezy_credits_25_variant_id: Optional[str] = None
    lemonsqueezy_credits_50_variant_id: Optional[str] = None
    lemonsqueezy_credits_100_variant_id: Optional[str] = None
    
    # Coinbase Commerce (crypto payments) - DEPRECATED
    # Disabled for LemonSqueezy compliance. Kept for reference only.
    # Do not re-enable without compliance review.
    coinbase_commerce_api_key: Optional[str] = None
    coinbase_commerce_webhook_secret: Optional[str] = None
    
    # PayPal Payouts (affiliate payouts)
    paypal_client_id: Optional[str] = None
    paypal_client_secret: Optional[str] = None
    paypal_payout_minimum: Decimal = Decimal("25.00")  # Minimum affiliate payout amount (USD)
    
    # Circle API (crypto payouts - USDC)
    circle_api_key: Optional[str] = None
    circle_environment: str = "sandbox"  # sandbox or production

    # Tax reporting (affiliate payouts)
    # If enabled, we will attempt to fetch a live USD valuation quote (e.g. Coinbase spot)
    # to snapshot FMV at the time of a crypto payout. If disabled, stablecoins fall back
    # to a 1.0 peg valuation.
    tax_valuation_external_enabled: bool = True
    tax_valuation_timeout_seconds: float = 3.0
    
    # Resend (email service)
    resend_api_key: Optional[str] = None  # For sending verification and password reset emails
    # Resend requires the "from" address to be either:
    # - a verified domain you own (e.g., noreply@parlaygorilla.com), or
    # - a Resend-provided address like onboarding@resend.dev (works without domain verification).
    #
    # Use RESEND_FROM to override in production once your domain is verified.
    resend_from: str = "Parlay Gorilla <onboarding@resend.dev>"

    # Optional: public logo URL for transactional emails (verification/reset).
    # If unset, emails default to {APP_URL}/images/newlogo.png.
    # NOTE: This must be publicly reachable by recipients (avoid localhost), and HTTPS is strongly recommended.
    email_logo_url: Optional[str] = None
    # Inline logo embedding (base64) can cause Gmail clipping for large images.
    # Disable by default; enable only for small logos and when needed.
    email_inline_logo_enabled: bool = False
    email_inline_logo_max_bytes: int = 12_000
    
    # Application URLs (for payment redirects)
    app_url: str = "http://localhost:3000"  # Frontend URL for redirects

    # ------------------------------------------------------------------
    # Web Push Notifications (opt-in)
    # ------------------------------------------------------------------
    # When enabled, the backend can send Web Push notifications to subscribed browsers.
    # VAPID keys are required to be configured when enabled.
    web_push_enabled: bool = False
    web_push_vapid_public_key: str = ""
    web_push_vapid_private_key: str = ""
    # RFC 8292 "subject" (mailto: or https://). Example: mailto:support@parlaygorilla.com
    web_push_subject: str = ""

    # Telegram alerts (operator alerts for parlay/schedule/quota failures)
    telegram_alerts_enabled: bool = False
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    
    @property
    def is_production(self) -> bool:
        return self.environment == "production"
    
    @field_validator("database_url", mode="before")
    @classmethod
    def validate_database_url(cls, v: Optional[str]) -> str:
        if not v:
            raise ValueError("DATABASE_URL is required")
        return v

    @model_validator(mode="after")
    def validate_external_services(self):
        if self.openai_enabled and not self.openai_api_key:
            raise ValueError("OPENAI_ENABLED=true requires OPENAI_API_KEY to be set")
        if self.environment == "production" and not (self.redis_url or "").strip():
            raise ValueError("ENVIRONMENT=production requires REDIS_URL to be set")
        if self.web_push_enabled:
            if not (self.web_push_vapid_public_key or "").strip():
                raise ValueError("WEB_PUSH_ENABLED=true requires WEB_PUSH_VAPID_PUBLIC_KEY to be set")
            if not (self.web_push_vapid_private_key or "").strip():
                raise ValueError("WEB_PUSH_ENABLED=true requires WEB_PUSH_VAPID_PRIVATE_KEY to be set")
            if not (self.web_push_subject or "").strip():
                raise ValueError("WEB_PUSH_ENABLED=true requires WEB_PUSH_SUBJECT to be set")
        return self

    @field_validator("probability_external_fetch_timeout_seconds", mode="before")
    @classmethod
    def validate_probability_external_fetch_timeout_seconds(cls, v: Optional[float]) -> float:
        if v is None:
            return 2.5
        try:
            value = float(v)
        except Exception as exc:
            raise ValueError("PROBABILITY_EXTERNAL_FETCH_TIMEOUT_SECONDS must be a number") from exc
        if value <= 0:
            raise ValueError("PROBABILITY_EXTERNAL_FETCH_TIMEOUT_SECONDS must be > 0")
        return value
    @field_validator("probability_prefetch_concurrency", mode="before")
    @classmethod
    def validate_probability_prefetch_concurrency(cls, v: Optional[int]) -> int:
        if v is None:
            return 8
        try:
            value = int(v)
        except Exception as exc:
            raise ValueError("PROBABILITY_PREFETCH_CONCURRENCY must be an integer") from exc
        if value < 1:
            raise ValueError("PROBABILITY_PREFETCH_CONCURRENCY must be >= 1")
        return value

    @field_validator("probability_prefetch_max_games", mode="before")
    @classmethod
    def validate_probability_prefetch_max_games(cls, v: Optional[int]) -> int:
        if v is None:
            return 50
        try:
            value = int(v)
        except Exception as exc:
            raise ValueError("PROBABILITY_PREFETCH_MAX_GAMES must be an integer") from exc
        if value < 1:
            raise ValueError("PROBABILITY_PREFETCH_MAX_GAMES must be >= 1")
        return value

    @field_validator("probability_prefetch_total_timeout_seconds", mode="before")
    @classmethod
    def validate_probability_prefetch_total_timeout_seconds(cls, v: Optional[float]) -> float:
        """
        Hard cap for the prefetch phase within candidate generation.

        Prefetch is an optimization and must never cause a request to hang. If
        the timeout is reached, remaining prefetch tasks are cancelled and
        candidate generation continues using whatever data is already cached.
        """
        if v is None:
            return 12.0
        try:
            value = float(v)
        except Exception as exc:
            raise ValueError("PROBABILITY_PREFETCH_TOTAL_TIMEOUT_SECONDS must be a number") from exc
        if value <= 0:
            # Treat non-positive values as "disable the hard cap".
            return 0.0
        return value

    @field_validator("analysis_probability_refresh_timeout_seconds", mode="before")
    @classmethod
    def validate_analysis_probability_refresh_timeout_seconds(cls, v: Optional[float]) -> float:
        if v is None:
            return 8.0
        try:
            value = float(v)
        except Exception as exc:
            raise ValueError("ANALYSIS_PROBABILITY_REFRESH_TIMEOUT_SECONDS must be a number") from exc
        if value <= 0:
            raise ValueError("ANALYSIS_PROBABILITY_REFRESH_TIMEOUT_SECONDS must be > 0")
        return value

    @field_validator("analysis_core_timeout_seconds", mode="before")
    @classmethod
    def validate_analysis_core_timeout_seconds(cls, v: Optional[float]) -> float:
        if v is None:
            return 8.0
        try:
            value = float(v)
        except Exception as exc:
            raise ValueError("ANALYSIS_CORE_TIMEOUT_SECONDS must be a number") from exc
        if value <= 0:
            raise ValueError("ANALYSIS_CORE_TIMEOUT_SECONDS must be > 0")
        return value

    @field_validator("analysis_core_ai_polish_timeout_seconds", mode="before")
    @classmethod
    def validate_analysis_core_ai_polish_timeout_seconds(cls, v: Optional[float]) -> float:
        if v is None:
            return 4.0
        try:
            value = float(v)
        except Exception as exc:
            raise ValueError("ANALYSIS_CORE_AI_POLISH_TIMEOUT_SECONDS must be a number") from exc
        if value <= 0:
            raise ValueError("ANALYSIS_CORE_AI_POLISH_TIMEOUT_SECONDS must be > 0")
        return value

    @field_validator("analysis_full_article_timeout_seconds", mode="before")
    @classmethod
    def validate_analysis_full_article_timeout_seconds(cls, v: Optional[float]) -> float:
        if v is None:
            return 90.0
        try:
            value = float(v)
        except Exception as exc:
            raise ValueError("ANALYSIS_FULL_ARTICLE_TIMEOUT_SECONDS must be a number") from exc
        if value <= 0:
            raise ValueError("ANALYSIS_FULL_ARTICLE_TIMEOUT_SECONDS must be > 0")
        return value

    model_config = ConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance"""
    return Settings()
settings = get_settings()
