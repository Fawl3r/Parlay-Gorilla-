"""
Billing API routes.

This module stays intentionally thin (<500 LOC) and mounts focused sub-routers:
- Subscription routes (status/plans + checkout creation)
- Pay-per-use parlay purchase routes
- Credit pack routes (access status + credit pack checkout)
"""

from fastapi import APIRouter

from .subscription_routes import router as subscription_router
from .parlay_purchase_routes import router as parlay_purchase_router
from .credit_pack_routes import router as credit_pack_router
from .webhook_diagnostics import router as webhook_diagnostics_router

router = APIRouter()

router.include_router(subscription_router)
router.include_router(parlay_purchase_router)
router.include_router(credit_pack_router)
router.include_router(webhook_diagnostics_router)


