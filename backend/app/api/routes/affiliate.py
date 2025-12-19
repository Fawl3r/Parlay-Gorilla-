"""
Affiliate API routes for the affiliate program.

Split into smaller modules under `affiliate_routes/` to keep files focused and
below the project’s file-size limits.
"""

from fastapi import APIRouter

from .affiliate_routes.attribute_routes import router as attribute_router
from .affiliate_routes.me_routes import router as me_router
from .affiliate_routes.public_routes import router as public_router
from .affiliate_routes.tax_routes import router as tax_router

router = APIRouter()
router.include_router(public_router)
router.include_router(me_router)
router.include_router(attribute_router)
router.include_router(tax_router)

