from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.game import Game


@pytest.mark.asyncio
async def test_nfl_weeks_marks_available_when_status_scheduled(client, db: AsyncSession, monkeypatch):
    """
    Regression: if games exist but have ESPN-style status `STATUS_SCHEDULED`,
    /api/weeks/nfl must still consider the week available.
    """
    week_start = datetime.now(timezone.utc) - timedelta(days=1)
    week_end = datetime.now(timezone.utc) + timedelta(days=6)

    # Insert a game in this window with ESPN status string.
    db.add(
        Game(
            external_game_id="espn:nfl:week-test",
            sport="NFL",
            home_team="Home",
            away_team="Away",
            start_time=datetime.now(timezone.utc) + timedelta(hours=4),
            status="STATUS_SCHEDULED",
        )
    )
    await db.commit()

    # Force the weeks list to a deterministic single week window that matches the inserted game.
    import app.api.routes.games_public_routes as routes

    monkeypatch.setattr(routes, "get_current_nfl_week", lambda *args, **kwargs: 18)
    monkeypatch.setattr(
        routes,
        "get_available_weeks",
        lambda *args, **kwargs: [
            {
                "week": 18,
                "label": "Week 18",
                "is_current": True,
                "is_available": False,  # should be flipped to True by DB check
                "start_date": week_start.isoformat(),
                "end_date": week_end.isoformat(),
            }
        ],
    )

    r = await client.get("/api/weeks/nfl")
    assert r.status_code == 200
    data = r.json()
    assert data["weeks"][0]["week"] == 18
    assert data["weeks"][0]["is_available"] is True


