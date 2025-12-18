import os
import asyncio
import pytest
from httpx import AsyncClient, ASGITransport

# Minimal env for in-memory testing
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("USE_SQLITE", "true")
os.environ.setdefault("THE_ODDS_API_KEY", "test-key")
os.environ.setdefault("OPENAI_API_KEY", "test-key")

from app.main import app  # noqa: E402
from app.database.session import Base, engine  # noqa: E402


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def init_models():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    loop.run_until_complete(init_models())
    yield
    loop.run_until_complete(engine.dispose())
    loop.close()


@pytest.fixture(scope="module")
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_social_feed_empty(client: AsyncClient):
    response = await client.get("/api/social/feed")
    assert response.status_code == 200
    payload = response.json()
    assert "items" in payload
    assert isinstance(payload["items"], list)
    assert payload["items"] == []


@pytest.mark.asyncio
async def test_social_leaderboard_empty(client: AsyncClient):
    response = await client.get("/api/social/leaderboard")
    assert response.status_code == 200
    payload = response.json()
    assert "leaderboard" in payload
    assert isinstance(payload["leaderboard"], list)

