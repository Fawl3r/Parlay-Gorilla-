"""Analysis feed endpoint for the social bot.

This is intentionally lightweight and stable:
- No scraping
- Small payload (short angles + key points)
- Cacheable
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_db
from app.models.game_analysis import GameAnalysis
from app.services.analysis_content_normalizer import AnalysisContentNormalizer
from app.utils.timezone_utils import TimezoneNormalizer

router = APIRouter()


def _sanitize_line(value: str, *, max_len: int) -> str:
    text = " ".join((value or "").replace("\r", " ").replace("\n", " ").split())
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


def _extract_key_points(content: Dict[str, Any]) -> List[str]:
    points: List[str] = []
    drivers = content.get("ui_key_drivers") or {}
    positives = drivers.get("positives") or []
    key_stats = content.get("key_stats") or []

    for x in positives:
        if len(points) >= 3:
            break
        s = _sanitize_line(str(x), max_len=140)
        if s:
            points.append(s)

    for x in key_stats:
        if len(points) >= 3:
            break
        s = _sanitize_line(str(x), max_len=140)
        if s and s not in points:
            points.append(s)

    return points[:3]


def _extract_risk_note(content: Dict[str, Any]) -> Optional[str]:
    drivers = content.get("ui_key_drivers") or {}
    risks = drivers.get("risks") or []
    if not risks:
        return None
    note = _sanitize_line(str(risks[0]), max_len=170)
    return note or None


def _extract_angle(content: Dict[str, Any]) -> str:
    # Prefer the UI-first opening, but fall back safely.
    for key in ["opening_summary", "subheadline", "headline"]:
        raw = content.get(key)
        if isinstance(raw, str) and raw.strip():
            return _sanitize_line(raw, max_len=220)
    return ""


def _build_cta_url(slug: str) -> str:
    base = (settings.frontend_url or "").rstrip("/")
    slug_norm = str(slug or "").lstrip("/")
    return f"{base}/analysis/{slug_norm}"


@router.get("/analysis-feed")
async def analysis_feed(
    response: Response,
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Return a small, cacheable feed of recent analysis excerpts for social posting."""
    response.headers["Cache-Control"] = "public, max-age=600"

    result = await db.execute(
        select(GameAnalysis).order_by(desc(GameAnalysis.generated_at)).limit(limit)
    )
    analyses = result.scalars().all()

    normalizer = AnalysisContentNormalizer()
    items: List[Dict[str, Any]] = []
    for analysis in analyses:
        content_raw = analysis.analysis_content or {}
        if not isinstance(content_raw, dict):
            content_raw = {}
        content = normalizer.normalize(content_raw)

        slug = str(analysis.slug or "").strip()
        if not slug:
            continue

        items.append(
            {
                "slug": slug,
                "angle": _extract_angle(content),
                "key_points": _extract_key_points(content),
                "risk_note": _extract_risk_note(content),
                "cta_url": _build_cta_url(slug),
                "generated_at": TimezoneNormalizer.ensure_utc(analysis.generated_at).isoformat(),
            }
        )

    return {"items": items, "count": len(items), "limit": limit}


