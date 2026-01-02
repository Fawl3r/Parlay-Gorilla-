"""Test candidate leg date range resolution for multi-day coverage"""

import pytest
import sys
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

# Import only what we need without triggering full app initialization
sys.path.insert(0, '.')

# Mock the NFL week utilities before importing
with patch('app.utils.nfl_week.get_current_nfl_week', return_value=1), \
     patch('app.utils.nfl_week.get_week_date_range', 
           side_effect=lambda week, season_year=None: (
               datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
               datetime(2024, 1, 8, 0, 0, 0, tzinfo=timezone.utc)
           )):
    from app.services.probability_engine_impl.candidate_leg_service import CandidateLegService


class TestCandidateLegDateRange:
    """Test that date ranges include multiple days for all sports"""

    def test_nfl_with_week_returns_full_week_range(self):
        """NFL with week specified should return full 7-day week range"""
        cutoff, future = CandidateLegService._resolve_date_range("NFL", week=1)
        
        # Should be approximately 7 days
        span_days = (future - cutoff).total_seconds() / 86400
        assert span_days >= 6.5, f"Expected ~7 days, got {span_days:.1f} days"
        assert span_days <= 7.5, f"Expected ~7 days, got {span_days:.1f} days"
        
        # Both should be timezone-aware
        assert cutoff.tzinfo is not None, "cutoff_time should be timezone-aware"
        assert future.tzinfo is not None, "future_cutoff should be timezone-aware"

    def test_nfl_without_week_returns_current_week_range(self):
        """NFL without week should return current week range (7 days)"""
        cutoff, future = CandidateLegService._resolve_date_range("NFL", week=None)
        
        # Should be approximately 7 days (full week)
        span_days = (future - cutoff).total_seconds() / 86400
        assert span_days >= 6.5, f"Expected ~7 days for NFL week, got {span_days:.1f} days"
        
        # Both should be timezone-aware
        assert cutoff.tzinfo is not None
        assert future.tzinfo is not None

    def test_nba_returns_multi_day_range(self):
        """NBA should return multi-day range (1 day back, 7 days forward = 8 days total)"""
        cutoff, future = CandidateLegService._resolve_date_range("NBA", week=None)
        
        # Should be approximately 8 days (1 back + 7 forward)
        span_days = (future - cutoff).total_seconds() / 86400
        assert span_days >= 7.5, f"Expected ~8 days for NBA, got {span_days:.1f} days"
        assert span_days <= 8.5, f"Expected ~8 days for NBA, got {span_days:.1f} days"
        
        # Both should be timezone-aware
        assert cutoff.tzinfo is not None
        assert future.tzinfo is not None
        
        # Should include games from yesterday through next week
        now = datetime.now(timezone.utc)
        assert cutoff <= now - timedelta(days=1) + timedelta(hours=1), "Should look back ~1 day"
        assert future >= now + timedelta(days=7) - timedelta(hours=1), "Should look forward ~7 days"

    def test_nhl_returns_multi_day_range(self):
        """NHL should return multi-day range"""
        cutoff, future = CandidateLegService._resolve_date_range("NHL", week=None)
        
        span_days = (future - cutoff).total_seconds() / 86400
        assert span_days >= 7.5, f"Expected ~8 days for NHL, got {span_days:.1f} days"
        assert cutoff.tzinfo is not None
        assert future.tzinfo is not None

    def test_mlb_returns_multi_day_range(self):
        """MLB should return multi-day range"""
        cutoff, future = CandidateLegService._resolve_date_range("MLB", week=None)
        
        span_days = (future - cutoff).total_seconds() / 86400
        assert span_days >= 7.5, f"Expected ~8 days for MLB, got {span_days:.1f} days"
        assert cutoff.tzinfo is not None
        assert future.tzinfo is not None

    def test_all_sports_use_timezone_aware_datetimes(self):
        """All sports should return timezone-aware datetimes"""
        sports = ["NFL", "NBA", "NHL", "MLB", "NCAAF", "NCAAB"]
        
        for sport in sports:
            cutoff, future = CandidateLegService._resolve_date_range(sport, week=None)
            assert cutoff.tzinfo is not None, f"{sport} cutoff_time should be timezone-aware"
            assert future.tzinfo is not None, f"{sport} future_cutoff should be timezone-aware"
            assert cutoff.tzinfo == timezone.utc, f"{sport} should use UTC timezone"
            assert future.tzinfo == timezone.utc, f"{sport} should use UTC timezone"

    def test_non_nfl_sports_include_multiple_days(self):
        """Non-NFL sports should include games from multiple days, not just today"""
        sports = ["NBA", "NHL", "MLB"]
        now = datetime.now(timezone.utc)
        
        for sport in sports:
            cutoff, future = CandidateLegService._resolve_date_range(sport, week=None)
            
            # Should look back at least 1 day
            days_back = (now - cutoff).total_seconds() / 86400
            assert days_back >= 0.5, f"{sport} should look back at least ~1 day, got {days_back:.1f} days"
            
            # Should look forward at least 7 days
            days_forward = (future - now).total_seconds() / 86400
            assert days_forward >= 6.5, f"{sport} should look forward at least ~7 days, got {days_forward:.1f} days"
            
            # Total span should be ~8 days
            span_days = (future - cutoff).total_seconds() / 86400
            assert span_days >= 7.5, f"{sport} should span ~8 days total, got {span_days:.1f} days"

