from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.models.game import Game
from app.models.market import Market
from app.models.odds import Odds
from app.services.analysis.core_analysis_generator import CoreAnalysisGenerator
from app.services.odds_history.odds_history_snapshot_repository import OddsHistorySnapshotRepository


class _StubStatsScraper:
    def clear_cache(self) -> None:
        return None

    async def get_matchup_data(self, **kwargs):
        home = kwargs.get("home_team") or "Home"
        away = kwargs.get("away_team") or "Away"
        return {
            "home_team_stats": {
                "ats_trends": {"wins": 5, "losses": 3, "pushes": 0, "win_percentage": 62.5, "recent": "3-2"},
                "over_under_trends": {"overs": 4, "unders": 4, "over_percentage": 50.0, "avg_total_points": 44.2},
            },
            "away_team_stats": {
                "ats_trends": {"wins": 4, "losses": 4, "pushes": 0, "win_percentage": 50.0, "recent": "2-3"},
                "over_under_trends": {"overs": 5, "unders": 3, "over_percentage": 62.5, "avg_total_points": 45.8},
            },
            "weather": None,
            "home_injuries": {"key_players_out": [], "injury_summary": "", "impact_assessment": ""},
            "away_injuries": {"key_players_out": [], "injury_summary": "", "impact_assessment": ""},
        }


@pytest.mark.asyncio
async def test_core_analysis_includes_market_movement_when_snapshot_present(db):
    # Create a game with odds-backed external id.
    game = Game(
        external_game_id="evt_test_1",
        sport="NFL",
        home_team="Seattle Seahawks",
        away_team="Los Angeles Rams",
        start_time=datetime.now(tz=timezone.utc),
        status="scheduled",
    )
    db.add(game)
    await db.flush()

    # Create basic markets/odds (current).
    h2h = Market(game_id=game.id, market_type="h2h", book="draftkings")
    spreads = Market(game_id=game.id, market_type="spreads", book="draftkings")
    totals = Market(game_id=game.id, market_type="totals", book="draftkings")
    db.add_all([h2h, spreads, totals])
    await db.flush()

    db.add_all(
        [
            Odds(market_id=h2h.id, outcome="home", price="-120", decimal_price=1.833, implied_prob=0.546),
            Odds(market_id=h2h.id, outcome="away", price="+100", decimal_price=2.000, implied_prob=0.500),
            Odds(
                market_id=spreads.id,
                outcome="Seattle Seahawks -1.5",
                price="-110",
                decimal_price=1.909,
                implied_prob=0.524,
            ),
            Odds(
                market_id=spreads.id,
                outcome="Los Angeles Rams +1.5",
                price="-110",
                decimal_price=1.909,
                implied_prob=0.524,
            ),
            Odds(market_id=totals.id, outcome="Over 47.5", price="-110", decimal_price=1.909, implied_prob=0.524),
            Odds(market_id=totals.id, outcome="Under 47.5", price="-110", decimal_price=1.909, implied_prob=0.524),
        ]
    )
    await db.commit()

    # Insert a historical lookback snapshot with different lines.
    repo = OddsHistorySnapshotRepository(db)
    await repo.upsert(
        external_game_id=game.external_game_id,
        sport_key="americanfootball_nfl",
        snapshot_kind="lookback_24h",
        snapshot_date=datetime.now(tz=timezone.utc).date(),
        requested_at=datetime.now(tz=timezone.utc),
        snapshot_time=datetime.now(tz=timezone.utc),
        data={
            "book": "draftkings",
            "home_team": game.home_team,
            "away_team": game.away_team,
            "home_implied_prob": 0.500,
            "away_implied_prob": 0.500,
            "home_spread_point": 1.5,
            "total_line": 44.5,
        },
    )
    await db.commit()

    # Sanity: ensure snapshot exists.
    snap = await repo.get_latest_for_game(external_game_id=game.external_game_id, snapshot_kind="lookback_24h")
    assert snap is not None

    # Generate core analysis; should include market_movement.
    gen = CoreAnalysisGenerator(db, stats_scraper=_StubStatsScraper())
    core = await gen.generate(game=game, timeout_seconds=3.0)

    mm = core.get("market_movement")
    assert isinstance(mm, dict)
    assert "summary" in mm
    assert "Spread" in (mm.get("summary") or "")
    assert "Total" in (mm.get("summary") or "")


