"""Games API endpoints (aggregator).

The original module grew large; routes are split into focused modules and
included here to keep files <500 lines and responsibilities clear.
"""

from fastapi import APIRouter

from app.api.routes.games_admin_routes import router as admin_router
from app.api.routes.games_public_routes import router as public_router
from app.api.routes.games_tools_routes import router as tools_router

router = APIRouter()
router.include_router(public_router)
router.include_router(admin_router)
router.include_router(tools_router)

