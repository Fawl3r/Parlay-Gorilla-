from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta

import pytest

from app.api.routes.analysis import _generate_slug
from app.models.game import Game
from app.models.game_analysis import GameAnalysis


@pytest.mark.asyncio
async def test_analysis_detail_generates_core_payload(client, db):
    now = datetime.utcnow()
    game = Game(
        external_game_id=f"test-{uuid.uuid4()}",
        sport="NBA",
        home_team="Boston Celtics",
        away_team="New York Knicks",
        start_time=now + timedelta(hours=6),
        status="scheduled",
    )
    db.add(game)
    await db.commit()
    await db.refresh(game)

    full_slug = _generate_slug(
        home_team=game.home_team,
        away_team=game.away_team,
        league=game.sport,
        game_time=game.start_time,
    )
    slug_part = full_slug.split("/", 1)[1]

    res = await client.get(f"/api/analysis/nba/{slug_part}?refresh=true")
    assert res.status_code == 200
    payload = res.json()
    content = payload.get("analysis_content") or {}

    assert "analysis is being prepared" not in str(content.get("opening_summary") or "").lower()
    assert isinstance(content.get("ats_trends"), dict)
    assert isinstance(content.get("totals_trends"), dict)
    assert str(content["ats_trends"].get("analysis") or "") != ""
    assert str(content["totals_trends"].get("analysis") or "") != ""
    assert str((content.get("ai_spread_pick") or {}).get("pick") or "") != ""
    assert str((content.get("ai_total_pick") or {}).get("pick") or "") != ""

    # SEO metadata should be present.
    seo = payload.get("seo_metadata") or {}
    assert isinstance(seo, dict)
    assert str(seo.get("title") or "") != ""


@pytest.mark.asyncio
async def test_refresh_regenerates_placeholder_core(client, db):
    now = datetime.utcnow()
    game = Game(
        external_game_id=f"test-{uuid.uuid4()}",
        sport="NBA",
        home_team="Los Angeles Lakers",
        away_team="Golden State Warriors",
        start_time=now + timedelta(hours=8),
        status="scheduled",
    )
    db.add(game)
    await db.commit()
    await db.refresh(game)

    full_slug = _generate_slug(
        home_team=game.home_team,
        away_team=game.away_team,
        league=game.sport,
        game_time=game.start_time,
    )
    placeholder = {
        "opening_summary": "Analysis is being prepared for Golden State Warriors @ Los Angeles Lakers. Please refresh in a moment.",
        "best_bets": [],
        "same_game_parlays": {},
        "full_article": "",
    }
    analysis = GameAnalysis(
        game_id=game.id,
        slug=full_slug,
        league="NBA",
        matchup=f"{game.away_team} @ {game.home_team}",
        analysis_content=placeholder,
        seo_metadata={"title": "Placeholder"},
        expires_at=game.start_time + timedelta(hours=2),
        version=1,
    )
    db.add(analysis)
    await db.commit()

    slug_part = full_slug.split("/", 1)[1]
    res = await client.get(f"/api/analysis/nba/{slug_part}?refresh=true")
    assert res.status_code == 200
    payload = res.json()
    content = payload.get("analysis_content") or {}
    assert "analysis is being prepared" not in str(content.get("opening_summary") or "").lower()
    assert str((content.get("ai_spread_pick") or {}).get("pick") or "") != ""


@pytest.mark.asyncio
async def test_concurrent_requests_do_not_create_duplicates(client, db):
    now = datetime.utcnow()
    game = Game(
        external_game_id=f"test-{uuid.uuid4()}",
        sport="NBA",
        home_team="Miami Heat",
        away_team="Orlando Magic",
        start_time=now + timedelta(hours=10),
        status="scheduled",
    )
    db.add(game)
    await db.commit()
    await db.refresh(game)

    full_slug = _generate_slug(
        home_team=game.home_team,
        away_team=game.away_team,
        league=game.sport,
        game_time=game.start_time,
    )
    slug_part = full_slug.split("/", 1)[1]

    async def hit():
        return await client.get(f"/api/analysis/nba/{slug_part}?refresh=true")

    r1, r2 = await asyncio.gather(hit(), hit())
    assert r1.status_code == 200
    assert r2.status_code == 200

    # Ensure only one analysis row exists for the game.
    from sqlalchemy import select
    from app.models.game_analysis import GameAnalysis as GA

    result = await db.execute(select(GA).where(GA.game_id == game.id))
    rows = result.scalars().all()
    assert len(rows) == 1


