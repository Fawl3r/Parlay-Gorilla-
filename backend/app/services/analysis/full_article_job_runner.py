"""In-process background runner for full-article generation.

This runner is best-effort: tasks may be lost on process restart. The core
analysis remains available immediately. The scheduler can be extended later
to re-queue missing full articles if desired.
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Optional

from sqlalchemy import select

from app.database.session import AsyncSessionLocal
from app.core.config import settings
from app.models.game import Game
from app.models.game_analysis import GameAnalysis
from app.services.analysis.analysis_repository import AnalysisRepository
from app.services.analysis.full_article_generator import FullArticleGenerator


class FullArticleJobRunner:
    def __init__(self, *, generator: Optional[FullArticleGenerator] = None):
        self._generator = generator or FullArticleGenerator()

    @property
    def enabled(self) -> bool:
        return bool(settings.analysis_full_article_enabled) and self._generator.enabled

    def enqueue(self, *, analysis_id: str) -> None:
        if not self.enabled:
            return
        asyncio.create_task(self._run(analysis_id=analysis_id))

    async def _run(self, *, analysis_id: str) -> None:
        try:
            analysis_uuid = uuid.UUID(analysis_id)
        except Exception:
            return

        async with AsyncSessionLocal() as db:
            repo = AnalysisRepository(db)
            lock = repo.article_lock(analysis_id=analysis_id)
            async with lock:
                result = await db.execute(select(GameAnalysis).where(GameAnalysis.id == analysis_uuid))
                analysis = result.scalar_one_or_none()
                if not analysis:
                    return

                content = analysis.analysis_content or {}
                if isinstance(content, dict) and str(content.get("full_article") or "").strip():
                    # Already generated.
                    return

                game_result = await db.execute(select(Game).where(Game.id == analysis.game_id))
                game = game_result.scalar_one_or_none()
                if not game:
                    return

                article = await self._generator.generate(
                    game=game,
                    core_content=content if isinstance(content, dict) else {},
                    timeout_seconds=settings.analysis_full_article_timeout_seconds,
                )
                if article.strip():
                    await repo.update_full_article(
                        analysis=analysis,
                        full_article=article,
                        full_article_status="ready",
                    )
                else:
                    await repo.update_full_article(
                        analysis=analysis,
                        full_article="",
                        full_article_status="error",
                        last_error="Full article generation failed or timed out.",
                    )


