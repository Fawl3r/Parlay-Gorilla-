"""Test configuration."""

pytest_plugins = ("pytest_asyncio.plugin",)

import os
from pathlib import Path
from typing import Any, AsyncIterator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

# --------------------------------------------------------------------------------------
# Force a clean, isolated DB for tests.
#
# IMPORTANT:
# - Do NOT use USE_SQLITE=true because app.database.session will then force a fixed
#   `parlay_gorilla.db` path (persistent across runs) and tests will contaminate dev data.
# - Instead, point DATABASE_URL at a dedicated sqlite file for the test run.
# --------------------------------------------------------------------------------------

_TEST_DB_PATH = Path(__file__).resolve().parent / ".pytest-db.sqlite"
try:
    if _TEST_DB_PATH.exists():
        _TEST_DB_PATH.unlink()
except Exception:
    # Best-effort; table creation below will fail loudly if something is wrong.
    pass

os.environ["ENVIRONMENT"] = "testing"
os.environ["DEBUG"] = "false"
os.environ["USE_SQLITE"] = "false"
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_TEST_DB_PATH.as_posix()}"
os.environ["THE_ODDS_API_KEY"] = os.environ.get("THE_ODDS_API_KEY", "test-key")
os.environ["OPENAI_ENABLED"] = "false"
os.environ["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY", "test-key")
os.environ["PROBABILITY_EXTERNAL_FETCH_ENABLED"] = "false"
os.environ["PROBABILITY_PREFETCH_ENABLED"] = "false"
os.environ["DISABLE_RATE_LIMITS"] = "true"

# Webhook secrets: keep tests offline and deterministic.
# If a developer has these set in their shell, webhook routes would start enforcing
# signatures and make tests flaky/harder to run locally.
os.environ["COINBASE_COMMERCE_WEBHOOK_SECRET"] = ""
os.environ["LEMONSQUEEZY_WEBHOOK_SECRET"] = ""

# Web Push: force disabled for deterministic tests (avoid leaking developer env config).
os.environ["WEB_PUSH_ENABLED"] = "false"
os.environ["WEB_PUSH_VAPID_PUBLIC_KEY"] = ""
os.environ["WEB_PUSH_VAPID_PRIVATE_KEY"] = ""
os.environ["WEB_PUSH_SUBJECT"] = ""

# Ensure tests never reuse a previous run's DB (important on Windows where file
# handles can prevent cleanup).
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_TEST_DB_PATH.as_posix()}?cache=shared&mode=rwc"

from app.main import app
from app.database.session import AsyncSessionLocal, Base, engine


@pytest.fixture(scope="session", autouse=True)
def _init_test_db() -> None:
    """
    Ensure tables exist for integration-style tests.

    Uses the configured SQLite DB for local testing. This keeps the test suite
    self-contained without requiring a running Postgres instance.
    """
    import asyncio

    async def init_models():
        # Ensure all models are registered with SQLAlchemy metadata for create_all.
        import app.models  # noqa: F401
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    loop = asyncio.get_event_loop_policy().new_event_loop()
    loop.run_until_complete(init_models())
    loop.close()


@pytest.fixture(autouse=True)
async def _clear_db_between_tests(db: AsyncSession):
    """
    Hard reset the test DB between tests to avoid cross-test collisions
    (e.g., unique `game_analyses.slug`).
    """
    from sqlalchemy import text
    from app.database.session import Base

    # Delete all rows from all tables between tests to avoid unique constraint collisions.
    # Use SQLAlchemy's dependency ordering to delete children before parents.
    for table in reversed(Base.metadata.sorted_tables):
        await db.execute(text(f'DELETE FROM "{table.name}"'))
    await db.commit()
    yield


@pytest.fixture
async def db() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session


@pytest.fixture
async def client() -> AsyncIterator[Any]:
    # Lazy import so unit tests that don't need an HTTP client don't pay the httpx import cost.
    from httpx import ASGITransport, AsyncClient

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture(autouse=True)
def _disable_external_matchup_fetch(monkeypatch):
    """
    Prevent flaky external HTTP calls (ESPN/API-Sports) during tests.

    Core analysis generation should be resilient without external stats; tests should
    be deterministic and offline-friendly.
    """
    from app.services.stats_scraper import StatsScraperService

    async def _stub_get_matchup_data(self: StatsScraperService, home_team: str, away_team: str, league: str, season: str, game_time):
        home_stats = await self.get_team_stats(home_team, season, bypass_cache=False)
        away_stats = await self.get_team_stats(away_team, season, bypass_cache=False)
        if not home_stats:
            home_stats = self._zero_stats(home_team, season)
        if not away_stats:
            away_stats = self._zero_stats(away_team, season)

        return {
            "home_team_stats": home_stats,
            "away_team_stats": away_stats,
            "weather": None,
            "home_injuries": {"key_players_out": [], "injury_summary": "Injuries unavailable in test mode.", "impact_assessment": "N/A"},
            "away_injuries": {"key_players_out": [], "injury_summary": "Injuries unavailable in test mode.", "impact_assessment": "N/A"},
        }

    monkeypatch.setattr(StatsScraperService, "get_matchup_data", _stub_get_matchup_data)

