"""Entitlements schema for GET /api/me/entitlements."""

from pydantic import BaseModel, Field
from typing import Optional


class EntitlementsCredits(BaseModel):
    """Credits remaining per feature."""
    ai_picks_remaining: int = Field(description="Credits available for AI parlay generation")
    gorilla_builder_remaining: int = Field(description="Credits available for custom builder actions")


class EntitlementsFeatures(BaseModel):
    """Feature flags and limits from plan."""
    mix_sports: bool = Field(description="Whether user can use mixed-sports parlays")
    max_legs: int = Field(ge=1, le=20, description="Max legs allowed for AI parlay")
    player_props: bool = Field(description="Whether user can include player props")


class EntitlementsResponse(BaseModel):
    """Response for GET /api/me/entitlements (single source of truth for UI)."""
    is_authenticated: bool = Field(description="Whether the user is logged in")
    plan: str = Field(description="anon | free | premium")
    credits: EntitlementsCredits = Field(default_factory=lambda: EntitlementsCredits(ai_picks_remaining=0, gorilla_builder_remaining=0))
    features: EntitlementsFeatures = Field(default_factory=lambda: EntitlementsFeatures(mix_sports=False, max_legs=5, player_props=False))
