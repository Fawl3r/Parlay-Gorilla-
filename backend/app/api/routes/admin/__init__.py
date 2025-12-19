"""
Admin API routes module.

All routes under /api/admin require admin role authentication.
"""

from fastapi import APIRouter

from .auth import require_admin, router as auth_router
from .metrics import router as metrics_router
from .users import router as users_router
from .feature_flags import router as feature_flags_router
from .events import router as events_router
from .payments import router as payments_router
from .logs import router as logs_router
from .model import router as model_router
from .affiliates import router as affiliates_router
from .payouts import router as payouts_router
from .tax import router as tax_router
from .promo_codes import router as promo_codes_router

# Create main admin router
router = APIRouter(prefix="/admin", tags=["Admin"])

# Include sub-routers
router.include_router(auth_router, prefix="/auth", tags=["Admin Auth"])
router.include_router(metrics_router, prefix="/metrics", tags=["Admin Metrics"])
router.include_router(users_router, prefix="/users", tags=["Admin Users"])
router.include_router(feature_flags_router, prefix="/feature-flags", tags=["Admin Feature Flags"])
router.include_router(events_router, prefix="/events", tags=["Admin Events"])
router.include_router(payments_router, prefix="/payments", tags=["Admin Payments"])
router.include_router(logs_router, prefix="/logs", tags=["Admin Logs"])
router.include_router(model_router, prefix="/model", tags=["Admin Model"])
router.include_router(affiliates_router, prefix="/affiliates", tags=["Admin Affiliates"])
router.include_router(payouts_router, prefix="/payouts", tags=["Admin Payouts"])
router.include_router(tax_router, prefix="/tax", tags=["Admin Tax"])
router.include_router(promo_codes_router, prefix="/promo-codes", tags=["Admin Promo Codes"])

__all__ = ["router", "require_admin"]

