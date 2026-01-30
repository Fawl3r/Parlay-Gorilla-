"""Runner-level test: full article job stores sanitized article (player names removed)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.game import Game
from app.models.game_analysis import GameAnalysis
from app.services.analysis.full_article_job_runner import FullArticleJobRunner


@pytest.mark.asyncio
async def test_full_article_job_runner_stores_sanitized_article(db):
    """Mock generator returns article with player name; assert stored article is sanitized."""
    game = Game(
        id=uuid.uuid4(),
        external_game_id="test-full-article-sanitize-1",
        sport="NFL",
        home_team="Seahawks",
        away_team="Raiders",
        start_time=datetime.now(timezone.utc),
    )
    db.add(game)
    await db.flush()

    analysis = GameAnalysis(
        id=uuid.uuid4(),
        game_id=game.id,
        slug="nfl/raiders-vs-seahawks-test-sanitize",
        league="NFL",
        matchup="Raiders @ Seahawks",
        analysis_content={},
        version=1,
    )
    db.add(analysis)
    await db.commit()
    await db.refresh(game)
    await db.refresh(analysis)

    raw_article = "## Opening Summary\n\nThe Seahawks are led by Geno Smith on offense."

    class _FakeSessionLocal:
        def __init__(self, session):
            self._session = session

        async def __aenter__(self):
            return self._session

        async def __aexit__(self, *args):
            pass

    with (
        patch(
            "app.services.analysis.full_article_job_runner.FullArticleGenerator",
        ) as MockGen,
        patch(
            "app.services.analysis.full_article_job_runner.AsyncSessionLocal",
            return_value=_FakeSessionLocal(db),
        ),
    ):
        mock_generator = MagicMock()
        mock_generator.enabled = True
        mock_generator.generate = AsyncMock(return_value=raw_article)
        MockGen.return_value = mock_generator

        runner = FullArticleJobRunner()
        await runner._run(analysis_id=str(analysis.id))

    await db.refresh(analysis)
    content = analysis.analysis_content or {}
    full_article = content.get("full_article", "")
    assert "Geno Smith" not in full_article
    assert "led by its core playmakers" in full_article
