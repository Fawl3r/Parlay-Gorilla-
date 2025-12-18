from datetime import datetime, timedelta, timezone

import pytest

from app.models.game import Game
from app.services.odds_fetcher import OddsFetcherService


@pytest.mark.asyncio
async def test_odds_fetcher_falls_back_to_espn_schedule(db, monkeypatch):
    """
    When The Odds API call fails (e.g., out of usage credits), we should still
    return upcoming games using the ESPN schedule fallback.
    """
    fetcher = OddsFetcherService(db)

    async def fake_fetch_odds_for_sport(*args, **kwargs):
        raise Exception("OUT_OF_USAGE_CREDITS")

    monkeypatch.setattr(fetcher, "fetch_odds_for_sport", fake_fetch_odds_for_sport)

    # Patch ESPN schedule service to avoid live network calls.
    from app.services import espn_schedule_games_service as espn_mod

    async def fake_ensure_upcoming_games(self, *, sport_config):
        db.add(
            Game(
                external_game_id="espn:nba:test",
                sport=sport_config.code,
                home_team="Home Team",
                away_team="Away Team",
                start_time=datetime.now(tz=timezone.utc) + timedelta(hours=2),
                status="scheduled",
            )
        )
        await db.commit()
        return 1

    monkeypatch.setattr(
        espn_mod.EspnScheduleGamesService, "ensure_upcoming_games", fake_ensure_upcoming_games
    )

    games = await fetcher.get_or_fetch_games("nba", force_refresh=True)
    assert len(games) >= 1
    assert games[0].home_team == "Home Team"
    assert games[0].away_team == "Away Team"




