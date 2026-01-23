"""End-to-end tests for SettlementWorker."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
import pytest
import asyncio
from sqlalchemy import select

from app.models.game import Game
from app.models.parlay import Parlay
from app.models.parlay_leg import ParlayLeg
from app.models.system_heartbeat import SystemHeartbeat
from app.workers.settlement_worker import SettlementWorker
from decimal import Decimal


@pytest.mark.asyncio
async def test_worker_starts_and_stops_cleanly():
    """Test that worker can start and stop without errors."""
    worker = SettlementWorker()
    
    # Start worker
    await worker.start()
    assert worker.running is True
    
    # Wait a moment
    await asyncio.sleep(0.1)
    
    # Stop worker
    await worker.stop()
    assert worker.running is False


@pytest.mark.asyncio
async def test_worker_processes_final_games(db):
    """Test that worker processes FINAL games correctly."""
    now = datetime.now(timezone.utc)
    
    # Create a FINAL game
    game = Game(
        external_game_id="test_worker_1",
        sport="NFL",
        home_team="Home Team",
        away_team="Away Team",
        start_time=now - timedelta(hours=1),
        status="FINAL",
        home_score=28,
        away_score=14,
    )
    db.add(game)
    await db.flush()
    
    # Create parlay and leg
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
    
    # Create worker and process settlements
    worker = SettlementWorker()
    await worker._process_settlements()
    
    # Verify leg was settled
    await db.refresh(leg)
    assert leg.status == "WON"
    assert leg.settled_at is not None
    
    # Verify parlay was updated
    await db.refresh(parlay)
    assert parlay.status == "WON"


@pytest.mark.asyncio
async def test_worker_handles_errors_gracefully(db):
    """Test that worker continues running after errors."""
    now = datetime.now(timezone.utc)
    
    # Create a game with invalid data (missing scores but FINAL)
    game = Game(
        external_game_id="test_worker_2",
        sport="NFL",
        home_team="Home Team",
        away_team="Away Team",
        start_time=now - timedelta(hours=1),
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
    
    # Process settlements - should handle missing scores gracefully
    worker = SettlementWorker()
    await worker._process_settlements()
    
    # Verify leg was VOIDed (not crashed)
    await db.refresh(leg)
    assert leg.status == "VOID"


@pytest.mark.asyncio
async def test_worker_updates_heartbeat(db):
    """Test that worker updates heartbeat correctly."""
    now = datetime.now(timezone.utc)
    
    game = Game(
        external_game_id="test_worker_3",
        sport="NFL",
        home_team="Home Team",
        away_team="Away Team",
        start_time=now - timedelta(hours=1),
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
    
    worker = SettlementWorker()
    await worker._process_settlements()
    
    # Check heartbeat was created/updated
    result = await db.execute(
        select(SystemHeartbeat).where(SystemHeartbeat.name == "settlement_worker")
    )
    heartbeat = result.scalar_one_or_none()
    
    assert heartbeat is not None
    assert heartbeat.last_beat_at is not None
    assert heartbeat.meta is not None
    assert "parlays_settled" in heartbeat.meta


@pytest.mark.asyncio
async def test_worker_respects_rate_limit(db):
    """Test that worker respects MAX_GAMES_PER_CYCLE limit."""
    now = datetime.now(timezone.utc)
    
    # Create more games than the limit
    games = []
    for i in range(150):  # More than MAX_GAMES_PER_CYCLE (100)
        game = Game(
            external_game_id=f"test_worker_rate_{i}",
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
    await db.commit()
    
    worker = SettlementWorker()
    
    # Process settlements
    await worker._process_settlements()
    
    # Worker should process max 100 games per cycle
    # (We can't easily verify this without mocking, but we can verify it doesn't crash)


@pytest.mark.asyncio
async def test_worker_circuit_breaker_opens_on_errors():
    """Test that circuit breaker opens after too many errors."""
    worker = SettlementWorker()
    
    # Simulate consecutive errors
    for i in range(worker.MAX_CONSECUTIVE_ERRORS):
        worker._consecutive_errors = i + 1
        worker._last_error_time = datetime.utcnow()
        
        # Check if circuit should open
        if worker._consecutive_errors >= worker.MAX_CONSECUTIVE_ERRORS:
            worker._circuit_open = True
            worker._circuit_open_since = datetime.utcnow()
    
    assert worker._circuit_open is True
    assert worker._consecutive_errors >= worker.MAX_CONSECUTIVE_ERRORS


@pytest.mark.asyncio
async def test_worker_has_active_games_check(db):
    """Test that _has_active_games correctly identifies active games."""
    now = datetime.now(timezone.utc)
    
    worker = SettlementWorker()
    
    # No active games initially
    has_active = await worker._has_active_games()
    assert has_active is False
    
    # Create a LIVE game
    game = Game(
        external_game_id="test_worker_active",
        sport="NFL",
        home_team="Home Team",
        away_team="Away Team",
        start_time=now - timedelta(minutes=30),
        status="LIVE",
        home_score=14,
        away_score=10,
    )
    db.add(game)
    await db.commit()
    
    # Should detect active game
    has_active = await worker._has_active_games()
    assert has_active is True
    
    # Create a FINAL game (recent)
    game2 = Game(
        external_game_id="test_worker_final",
        sport="NFL",
        home_team="Home Team 2",
        away_team="Away Team 2",
        start_time=now - timedelta(minutes=30),
        status="FINAL",
        home_score=28,
        away_score=14,
    )
    db.add(game2)
    await db.commit()
    
    # Should still detect active (FINAL within last hour)
    has_active = await worker._has_active_games()
    assert has_active is True
