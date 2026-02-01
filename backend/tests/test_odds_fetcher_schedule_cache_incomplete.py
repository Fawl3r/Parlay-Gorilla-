import pytest
from datetime import datetime, timedelta

from app.models.game import Game
from app.services.odds_fetcher import OddsFetcherService


@pytest.mark.asyncio
async def test_schedule_only_db_rows_do_not_block_odds_fetch(db, monkeypatch):
    """
    If the DB contains schedule-only games (no markets/odds), the odds fetcher must NOT treat
    that as a cache hit. It should fall through to the odds-fetch path so h2h markets can appear.
    """
    # Clear in-process cache (class-level) so it doesn't mask the behavior.
    OddsFetcherService._games_cache = {}

    # Insert a schedule-only NHL game (markets are absent because they are a separate table).
    game = Game(
        external_game_id="espn:nhl:test-event-1",
        sport="NHL",
        home_team="Detroit Red Wings",
        away_team="Colorado Avalanche",
        start_time=datetime.utcnow() + timedelta(days=1),
        status="scheduled",
    )
    db.add(game)
    await db.commit()

    async def _fake_fetch_odds_for_sport(self, sport_config, markets=None, force_refresh=False, include_premium_markets=False):
        # Minimal The Odds API payload shape that our data store expects.
        commence = (datetime.utcnow() + timedelta(days=1)).isoformat().replace("+00:00", "Z")
        return [
            {
                "id": "odds-nhl-test-1",
                "home_team": "Detroit Red Wings",
                "away_team": "Colorado Avalanche",
                "commence_time": commence,
                "bookmakers": [
                    {
                        "key": "fanduel",
                        "markets": [
                            {
                                "key": "h2h",
                                "outcomes": [
                                    {"name": "Colorado Avalanche", "price": -110},
                                    {"name": "Detroit Red Wings", "price": -110},
                                ],
                            }
                        ],
                    }
                ],
            }
        ]

    monkeypatch.setattr(OddsFetcherService, "fetch_odds_for_sport", _fake_fetch_odds_for_sport)

    svc = OddsFetcherService(db)
    games = await svc.get_or_fetch_games("nhl", force_refresh=False)

    assert any(
        any(m.market_type.lower() == "h2h" and len(m.odds) >= 2 for m in g.markets)
        for g in games
    ), "Expected at least one returned game to include a usable h2h market"

