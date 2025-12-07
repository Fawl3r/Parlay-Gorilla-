"""API route modules"""

from . import (
    health, games, parlay, auth, analytics, social, websocket, variants, reports, analysis,
    parlay_extended, team_stats, scraper, user, events, billing, webhooks, profile, subscription
)
from .admin import router as admin_router

__all__ = [
    "health", "games", "parlay", "auth", "analytics", "social", "websocket", 
    "variants", "reports", "analysis", "parlay_extended", "team_stats", "scraper", "user",
    "events", "admin_router", "billing", "webhooks", "profile", "subscription"
]
