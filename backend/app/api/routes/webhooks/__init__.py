"""
Webhook routes for payment providers.

This package keeps provider handlers in focused modules (<500 LOC each) and
exposes a single `router` for `app.main` to mount.
"""

from fastapi import APIRouter

from .coinbase_webhook_routes import router as coinbase_router
from .stripe_webhook_routes import router as stripe_router

router = APIRouter()

router.include_router(stripe_router)
router.include_router(coinbase_router)


