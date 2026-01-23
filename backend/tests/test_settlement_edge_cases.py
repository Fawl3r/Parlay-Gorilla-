"""Edge case tests for settlement system."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from decimal import Decimal
import pytest
from sqlalchemy import select

from app.models.game import Game
from app.models.parlay import Parlay
from app.models.parlay_leg import ParlayLeg
from app.models.saved_parlay import SavedParlay
from app.models.user import User
from app.services.settlement.settlement_service import SettlementService


@pytest.mark.asyncio
async def test_settlement_with_null_home_score(db):
    """Test settlement when home_score is None."""
    now = datetime.now(timezone.utc)
    
    game = Game(
        external_game_id="test_edge_null_home",
        sport="NFL",
        home_team="Home Team",
        away_team="Away Team",
        start_time=now - timedelta(hours=2),
        status="FINAL",
        home_score=None,
        away_score=14,
    )
    db.add(game)
    await db.flush()
    
    parlay = Parlay(
        user_id=None,
        legs=[],
        num_legs=1,
        parlay_hit_prob=Decimal("0.55"),
        risk_profile="balanced",
        status="PENDING",
    )
    db.add(parlay)
    await db.flush()
    
    leg = ParlayLeg(
        parlay_id=parlay.id,
        game_id=game.id,
        market_type="h2h",
        selection="Home Team",
        status="PENDING",
    )
    db.add(leg)
    await db.commit()
    
    service = SettlementService(db)
    settled_count = await service.settle_parlay_legs_for_game(game.id)
    await db.commit()
    
    # Should VOID the leg
    assert settled_count == 1
    await db.refresh(leg)
    assert leg.status == "VOID"


@pytest.mark.asyncio
async def test_settlement_with_null_away_score(db):
    """Test settlement when away_score is None."""
    now = datetime.now(timezone.utc)
    
    game = Game(
        external_game_id="test_edge_null_away",
        sport="NFL",
        home_team="Home Team",
        away_team="Away Team",
        start_time=now - timedelta(hours=2),
        status="FINAL",
        home_score=28,
        away_score=None,
    )
    db.add(game)
    await db.flush()
    
    leg = ParlayLeg(
        game_id=game.id,
        market_type="h2h",
        selection="Home Team",
        status="PENDING",
    )
    db.add(leg)
    await db.commit()
    
    service = SettlementService(db)
    settled_count = await service.settle_parlay_legs_for_game(game.id)
    await db.commit()
    
    assert settled_count == 1
    await db.refresh(leg)
    assert leg.status == "VOID"


@pytest.mark.asyncio
async def test_settlement_with_missing_line_spread(db):
    """Test spread leg with missing line."""
    now = datetime.now(timezone.utc)
    
    game = Game(
        external_game_id="test_edge_missing_line",
        sport="NFL",
        home_team="Home Team",
        away_team="Away Team",
        start_time=now - timedelta(hours=2),
        status="FINAL",
        home_score=28,
        away_score=14,
    )
    db.add(game)
    await db.flush()
    
    leg = ParlayLeg(
        game_id=game.id,
        market_type="spreads",
        selection="Home Team",
        line=None,  # Missing line
        status="PENDING",
    )
    db.add(leg)
    await db.commit()
    
    service = SettlementService(db)
    settled_count = await service.settle_parlay_legs_for_game(game.id)
    await db.commit()
    
    assert settled_count == 1
    await db.refresh(leg)
    assert leg.status == "VOID"


@pytest.mark.asyncio
async def test_settlement_with_missing_line_totals(db):
    """Test totals leg with missing line."""
    now = datetime.now(timezone.utc)
    
    game = Game(
        external_game_id="test_edge_missing_line_total",
        sport="NFL",
        home_team="Home Team",
        away_team="Away Team",
        start_time=now - timedelta(hours=2),
        status="FINAL",
        home_score=28,
        away_score=14,
    )
    db.add(game)
    await db.flush()
    
    leg = ParlayLeg(
        game_id=game.id,
        market_type="totals",
        selection="over 46.5",
        line=None,  # Missing line
        status="PENDING",
    )
    db.add(leg)
    await db.commit()
    
    service = SettlementService(db)
    settled_count = await service.settle_parlay_legs_for_game(game.id)
    await db.commit()
    
    assert settled_count == 1
    await db.refresh(leg)
    assert leg.status == "VOID"


@pytest.mark.asyncio
async def test_settlement_with_invalid_market_type(db):
    """Test leg with invalid market_type."""
    now = datetime.now(timezone.utc)
    
    game = Game(
        external_game_id="test_edge_invalid_market",
        sport="NFL",
        home_team="Home Team",
        away_team="Away Team",
        start_time=now - timedelta(hours=2),
        status="FINAL",
        home_score=28,
        away_score=14,
    )
    db.add(game)
    await db.flush()
    
    leg = ParlayLeg(
        game_id=game.id,
        market_type="invalid_type",
        selection="Home Team",
        status="PENDING",
    )
    db.add(leg)
    await db.commit()
    
    service = SettlementService(db)
    settled_count = await service.settle_parlay_legs_for_game(game.id)
    await db.commit()
    
    # Should VOID invalid market types
    assert settled_count == 1
    await db.refresh(leg)
    assert leg.status == "VOID"


@pytest.mark.asyncio
async def test_settlement_parlay_with_no_legs(db):
    """Test parlay with no legs is skipped."""
    parlay = Parlay(
        user_id=None,
        legs=[],
        num_legs=0,
        parlay_hit_prob=Decimal("0.50"),
        risk_profile="balanced",
        status="PENDING",
    )
    db.add(parlay)
    await db.commit()
    
    service = SettlementService(db)
    stats = await service.settle_all_pending_parlays()
    await db.commit()
    
    # Should skip parlay with no legs
    assert stats.parlays_settled == 0


@pytest.mark.asyncio
async def test_settlement_orphaned_leg_no_parlay(db):
    """Test leg with no parlay_id or saved_parlay_id."""
    now = datetime.now(timezone.utc)
    
    game = Game(
        external_game_id="test_edge_orphan",
        sport="NFL",
        home_team="Home Team",
        away_team="Away Team",
        start_time=now - timedelta(hours=2),
        status="FINAL",
        home_score=28,
        away_score=14,
    )
    db.add(game)
    await db.flush()
    
    # Orphaned leg (no parlay_id or saved_parlay_id)
    leg = ParlayLeg(
        game_id=game.id,
        market_type="h2h",
        selection="Home Team",
        status="PENDING",
    )
    db.add(leg)
    await db.commit()
    
    service = SettlementService(db)
    settled_count = await service.settle_parlay_legs_for_game(game.id)
    await db.commit()
    
    # Should still settle orphaned leg
    assert settled_count == 1
    await db.refresh(leg)
    assert leg.status == "WON"


@pytest.mark.asyncio
async def test_settlement_large_batch_of_games(db):
    """Test settlement with many games going FINAL simultaneously."""
    now = datetime.now(timezone.utc)
    
    # Create 50 FINAL games
    games = []
    for i in range(50):
        game = Game(
            external_game_id=f"test_edge_batch_{i}",
            sport="NFL",
            home_team=f"Home {i}",
            away_team=f"Away {i}",
            start_time=now - timedelta(hours=1),
            status="FINAL",
            home_score=28,
            away_score=14,
        )
        games.append(game)
    
    db.add_all(games)
    await db.flush()
    
    # Create legs for each game
    legs = []
    for game in games:
        leg = ParlayLeg(
            game_id=game.id,
            market_type="h2h",
            selection="Home Team",
            status="PENDING",
        )
        legs.append(leg)
    
    db.add_all(legs)
    await db.commit()
    
    service = SettlementService(db)
    
    # Process all games
    total_settled = 0
    for game in games:
        settled = await service.settle_parlay_legs_for_game(game.id)
        total_settled += settled
    
    await db.commit()
    
    # Should settle all legs
    assert total_settled == 50
    
    # Verify all legs were settled
    for leg in legs:
        await db.refresh(leg)
        assert leg.status == "WON"
        assert leg.settled_at is not None


@pytest.mark.asyncio
async def test_settlement_zero_scores(db):
    """Test settlement with zero scores."""
    now = datetime.now(timezone.utc)
    
    game = Game(
        external_game_id="test_edge_zero",
        sport="NFL",
        home_team="Home Team",
        away_team="Away Team",
        start_time=now - timedelta(hours=2),
        status="FINAL",
        home_score=0,
        away_score=0,
    )
    db.add(game)
    await db.flush()
    
    leg = ParlayLeg(
        game_id=game.id,
        market_type="h2h",
        selection="Home Team",
        status="PENDING",
    )
    db.add(leg)
    await db.commit()
    
    service = SettlementService(db)
    settled_count = await service.settle_parlay_legs_for_game(game.id)
    await db.commit()
    
    # Tie game should result in LOST per business rules
    assert settled_count == 1
    await db.refresh(leg)
    assert leg.status == "LOST"


@pytest.mark.asyncio
async def test_settlement_very_large_scores(db):
    """Test settlement with very large scores."""
    now = datetime.now(timezone.utc)
    
    game = Game(
        external_game_id="test_edge_large",
        sport="NBA",
        home_team="Home Team",
        away_team="Away Team",
        start_time=now - timedelta(hours=2),
        status="FINAL",
        home_score=150,
        away_score=120,
    )
    db.add(game)
    await db.flush()
    
    leg = ParlayLeg(
        game_id=game.id,
        market_type="h2h",
        selection="Home Team",
        status="PENDING",
    )
    db.add(leg)
    await db.commit()
    
    service = SettlementService(db)
    settled_count = await service.settle_parlay_legs_for_game(game.id)
    await db.commit()
    
    assert settled_count == 1
    await db.refresh(leg)
    assert leg.status == "WON"


@pytest.mark.asyncio
async def test_settlement_spread_exact_push(db):
    """Test spread leg that pushes exactly."""
    now = datetime.now(timezone.utc)
    
    game = Game(
        external_game_id="test_edge_push",
        sport="NFL",
        home_team="Home Team",
        away_team="Away Team",
        start_time=now - timedelta(hours=2),
        status="FINAL",
        home_score=24,
        away_score=20,  # Margin: +4
    )
    db.add(game)
    await db.flush()
    
    leg = ParlayLeg(
        game_id=game.id,
        market_type="spreads",
        selection="Home Team",
        line=Decimal("-4.0"),  # Exactly matches margin
        status="PENDING",
    )
    db.add(leg)
    await db.commit()
    
    service = SettlementService(db)
    settled_count = await service.settle_parlay_legs_for_game(game.id)
    await db.commit()
    
    assert settled_count == 1
    await db.refresh(leg)
    assert leg.status == "PUSH"


@pytest.mark.asyncio
async def test_settlement_totals_exact_push(db):
    """Test totals leg that pushes exactly."""
    now = datetime.now(timezone.utc)
    
    game = Game(
        external_game_id="test_edge_total_push",
        sport="NFL",
        home_team="Home Team",
        away_team="Away Team",
        start_time=now - timedelta(hours=2),
        status="FINAL",
        home_score=24,
        away_score=22,  # Total: 46
    )
    db.add(game)
    await db.flush()
    
    leg = ParlayLeg(
        game_id=game.id,
        market_type="totals",
        selection="over 46.0",
        line=Decimal("46.0"),  # Exactly matches total
        status="PENDING",
    )
    db.add(leg)
    await db.commit()
    
    service = SettlementService(db)
    settled_count = await service.settle_parlay_legs_for_game(game.id)
    await db.commit()
    
    assert settled_count == 1
    await db.refresh(leg)
    assert leg.status == "PUSH"
