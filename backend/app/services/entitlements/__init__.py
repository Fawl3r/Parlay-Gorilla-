"""Entitlements service for parlay suggest access and GET /api/me/entitlements."""

from app.services.entitlements.entitlement_service import EntitlementService, get_entitlement_service

__all__ = ["EntitlementService", "get_entitlement_service"]
