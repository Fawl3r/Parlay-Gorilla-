from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.models.game import Game
from app.services.odds_api.odds_api_data_store import OddsApiDataStore
from app.services.sports_config import get_sport_config


@pytest.mark.asyncio
async def test_soccer_h2h_stores_draw_separately(db):
    sport_config = get_sport_config("mls")
    store = OddsApiDataStore(db)

    commence = datetime.now(tz=timezone.utc) + timedelta(hours=8)
    commence_str = commence.isoformat().replace("+00:00", "Z")

    api_data = [
        {
            "id": "odds-mls-1",
            "home_team": "Seattle Sounders FC",
            "away_team": "LA Galaxy",
            "commence_time": commence_str,
            "bookmakers": [
                {
                    "key": "draftkings",
                    "markets": [
                        {
                            "key": "h2h",
                            "outcomes": [
                                {"name": "Seattle Sounders FC", "price": -120},
                                {"name": "Draw", "price": 250},
                                {"name": "LA Galaxy", "price": 300},
                            ],
                        }
                    ],
                }
            ],
        }
    ]

    games = await store.normalize_and_store_odds(api_data, sport_config)
    assert len(games) == 1

    # Query the stored odds outcomes for the created game.
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    from app.models.market import Market

    result = await db.execute(
        select(Market)
        .where(Market.game_id == games[0].id)
        .where(Market.market_type == "h2h")
        .options(selectinload(Market.odds))
    )
    market = result.scalar_one()

    by_outcome = {str(o.outcome).lower(): str(o.price) for o in (market.odds or [])}
    assert by_outcome.get("home") == "-120"
    assert by_outcome.get("away") == "+300"
    assert by_outcome.get("draw") == "+250"


@pytest.mark.asyncio
async def test_soccer_promotes_espn_placeholder_to_oddsapi_id_with_normalized_team_names(db):
    sport_config = get_sport_config("mls")
    store = OddsApiDataStore(db)

    commence = datetime.utcnow() + timedelta(hours=6)

    # ESPN placeholder uses a slightly different team name (no FC suffix).
    existing = Game(
        external_game_id="espn:mls:123",
        sport=sport_config.code,
        home_team="Seattle Sounders",
        away_team="LA Galaxy",
        start_time=commence,
        status="scheduled",
    )
    db.add(existing)
    await db.commit()

    commence_str = commence.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
    api_data = [
        {
            "id": "odds-mls-123",
            "home_team": "Seattle Sounders FC",
            "away_team": "LA Galaxy",
            "commence_time": commence_str,
            "bookmakers": [],
        }
    ]

    await store.normalize_and_store_odds(api_data, sport_config)

    from sqlalchemy import select

    result = await db.execute(select(Game).where(Game.sport == sport_config.code))
    rows = result.scalars().all()
    assert len(rows) == 1
    assert rows[0].external_game_id == "odds-mls-123"
    assert rows[0].home_team == "Seattle Sounders FC"


