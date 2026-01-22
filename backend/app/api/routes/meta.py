"""Meta information endpoints"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class VersionResponse(BaseModel):
    """Version information response model"""
    app_version: str
    build: str
    engine: str


@router.get("/version", response_model=VersionResponse)
async def get_version():
    """Get application version information"""
    return {
        "app_version": "1.0a",
        "build": "FREE",
        "engine": "deterministic-core"
    }
