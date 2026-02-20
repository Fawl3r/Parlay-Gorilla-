"""
Endpoint-level integration tests: winner prediction and confidence logic
use odds + canonical/v2 team stats + API-Sports v2 feature signals across
sports via the real analysis API route. No external API calls.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, AsyncMock

import pytest

from app.api.routes.analysis import _generate_slug
from app.models.game import Game
from app.models.market import Market
from app.models.odds import Odds
from app.services.analysis.core_analysis_generator import CoreAnalysisGenerator


# -----------------------------------------------------------------------------
# NHL fixture: canonical stats + v2 features (net_strength, form_score_5, home_away_split_delta)
# -----------------------------------------------------------------------------
NHL_MATCHUP_FIXTURE = {
    "home_team_stats": {
        "record": {"wins": 42, "losses": 28, "ties": 0},
        "scoring": {"goals_for_avg": 3.4, "goals_against_avg": 2.8},
        "efficiency": {"pp_pct": 22.0, "pk_pct": 82.0},
        "last_n": {"last_5": {"wins": 3, "losses": 2, "ties": 0}},
    },
    "away_team_stats": {
        "record": {"wins": 38, "losses": 32, "ties": 0},
        "scoring": {"goals_for_avg": 2.9, "goals_against_avg": 3.1},
        "efficiency": {"pp_pct": 19.0, "pk_pct": 79.0},
        "last_n": {"last_5": {"wins": 2, "losses": 3, "ties": 0}},
    },
    "home_features": {
        "strength": {"net_strength": 0.12},
        "form": {"form_score_5": 0.15, "home_away_split_delta": 0.08},
    },
    "away_features": {
        "strength": {"net_strength": -0.05},
        "form": {"form_score_5": -0.10, "home_away_split_delta": -0.03},
    },
    "home_data_quality": {"trust_score": 0.85},
    "away_data_quality": {"trust_score": 0.82},
    "home_injuries": {"key_players_out": [], "injury_summary": "No major injuries.", "impact_assessment": "Low"},
    "away_injuries": {"key_players_out": [], "injury_summary": "No major injuries.", "impact_assessment": "Low"},
    "weather": None,
    "stats_fetched_at": "2025-03-15T19:00:00+00:00",
    "injuries_fetched_at": "2025-03-15T19:00:00+00:00",
}


# -----------------------------------------------------------------------------
# MLB fixture: runs_for_avg / runs_against_avg scoring aliases
# -----------------------------------------------------------------------------
MLB_MATCHUP_FIXTURE = {
    "home_team_stats": {
        "record": {"wins": 88, "losses": 74},
        "scoring": {"runs_for_avg": 5.2, "runs_against_avg": 4.1},
        "efficiency": {},
        "last_n": {"last_5": {"wins": 3, "losses": 2}},
    },
    "away_team_stats": {
        "record": {"wins": 82, "losses": 80},
        "scoring": {"runs_for_avg": 4.5, "runs_against_avg": 4.6},
        "efficiency": {},
        "last_n": {"last_5": {"wins": 2, "losses": 3}},
    },
    "home_features": {
        "strength": {"net_strength": 0.06},
        "form": {"form_score_5": 0.05},
    },
    "away_features": {
        "strength": {"net_strength": -0.02},
        "form": {"form_score_5": -0.04},
    },
    "home_data_quality": {"trust_score": 0.90},
    "away_data_quality": {"trust_score": 0.88},
    "home_injuries": {"key_players_out": [], "injury_summary": "None.", "impact_assessment": "N/A"},
    "away_injuries": {"key_players_out": [], "injury_summary": "None.", "impact_assessment": "N/A"},
    "weather": None,
    "stats_fetched_at": "2025-06-20T01:00:00+00:00",
    "injuries_fetched_at": "2025-06-20T01:00:00+00:00",
}


async def _add_h2h_odds(db, game_id, home_implied=0.58, away_implied=0.42):
    """Create h2h market and odds so OddsSnapshotBuilder returns valid snapshot."""
    market = Market(
        id=uuid.uuid4(),
        game_id=game_id,
        market_type="h2h",
        book="draftkings",
    )
    db.add(market)
    await db.flush()
    db.add(
        Odds(
            market_id=market.id,
            outcome="home",
            price="-140",
            decimal_price=1.714,
            implied_prob=home_implied,
        )
    )
    db.add(
        Odds(
            market_id=market.id,
            outcome="away",
            price="+120",
            decimal_price=2.20,
            implied_prob=away_implied,
        )
    )
    await db.flush()


@pytest.mark.asyncio
async def test_analysis_route_e2e_nhl_canonical_stats_and_v2_features_yields_confidence_breakdown(
    client,
    db,
):
    """NHL: odds + canonical stats + v2 features produce confidence_breakdown and non-odds_only method."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    game_time = now + timedelta(hours=24)
    game = Game(
        external_game_id=f"e2e-nhl-{uuid.uuid4()}",
        sport="NHL",
        home_team="Toronto Maple Leafs",
        away_team="Boston Bruins",
        start_time=game_time,
        status="scheduled",
    )
    db.add(game)
    await db.commit()
    await db.refresh(game)

    await _add_h2h_odds(db, game.id)
    await db.commit()

    full_slug = _generate_slug(
        home_team=game.home_team,
        away_team=game.away_team,
        league=game.sport,
        game_time=game.start_time,
    )
    slug_part = full_slug.split("/", 1)[1]

    async def _mock_safe_matchup_data(*, game, timeout_seconds):
        return NHL_MATCHUP_FIXTURE

    with patch.object(
        CoreAnalysisGenerator,
        "_safe_matchup_data",
        new=AsyncMock(side_effect=_mock_safe_matchup_data),
    ):
        res = await client.get(f"/api/analysis/nhl/{slug_part}")

    assert res.status_code == 200, res.text
    payload = res.json()
    content = (payload.get("analysis_content") or {})
    confidence_breakdown = content.get("confidence_breakdown") or {}
    model_probs = content.get("model_win_probability") or {}

    assert confidence_breakdown, "confidence_breakdown must be present"
    assert float(confidence_breakdown.get("statistical_edge", 0)) > 10
    calculation_method = (model_probs.get("calculation_method") or "").strip()
    assert calculation_method != "odds_only"
    assert calculation_method in {
        "odds_stats_features",
        "odds_and_features",
        "stats_and_features",
    }


@pytest.mark.asyncio
async def test_analysis_route_e2e_mlb_runs_scoring_aliases_do_not_break_confidence(
    client,
    db,
):
    """MLB: runs_for_avg / runs_against_avg aliases work; confidence and data_quality present."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    game_time = now + timedelta(hours=12)
    game = Game(
        external_game_id=f"e2e-mlb-{uuid.uuid4()}",
        sport="MLB",
        home_team="New York Yankees",
        away_team="Boston Red Sox",
        start_time=game_time,
        status="scheduled",
    )
    db.add(game)
    await db.commit()
    await db.refresh(game)

    await _add_h2h_odds(db, game.id, home_implied=0.55, away_implied=0.45)
    await db.commit()

    full_slug = _generate_slug(
        home_team=game.home_team,
        away_team=game.away_team,
        league=game.sport,
        game_time=game.start_time,
    )
    slug_part = full_slug.split("/", 1)[1]

    async def _mock_safe_matchup_data(*, game, timeout_seconds):
        return MLB_MATCHUP_FIXTURE

    with patch.object(
        CoreAnalysisGenerator,
        "_safe_matchup_data",
        new=AsyncMock(side_effect=_mock_safe_matchup_data),
    ):
        res = await client.get(f"/api/analysis/mlb/{slug_part}")

    assert res.status_code == 200, res.text
    payload = res.json()
    content = (payload.get("analysis_content") or {})
    confidence_breakdown = content.get("confidence_breakdown") or {}
    model_probs = content.get("model_win_probability") or {}

    assert confidence_breakdown, "confidence_breakdown must be present"
    assert float(confidence_breakdown.get("data_quality", 0)) >= 10
    home_prob = float(model_probs.get("home_win_prob") or 0)
    assert home_prob > 0.50
    calculation_method = (model_probs.get("calculation_method") or "").strip()
    assert calculation_method in (
        "odds_stats_features",
        "odds_and_features",
        "stats_and_features",
        "odds_and_stats",
        "stats_only",
        "stats_and_features",
    )
