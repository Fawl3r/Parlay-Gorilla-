"""Analysis repository.

This module is responsible for:
- loading/saving `GameAnalysis` rows
- merging core updates without losing existing full articles
- providing an in-process concurrency guard for per-game generation
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.game import Game
from app.models.game_analysis import GameAnalysis
from app.services.analysis.analysis_contract import (
    is_core_ready,
    is_full_article_ready,
    merge_preserving_full_article,
    with_generation_metadata,
)


_CORE_LOCKS: dict[str, asyncio.Lock] = {}
_ARTICLE_LOCKS: dict[str, asyncio.Lock] = {}


def _get_lock(lock_map: dict[str, asyncio.Lock], key: str) -> asyncio.Lock:
    lock = lock_map.get(key)
    if lock is None:
        lock = asyncio.Lock()
        lock_map[key] = lock
    return lock


class AnalysisRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    @staticmethod
    def _analysis_cache_ttl_hours_for_league(*, league: str) -> float:
        league_upper = str(league or "").upper()
        if league_upper == "NFL":
            return float(getattr(settings, "analysis_cache_ttl_hours", 48.0) or 48.0)
        return float(getattr(settings, "analysis_cache_ttl_hours_non_nfl", 24.0) or 24.0)

    async def get_by_slug(self, *, league: str, slug: str) -> Optional[GameAnalysis]:
        full_slug = slug
        # Allow callers to pass slug without the sport prefix.
        if "/" not in full_slug:
            full_slug = f"{league.lower()}/{slug}"

        result = await self._db.execute(
            select(GameAnalysis).where(
                GameAnalysis.slug == full_slug,
                GameAnalysis.league == league.upper(),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_game_id(self, *, league: str, game_id) -> Optional[GameAnalysis]:
        result = await self._db.execute(
            select(GameAnalysis).where(
                GameAnalysis.game_id == game_id,
                GameAnalysis.league == league.upper(),
            )
        )
        return result.scalar_one_or_none()

    async def get_game_start_time(self, *, game_id) -> Optional[datetime]:
        result = await self._db.execute(select(Game.start_time).where(Game.id == game_id))
        return result.scalar_one_or_none()

    def core_lock(self, *, league: str, game_id: str) -> asyncio.Lock:
        return _get_lock(_CORE_LOCKS, f"{league.upper()}:{game_id}")

    def article_lock(self, *, analysis_id: str) -> asyncio.Lock:
        return _get_lock(_ARTICLE_LOCKS, f"analysis:{analysis_id}")

    @staticmethod
    def analysis_has_core(analysis: GameAnalysis) -> bool:
        content = analysis.analysis_content or {}
        return isinstance(content, dict) and is_core_ready(content)

    @staticmethod
    def analysis_has_full_article(analysis: GameAnalysis) -> bool:
        content = analysis.analysis_content or {}
        return isinstance(content, dict) and is_full_article_ready(content)

    async def upsert_core(
        self,
        *,
        analysis: Optional[GameAnalysis],
        game: Game,
        canonical_slug: str,
        core_content: Dict[str, Any],
        core_status: str,
        full_article_status: str,
        last_error: Optional[str] = None,
        seo_metadata: Optional[Dict[str, Any]] = None,
        force_refresh: bool = False,
    ) -> GameAnalysis:
        now = datetime.now(tz=timezone.utc)
        ttl_hours = self._analysis_cache_ttl_hours_for_league(league=game.sport)
        expires_at = now + timedelta(hours=ttl_hours)

        core_with_meta = with_generation_metadata(
            core_content,
            core_status=core_status,
            full_article_status=full_article_status,
            last_error=last_error,
        )

        if analysis is None:
            analysis = GameAnalysis(
                game_id=game.id,
                slug=canonical_slug,
                league=game.sport,
                matchup=f"{game.away_team} @ {game.home_team}",
                analysis_content=core_with_meta,
                seo_metadata=seo_metadata,
                expires_at=expires_at,
                version=1,
            )
            self._db.add(analysis)
        else:
            # If force_refresh, completely replace core content (preserve full_article only)
            merged = merge_preserving_full_article(
                existing=analysis.analysis_content, 
                incoming=core_with_meta,
                force_refresh_core=force_refresh
            )
            analysis.analysis_content = merged
            analysis.slug = canonical_slug  # normalize legacy slugs
            if seo_metadata is not None:
                analysis.seo_metadata = seo_metadata
            analysis.version = int(getattr(analysis, "version", 1) or 1) + 1
            analysis.generated_at = now
            analysis.expires_at = expires_at

        await self._db.commit()
        await self._db.refresh(analysis)
        return analysis

    async def update_full_article(
        self,
        *,
        analysis: GameAnalysis,
        full_article: str,
        full_article_status: str,
        last_error: Optional[str] = None,
        redaction_count: Optional[int] = None,
        role_language_rewrite_count: Optional[int] = None,
    ) -> GameAnalysis:
        content = analysis.analysis_content or {}
        if not isinstance(content, dict):
            content = {}

        content["full_article"] = full_article
        content = with_generation_metadata(
            content,
            core_status=(content.get("generation") or {}).get("core_status", "ready"),
            full_article_status=full_article_status,
            last_error=last_error,
            redaction_count=redaction_count,
            role_language_rewrite_count=role_language_rewrite_count,
        )

        analysis.analysis_content = content
        analysis.version = int(getattr(analysis, "version", 1) or 1) + 1
        analysis.generated_at = datetime.now(tz=timezone.utc)

        await self._db.commit()
        await self._db.refresh(analysis)
        return analysis


