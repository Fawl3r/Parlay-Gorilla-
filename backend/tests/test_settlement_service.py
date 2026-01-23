"""Integration tests for SettlementService."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from decimal import Decimal
import pytest
from sqlalchemy import select

from app.models.game import Game
from app.models.parlay import Parlay
from app.models.parlay_leg import ParlayLeg
from app.models.saved_parlay import SavedParlay
from app.models.parlay_feed_event import ParlayFeedEvent
from app.services.settlement.settlement_service import SettlementService


@pytest.mark.asyncio
async def test_settle_legs_for_final_game(db):
    """Test settling legs for a FINAL game."""
    now = datetime.now(timezone.utc)
    
    # Create a FINAL game
    game = Game(
        external_game_id="test_settle_1",
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
    
    # Create a parlay
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
    
    # Create a pending leg for home team
    leg = ParlayLeg(
        parlay_id=parlay.id,
        game_id=game.id,
        market_type="h2h",
        selection="Home Team",
        status="PENDING",
    )
    db.add(leg)
    await db.commit()
    
    # Settle legs for the game
    service = SettlementService(db)
    settled_count = await service.settle_parlay_legs_for_game(game.id)
    
    assert settled_count == 1
    
    # Verify leg was updated
    await db.refresh(leg)
    assert leg.status == "WON"
    assert leg.settled_at is not None
    assert "final: 14-28" in leg.result_reason
    
    # Verify parlay status was updated
    await db.refresh(parlay)
    assert parlay.status == "WON"
    assert parlay.settled_at is not None


@pytest.mark.asyncio
async def test_settle_legs_game_not_final_returns_zero(db):
    """Test that non-FINAL game returns 0 settled legs."""
    now = datetime.now(timezone.utc)
    
    game = Game(
        external_game_id="test_settle_2",
        sport="NFL",
        home_team="Home Team",
        away_team="Away Team",
        start_time=now,
        status="LIVE",
        home_score=14,
        away_score=10,
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
    
    assert settled_count == 0
    
    # Verify leg was not updated
    await db.refresh(leg)
    assert leg.status == "PENDING"
    assert leg.settled_at is None


@pytest.mark.asyncio
async def test_settle_legs_missing_game_returns_zero(db):
    """Test that missing game returns 0 without crashing."""
    from uuid import uuid4
    
    service = SettlementService(db)
    settled_count = await service.settle_parlay_legs_for_game(uuid4())
    
    assert settled_count == 0


@pytest.mark.asyncio
async def test_settle_legs_null_scores_voids_legs(db):
    """Test that legs are VOIDed when game has null scores."""
    now = datetime.now(timezone.utc)
    
    game = Game(
        external_game_id="test_settle_3",
        sport="NFL",
        home_team="Home Team",
        away_team="Away Team",
        start_time=now - timedelta(hours=2),
        status="FINAL",
        home_score=None,
        away_score=None,
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
    
    assert settled_count == 1
    
    # Verify leg was VOIDed
    await db.refresh(leg)
    assert leg.status == "VOID"
    assert leg.settled_at is not None


@pytest.mark.asyncio
async def test_settle_legs_multiple_parlays_same_game(db):
    """Test settling legs for multiple parlays on the same game."""
    now = datetime.now(timezone.utc)
    
    game = Game(
        external_game_id="test_settle_4",
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
    
    # Create two parlays
    parlay1 = Parlay(
        user_id=None,
        legs=[],
        num_legs=1,
        parlay_hit_prob=Decimal("0.55"),
        risk_profile="balanced",
        status="PENDING",
    )
    parlay2 = Parlay(
        user_id=None,
        legs=[],
        num_legs=1,
        parlay_hit_prob=Decimal("0.45"),
        risk_profile="balanced",
        status="PENDING",
    )
    db.add_all([parlay1, parlay2])
    await db.flush()
    
    # Create legs for both parlays
    leg1 = ParlayLeg(
        parlay_id=parlay1.id,
        game_id=game.id,
        market_type="h2h",
        selection="Home Team",
        status="PENDING",
    )
    leg2 = ParlayLeg(
        parlay_id=parlay2.id,
        game_id=game.id,
        market_type="h2h",
        selection="Away Team",
        status="PENDING",
    )
    db.add_all([leg1, leg2])
    await db.commit()
    
    service = SettlementService(db)
    settled_count = await service.settle_parlay_legs_for_game(game.id)
    
    assert settled_count == 2
    
    # Verify both legs were updated
    await db.refresh(leg1)
    await db.refresh(leg2)
    assert leg1.status == "WON"
    assert leg2.status == "LOST"
    
    # Verify both parlays were updated
    await db.refresh(parlay1)
    await db.refresh(parlay2)
    assert parlay1.status == "WON"
    assert parlay2.status == "LOST"


@pytest.mark.asyncio
async def test_settle_legs_spread_and_totals(db):
    """Test settling spread and totals legs."""
    now = datetime.now(timezone.utc)
    
    game = Game(
        external_game_id="test_settle_5",
        sport="NFL",
        home_team="Home Team",
        away_team="Away Team",
        start_time=now - timedelta(hours=2),
        status="FINAL",
        home_score=28,
        away_score=14,  # Margin: +14, Total: 42
    )
    db.add(game)
    await db.flush()
    
    parlay = Parlay(
        user_id=None,
        legs=[],
        num_legs=2,
        parlay_hit_prob=Decimal("0.50"),
        risk_profile="balanced",
        status="PENDING",
    )
    db.add(parlay)
    await db.flush()
    
    # Create spread leg (home -3.5, covers)
    leg_spread = ParlayLeg(
        parlay_id=parlay.id,
        game_id=game.id,
        market_type="spreads",
        selection="Home Team",
        line=Decimal("-3.5"),
        status="PENDING",
    )
    # Create totals leg (over 40.5, wins)
    leg_total = ParlayLeg(
        parlay_id=parlay.id,
        game_id=game.id,
        market_type="totals",
        selection="over 40.5",
        line=Decimal("40.5"),
        status="PENDING",
    )
    db.add_all([leg_spread, leg_total])
    await db.commit()
    
    service = SettlementService(db)
    settled_count = await service.settle_parlay_legs_for_game(game.id)
    
    assert settled_count == 2
    
    # Verify both legs were updated correctly
    await db.refresh(leg_spread)
    await db.refresh(leg_total)
    assert leg_spread.status == "WON"
    assert leg_total.status == "WON"
    
    # Verify parlay status
    await db.refresh(parlay)
    assert parlay.status == "WON"


@pytest.mark.asyncio
async def test_settle_legs_creates_feed_events(db):
    """Test that feed events are created when legs are settled."""
    now = datetime.now(timezone.utc)
    
    game = Game(
        external_game_id="test_settle_6",
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
    await service.settle_parlay_legs_for_game(game.id)
    await db.commit()
    
    # Check for feed events
    result = await db.execute(
        select(ParlayFeedEvent).where(ParlayFeedEvent.event_type == "LEG_WON")
    )
    events = result.scalars().all()
    assert len(events) >= 1


@pytest.mark.asyncio
async def test_settle_all_pending_parlays_updates_status(db):
    """Test that settle_all_pending_parlays updates parlay statuses."""
    now = datetime.now(timezone.utc)
    
    # Create two games
    game1 = Game(
        external_game_id="test_settle_7a",
        sport="NFL",
        home_team="Home Team 1",
        away_team="Away Team 1",
        start_time=now - timedelta(hours=2),
        status="FINAL",
        home_score=28,
        away_score=14,
    )
    game2 = Game(
        external_game_id="test_settle_7b",
        sport="NFL",
        home_team="Home Team 2",
        away_team="Away Team 2",
        start_time=now - timedelta(hours=2),
        status="FINAL",
        home_score=21,
        away_score=17,
    )
    db.add_all([game1, game2])
    await db.flush()
    
    # Create parlay with two legs
    parlay = Parlay(
        user_id=None,
        legs=[],
        num_legs=2,
        parlay_hit_prob=Decimal("0.50"),
        risk_profile="balanced",
        status="PENDING",
    )
    db.add(parlay)
    await db.flush()
    
    # Create legs (both should win)
    leg1 = ParlayLeg(
        parlay_id=parlay.id,
        game_id=game1.id,
        market_type="h2h",
        selection="Home Team 1",
        status="WON",  # Already settled
    )
    leg2 = ParlayLeg(
        parlay_id=parlay.id,
        game_id=game2.id,
        market_type="h2h",
        selection="Home Team 2",
        status="WON",  # Already settled
    )
    db.add_all([leg1, leg2])
    await db.commit()
    
    service = SettlementService(db)
    stats = await service.settle_all_pending_parlays()
    await db.commit()
    
    # Verify parlay was settled
    assert stats.parlays_settled >= 1
    assert stats.parlays_won >= 1
    
    await db.refresh(parlay)
    assert parlay.status == "WON"
    assert parlay.settled_at is not None


@pytest.mark.asyncio
async def test_settle_all_pending_parlays_handles_lost_parlay(db):
    """Test that lost parlays are correctly identified."""
    now = datetime.now(timezone.utc)
    
    game = Game(
        external_game_id="test_settle_8",
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
    
    parlay = Parlay(
        user_id=None,
        legs=[],
        num_legs=2,
        parlay_hit_prob=Decimal("0.50"),
        risk_profile="balanced",
        status="PENDING",
    )
    db.add(parlay)
    await db.flush()
    
    # Create legs: one WON, one LOST
    leg1 = ParlayLeg(
        parlay_id=parlay.id,
        game_id=game.id,
        market_type="h2h",
        selection="Home Team",
        status="WON",
    )
    leg2 = ParlayLeg(
        parlay_id=parlay.id,
        game_id=game.id,
        market_type="h2h",
        selection="Away Team",
        status="LOST",
    )
    db.add_all([leg1, leg2])
    await db.commit()
    
    service = SettlementService(db)
    stats = await service.settle_all_pending_parlays()
    await db.commit()
    
    # Verify parlay was marked as LOST
    assert stats.parlays_settled >= 1
    assert stats.parlays_lost >= 1
    
    await db.refresh(parlay)
    assert parlay.status == "LOST"
    assert parlay.settled_at is not None


@pytest.mark.asyncio
async def test_settle_all_pending_parlays_saved_parlays(db):
    """Test that saved_parlays are also settled."""
    now = datetime.now(timezone.utc)
    
    from app.models.user import User
    
    # Create a user
    user = User(
        email="test@example.com",
        hashed_password="hashed",
    )
    db.add(user)
    await db.flush()
    
    game = Game(
        external_game_id="test_settle_9",
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
    
    # Create saved parlay
    saved_parlay = SavedParlay(
        user_id=user.id,
        parlay_type="custom",
        title="Test Parlay",
        legs=[],
        content_hash="test_hash",
        status="PENDING",
    )
    db.add(saved_parlay)
    await db.flush()
    
    # Create leg
    leg = ParlayLeg(
        saved_parlay_id=saved_parlay.id,
        game_id=game.id,
        market_type="h2h",
        selection="Home Team",
        status="WON",  # Already settled
    )
    db.add(leg)
    await db.commit()
    
    service = SettlementService(db)
    stats = await service.settle_all_pending_parlays()
    await db.commit()
    
    # Verify saved parlay was settled
    assert stats.parlays_settled >= 1
    
    await db.refresh(saved_parlay)
    assert saved_parlay.status == "WON"
    assert saved_parlay.settled_at is not None


@pytest.mark.asyncio
async def test_settle_legs_orphaned_leg_no_parlay_id(db):
    """Test that legs without parlay_id are still settled."""
    now = datetime.now(timezone.utc)
    
    game = Game(
        external_game_id="test_settle_10",
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
    
    # Create orphaned leg (no parlay_id or saved_parlay_id)
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
    
    # Should still settle the leg
    assert settled_count == 1
    
    await db.refresh(leg)
    assert leg.status == "WON"
    assert leg.settled_at is not None


@pytest.mark.asyncio
async def test_settle_legs_error_handling_continues_on_failure(db):
    """Test that errors in one leg don't stop settlement of others."""
    now = datetime.now(timezone.utc)
    
    game = Game(
        external_game_id="test_settle_11",
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
    
    parlay = Parlay(
        user_id=None,
        legs=[],
        num_legs=2,
        parlay_hit_prob=Decimal("0.50"),
        risk_profile="balanced",
        status="PENDING",
    )
    db.add(parlay)
    await db.flush()
    
    # Create two legs
    leg1 = ParlayLeg(
        parlay_id=parlay.id,
        game_id=game.id,
        market_type="h2h",
        selection="Home Team",
        status="PENDING",
    )
    leg2 = ParlayLeg(
        parlay_id=parlay.id,
        game_id=game.id,
        market_type="invalid_type",  # This will cause an error
        selection="Home Team",
        status="PENDING",
    )
    db.add_all([leg1, leg2])
    await db.commit()
    
    service = SettlementService(db)
    settled_count = await service.settle_parlay_legs_for_game(game.id)
    await db.commit()
    
    # Should settle at least one leg (the valid one)
    assert settled_count >= 1
    
    # Verify valid leg was settled
    await db.refresh(leg1)
    assert leg1.status == "WON"
    
    # Invalid leg should be VOIDed
    await db.refresh(leg2)
    assert leg2.status == "VOID"
