"""Application configuration management"""

from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Environment
    environment: str = "development"  # development, staging, production
    debug: bool = False
    
    # Database - supports multiple configurations
    database_url: str  # Primary database URL
    use_sqlite: bool = False  # Fallback to SQLite for quick local testing
    
    # Redis for caching and job queues
    redis_url: str = "redis://localhost:6379"
    
    # External APIs
    the_odds_api_key: str
    openai_api_key: str
    
    # Optional APIs (for enhanced features)
    sportsradar_api_key: Optional[str] = None  # SportsRadar API for schedules, stats, injuries
    openweather_api_key: Optional[str] = None
    getty_images_api_key: Optional[str] = None  # For team action photos via Getty/Imagn (best quality, requires license)
    getty_images_api_secret: Optional[str] = None  # Getty Images API secret (required with API key for OAuth2)
    pexels_api_key: Optional[str] = None  # For team action photos (better quality, 200 req/hour free)
    unsplash_access_key: Optional[str] = None  # For team action photos (50 req/hour free)
    
    # Supabase Auth (optional - for user authentication)
    supabase_url: Optional[str] = None
    supabase_anon_key: Optional[str] = None
    supabase_service_key: Optional[str] = None
    
    # Neon Database (production)
    neon_database_url: Optional[str] = None
    
    # Application URLs
    backend_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:3000"
    
    # JWT Settings
    jwt_secret: str = "your-super-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_period: int = 60  # seconds
    
    # Background Jobs
    enable_background_jobs: bool = True
    scraper_interval_minutes: int = 30
    odds_sync_interval_minutes: int = 5
    
    # LemonSqueezy (recurring subscriptions)
    lemonsqueezy_api_key: Optional[str] = None
    lemonsqueezy_store_id: Optional[str] = None
    lemonsqueezy_webhook_secret: Optional[str] = None
    
    # Coinbase Commerce (crypto payments)
    coinbase_commerce_api_key: Optional[str] = None
    coinbase_commerce_webhook_secret: Optional[str] = None
    
    # Resend (email service)
    resend_api_key: Optional[str] = None  # For sending verification and password reset emails
    
    # Application URLs (for payment redirects)
    app_url: str = "http://localhost:3000"  # Frontend URL for redirects
    
    @property
    def effective_database_url(self) -> str:
        """Get the effective database URL based on environment"""
        if self.environment == "production" and self.neon_database_url:
            return self.neon_database_url
        return self.database_url
    
    @property
    def is_production(self) -> bool:
        return self.environment == "production"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra env vars


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance"""
    return Settings()


settings = get_settings()
