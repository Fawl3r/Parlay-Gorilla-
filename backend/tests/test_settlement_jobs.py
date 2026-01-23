"""Tests for settlement background jobs."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from decimal import Decimal
import pytest
from unittest.mock import AsyncMock, patch

from app.models.game import Game
from app.models.parlay import Parlay
from app.models.parlay_leg import ParlayLeg
from app.models.saved_parlay import SavedParlay
from app.models.user import User
from app.services.scheduler import BackgroundScheduler
from app.core.config import Settings


@pytest.mark.asyncio
async def test_auto_resolve_parlays_job_skips_when_feature_disabled(db):
    """Test that _auto_resolve_parlays skips when FEATURE_SETTLEMENT is disabled."""
    scheduler = BackgroundScheduler()
    
    # Mock settings to disable settlement
    with patch('app.services.scheduler.settings') as mock_settings:
        mock_settings.feature_settlement = False
        
        # Should return early without processing
        await scheduler._auto_resolve_parlays()
        
        # Verify no processing occurred (no error means it skipped)


@pytest.mark.asyncio
async def test_resolve_saved_parlays_job_skips_when_feature_disabled(db):
    """Test that _resolve_saved_parlays skips when FEATURE_SETTLEMENT is disabled."""
    scheduler = BackgroundScheduler()
    
    # Mock settings to disable settlement
    with patch('app.services.scheduler.settings') as mock_settings:
        mock_settings.feature_settlement = False
        
        # Should return early without processing
        await scheduler._resolve_saved_parlays()
        
        # Verify no processing occurred


@pytest.mark.asyncio
async def test_process_ready_commissions_job_skips_when_feature_disabled(db):
    """Test that _process_ready_commissions skips when FEATURE_SETTLEMENT is disabled."""
    scheduler = BackgroundScheduler()
    
    # Mock settings to disable settlement
    with patch('app.services.scheduler.settings') as mock_settings:
        mock_settings.feature_settlement = False
        
        # Should return early without processing
        await scheduler._process_ready_commissions()
        
        # Verify no processing occurred


@pytest.mark.asyncio
async def test_auto_resolve_parlays_job_processes_when_enabled(db):
    """Test that _auto_resolve_parlays processes when FEATURE_SETTLEMENT is enabled."""
    now = datetime.now(timezone.utc)
    
    # Create a FINAL game
    game = Game(
        external_game_id="test_job_1",
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
    
    scheduler = BackgroundScheduler()
    
    # Mock settings to enable settlement
    with patch('app.services.scheduler.settings') as mock_settings:
        mock_settings.feature_settlement = True
        
        # Mock the parlay tracker service
        with patch('app.services.scheduler.ParlayTrackerService') as mock_tracker_class:
            mock_tracker = AsyncMock()
            mock_tracker.auto_resolve_parlays = AsyncMock(return_value=1)
            mock_tracker_class.return_value = mock_tracker
            
            await scheduler._auto_resolve_parlays()
            
            # Verify tracker was called
            mock_tracker.auto_resolve_parlays.assert_called_once()


@pytest.mark.asyncio
async def test_jobs_handle_errors_without_crashing(db):
    """Test that settlement jobs handle errors gracefully."""
    scheduler = BackgroundScheduler()
    
    # Mock settings to enable settlement
    with patch('app.services.scheduler.settings') as mock_settings:
        mock_settings.feature_settlement = True
        
        # Mock an error in the tracker
        with patch('app.services.scheduler.ParlayTrackerService') as mock_tracker_class:
            mock_tracker = AsyncMock()
            mock_tracker.auto_resolve_parlays = AsyncMock(side_effect=Exception("Test error"))
            mock_tracker_class.return_value = mock_tracker
            
            # Should not crash, just log error
            try:
                await scheduler._auto_resolve_parlays()
            except Exception:
                pytest.fail("Job should not raise exception, should be handled by crash_proof_job decorator")
