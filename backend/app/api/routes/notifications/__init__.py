"""Notifications route aggregation."""

from fastapi import APIRouter

from app.api.routes.notifications.push_routes import router as push_router

router = APIRouter()
router.include_router(push_router)

__all__ = ["router"]


