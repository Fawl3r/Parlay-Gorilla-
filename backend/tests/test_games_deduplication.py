from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.models.game import Game
from app.models.market import Market
from app.models.odds import Odds
from app.services.espn_schedule_games_service import EspnScheduleGamesService
from app.services.game_match_key import build_canonical_key
from app.services.game_time_corrector import GameTimeCorrector
from app.services.games_deduplication_service import GamesDeduplicationService
from app.services.odds_fetcher import OddsFetcherService
from app.services.sports_config import get_sport_config
from app.services.team_name_normalizer import TeamNameNormalizer


@pytest.mark.asyncio
async def test_get_or_fetch_games_dedupes_schedule_duplicates_prefers_odds(db):
    """
    If both an ESPN schedule placeholder game and an OddsAPI game exist for the same matchup/time,
    the API response should return only one row and prefer the one with markets/odds.
    """

    sport_config = get_sport_config("nfl")
    start_time = datetime.now(tz=timezone.utc) + timedelta(hours=2)
    # Same 5-min bucket: e.g. 17:30 and 17:32 both floor to 17:30 (not 17:35).
    bucket_start = start_time.replace(minute=(start_time.minute // 5) * 5, second=0, microsecond=0)

    schedule_game = Game(
        external_game_id="espn:nfl:test-1",
        sport=sport_config.code,
        home_team="Los Angeles Rams",
        away_team="Seattle Seahawks",
        start_time=bucket_start,
        status="scheduled",
    )
    odds_game = Game(
        external_game_id="odds:test-1",
        sport=sport_config.code,
        home_team="Los Angeles Rams",
        away_team="Seattle Seahawks",
        start_time=bucket_start + timedelta(minutes=2),
        status="scheduled",
    )

    db.add_all([schedule_game, odds_game])
    await db.flush()

    market = Market(game_id=odds_game.id, market_type="h2h", book="testbook")
    db.add(market)
    await db.flush()

    db.add_all(
        [
            Odds(
                market_id=market.id,
                outcome="home",
                price="-120",
                decimal_price=1.8333,
                implied_prob=0.5454,
            ),
            Odds(
                market_id=market.id,
                outcome="away",
                price="+100",
                decimal_price=2.0,
                implied_prob=0.5,
            ),
        ]
    )
    await db.commit()

    fetcher = OddsFetcherService(db)
    games = await fetcher.get_or_fetch_games("nfl", force_refresh=False)

    assert len(games) == 1
    assert games[0].home_team == "Los Angeles Rams"
    assert games[0].away_team == "Seattle Seahawks"
    assert games[0].markets, "Expected the deduped game to include markets/odds"
    assert not games[0].external_game_id.startswith("espn:")


@pytest.mark.asyncio
async def test_espn_schedule_upsert_matches_existing_game_by_matchup_time(db, monkeypatch):
    """
    The ESPN fallback should not create a duplicate `Game` row when an OddsAPI game already exists
    for the same matchup/time.
    """

    sport_config = get_sport_config("nfl")
    today = datetime.utcnow().date()
    start_time = datetime.now(tz=timezone.utc) + timedelta(hours=2)

    existing = Game(
        external_game_id="odds:existing",
        sport=sport_config.code,
        home_team="Los Angeles Rams",
        away_team="Seattle Seahawks",
        start_time=start_time,
        status="scheduled",
    )
    db.add(existing)
    await db.commit()

    async def fake_fetch_espn_schedule_for_date(self, target_date, sport_code="NFL"):
        if sport_code != sport_config.code or target_date != today:
            return []
        return [
            {
                "event_id": "999",
                "home_team": "Los Angeles Rams",
                "away_team": "Seattle Seahawks",
                "start_time": start_time,
                "status": "STATUS_SCHEDULED",
            }
        ]

    monkeypatch.setattr(GameTimeCorrector, "fetch_espn_schedule_for_date", fake_fetch_espn_schedule_for_date)

    service = EspnScheduleGamesService(db)
    await service.ensure_upcoming_games(sport_config=sport_config)

    result = await db.execute(select(Game).where(Game.sport == sport_config.code))
    games = result.scalars().all()
    assert len(games) == 1
    assert games[0].external_game_id == "odds:existing"


def test_minute_drift_same_5min_bucket_same_canonical_key():
    """Start times 1–4 minutes apart in the same 5-min bucket produce the same canonical key."""
    normalizer = TeamNameNormalizer()
    base = datetime(2026, 2, 20, 18, 30, 0, tzinfo=timezone.utc)
    k30 = build_canonical_key("NFL", "Chiefs", "Bills", base, team_normalizer=normalizer, sport_for_normalizer="NFL")
    k33 = build_canonical_key(
        "NFL", "Chiefs", "Bills",
        base.replace(minute=33, second=0, microsecond=0),
        team_normalizer=normalizer,
        sport_for_normalizer="NFL",
    )
    assert k30 == k33


@pytest.mark.asyncio
async def test_swapped_home_away_same_canonical_key(db, monkeypatch):
    """ESPN returns swapped home/away for same matchup; no duplicate row created."""
    sport_config = get_sport_config("nfl")
    today = datetime.utcnow().date()
    start_time = datetime.now(tz=timezone.utc) + timedelta(hours=3)

    existing = Game(
        external_game_id="odds:swap-test",
        sport=sport_config.code,
        home_team="Ravens",
        away_team="49ers",
        start_time=start_time,
        status="scheduled",
    )
    db.add(existing)
    await db.commit()

    # ESPN returns 49ers @ Ravens (away @ home)
    async def fake_fetch_espn(self, target_date, sport_code="NFL"):
        if sport_code != sport_config.code or target_date != today:
            return []
        return [
            {
                "event_id": "888",
                "home_team": "49ers",
                "away_team": "Ravens",
                "start_time": start_time,
                "status": "STATUS_SCHEDULED",
            }
        ]

    monkeypatch.setattr(GameTimeCorrector, "fetch_espn_schedule_for_date", fake_fetch_espn)
    service = EspnScheduleGamesService(db)
    await service.ensure_upcoming_games(sport_config=sport_config)

    result = await db.execute(select(Game).where(Game.sport == sport_config.code))
    games = result.scalars().all()
    assert len(games) == 1
    assert games[0].external_game_id == "odds:swap-test"


def test_canonical_key_order_insensitive():
    """Canonical key is same for swapped home/away."""
    normalizer = TeamNameNormalizer()
    start = datetime(2026, 2, 20, 18, 30, 0, tzinfo=timezone.utc)
    k1 = build_canonical_key("NFL", "Chiefs", "Bills", start, team_normalizer=normalizer, sport_for_normalizer="NFL")
    k2 = build_canonical_key("NFL", "Bills", "Chiefs", start, team_normalizer=normalizer, sport_for_normalizer="NFL")
    assert k1 == k2

