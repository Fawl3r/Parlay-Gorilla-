"""
Ops debug: GET /ops/availability-contract — validate sports list contract.

Ensures every sport has slug, sport_state, is_enabled; detects duplicates and type errors.
Gated by OPS_DEBUG_ENABLED and optional X-Ops-Token. No-store via OpsNoStoreMiddleware.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Header, HTTPException

from app.core.config import get_settings
from app.core.dependencies import get_db
from app.services.sport_state_service import get_sport_state
from app.services.sports_config import is_sport_visible, list_supported_sports
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

VALID_SPORT_STATES = frozenset({"OFFSEASON", "PRESEASON", "IN_SEASON", "IN_BREAK", "POSTSEASON"})


async def _require_ops_debug(
    x_ops_token: str | None = Header(None, alias="X-Ops-Token"),
) -> None:
    """Raise 404 if ops debug disabled; 403 if token required and missing/wrong."""
    settings = get_settings()
    if not settings.ops_debug_enabled:
        raise HTTPException(status_code=404, detail="Not Found")
    if settings.ops_debug_token is not None and (settings.ops_debug_token or "").strip():
        if (x_ops_token or "").strip() != (settings.ops_debug_token or "").strip():
            raise HTTPException(status_code=403, detail="Forbidden")


def _build_and_validate(
    items: List[Dict[str, Any]],
) -> tuple[bool, Dict[str, Any]]:
    """Validate contract for each item. Return (ok, issues dict)."""
    missing_required: List[Dict[str, Any]] = []
    type_errors: List[Dict[str, Any]] = []
    duplicate_slugs: List[str] = []
    unknown_sport_state_values: List[Dict[str, Any]] = []

    seen_slugs: Dict[str, int] = {}
    for i, item in enumerate(items):
        slug = item.get("slug")
        slug_lower = (slug if slug is not None else "").lower().strip()
        if slug_lower:
            seen_slugs[slug_lower] = seen_slugs.get(slug_lower, 0) + 1

    for slug_lower, count in seen_slugs.items():
        if count > 1:
            duplicate_slugs.append(slug_lower)

    for i, item in enumerate(items):
        if not isinstance(item, dict):
            type_errors.append({"index": i, "error": "not a dict"})
            continue
        slug = item.get("slug")
        sport_state = item.get("sport_state")
        is_enabled = item.get("is_enabled")

        missing = []
        if slug is None or (isinstance(slug, str) and not slug.strip()):
            missing.append("slug")
        if sport_state is None:
            missing.append("sport_state")
        if is_enabled is None and "is_enabled" not in item:
            missing.append("is_enabled")
        if missing:
            missing_required.append({"index": i, "slug": slug, "missing": missing})
            continue

        if not isinstance(slug, str):
            type_errors.append({"index": i, "slug": slug, "field": "slug", "error": "must be string"})
        if sport_state is not None and not isinstance(sport_state, str):
            type_errors.append(
                {"index": i, "slug": slug, "field": "sport_state", "error": "must be string"}
            )
        elif isinstance(sport_state, str):
            state_norm = str(sport_state).strip().upper()
            if state_norm not in VALID_SPORT_STATES:
                unknown_sport_state_values.append({"index": i, "slug": slug, "sport_state": sport_state})
        if is_enabled is not None and not isinstance(is_enabled, bool):
            type_errors.append(
                {"index": i, "slug": slug, "field": "is_enabled", "error": "must be boolean"}
            )

    issues = {
        "missing_required": missing_required,
        "type_errors": type_errors,
        "duplicate_slugs": duplicate_slugs,
        "unknown_sport_state_values": unknown_sport_state_values,
    }
    ok = (
        not missing_required
        and not type_errors
        and not duplicate_slugs
        and not unknown_sport_state_values
    )
    return ok, issues


@router.get("/availability-contract")
async def get_availability_contract(
    db: AsyncSession = Depends(get_db),
    _: None = Depends(_require_ops_debug),
) -> Dict[str, Any]:
    """
    Validate sports list contract: required fields (slug, sport_state, is_enabled) and types.

    Uses same registry and get_sport_state as /api/sports. Returns ok=true when valid.
    """
    now = datetime.now(timezone.utc)
    configs = list_supported_sports()
    items: List[Dict[str, Any]] = []

    for cfg in configs:
        if not is_sport_visible(cfg):
            continue
        state_result = await get_sport_state(db=db, sport_code=cfg.code, now=now)
        sport_state = state_result.get("sport_state", "OFFSEASON")
        next_game_at = state_result.get("next_game_at")
        items.append(
            {
                "slug": cfg.slug,
                "sport_state": sport_state,
                "is_enabled": state_result.get("is_enabled", False),
                "next_game_at": next_game_at,
                "days_to_next": state_result.get("days_to_next"),
                "preseason_enable_days": state_result.get("preseason_enable_days"),
            }
        )

    ok, issues = _build_and_validate(items)
    enabled_count = sum(1 for it in items if it.get("is_enabled") is True)
    response: Dict[str, Any] = {
        "ok": ok,
        "checked_at_utc": now.isoformat(),
        "counts": {"sports": len(items), "enabled": enabled_count, "disabled": len(items) - enabled_count},
        "issues": issues,
    }
    if ok:
        response["sports_sample"] = items[:3]
    else:
        response["sports_sample"] = items
    return response
