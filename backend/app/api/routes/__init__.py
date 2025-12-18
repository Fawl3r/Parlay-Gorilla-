"""API route modules"""

from . import (
    health, games, sports, bug_reports, parlay, auth, analytics, social, websocket, variants, reports, analysis,
    parlay_extended, team_stats, scraper, user, events, billing, webhooks, profile, subscription, notifications,
    live_games, parlay_tips, metrics, affiliate, custom_parlay, upset_finder, saved_parlays
)
from .admin import router as admin_router

__all__ = [
    "health", "games", "sports", "bug_reports", "parlay", "auth", "analytics", "social", "websocket", 
    "variants", "reports", "analysis", "parlay_extended", "team_stats", "scraper", "user",
    "events", "admin_router", "billing", "webhooks", "profile", "subscription", "notifications",
    "live_games", "parlay_tips", "metrics", "affiliate", "custom_parlay", "upset_finder", "saved_parlays"
]
