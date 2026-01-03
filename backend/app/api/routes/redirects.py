"""Short redirect routes (no /api prefix).

Used for clean social links that fan out to the frontend with UTMs.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from fastapi.responses import RedirectResponse

from app.core.config import settings

router = APIRouter()


@router.get("/r/{slug:path}")
async def redirect_analysis_slug(
    slug: str,
    v: str = Query("a", description="A/B variant: a|b"),
):
    variant = (v or "a").strip().lower()
    if variant not in {"a", "b"}:
        variant = "a"

    base = (settings.frontend_url or "").rstrip("/")
    slug_norm = (slug or "").lstrip("/")

    utm_content = f"variant_{variant}"
    target = (
        f"{base}/analysis/{slug_norm}"
        f"?utm_source=x&utm_medium=social&utm_campaign=analysis&utm_content={utm_content}"
    )
    return RedirectResponse(url=target, status_code=302)


