"""Application configuration management"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database
    database_url: str
    
    # External APIs
    the_odds_api_key: str
    openai_api_key: str
    
    # Optional APIs (for enhanced features)
    openweather_api_key: Optional[str] = None  # OpenWeatherMap API key (free tier available)
    
    # Supabase Auth (for user authentication)
    supabase_url: Optional[str] = None  # Supabase project URL
    supabase_anon_key: Optional[str] = None  # Supabase anon/public key
    supabase_service_key: Optional[str] = None  # Supabase service role key (for admin operations)
    
    # Email service (optional)
    resend_api_key: Optional[str] = None  # Resend API key (free tier: 3000 emails/month)
    
    # Application
    backend_url: str = "http://localhost:8000"
    debug: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

