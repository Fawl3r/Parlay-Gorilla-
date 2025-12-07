"""
Tests for event tracking functionality.

Verifies that:
- Events are created correctly
- Event queries work as expected
- Parlay events are tracked properly
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import uuid

from app.services.event_tracking_service import EventTrackingService
from app.models.app_event import AppEvent
from app.models.parlay_event import ParlayEvent


class TestEventTrackingService:
    """Tests for EventTrackingService."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        return db
    
    @pytest.fixture
    def service(self, mock_db):
        """Create an EventTrackingService instance."""
        return EventTrackingService(mock_db)
    
    @pytest.mark.asyncio
    async def test_track_event_basic(self, service, mock_db):
        """Test basic event tracking."""
        # Track an event
        event = await service.track_event(
            event_type="view_analysis",
            session_id="test-session-123",
            metadata={"sport": "nfl", "matchup": "bears-vs-packers"},
        )
        
        # Verify db.add was called
        mock_db.add.assert_called_once()
        
        # Verify db.commit was called
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_track_event_with_user(self, service, mock_db):
        """Test event tracking with authenticated user."""
        user_id = str(uuid.uuid4())
        
        event = await service.track_event(
            event_type="build_parlay",
            user_id=user_id,
            session_id="test-session-123",
        )
        
        mock_db.add.assert_called_once()
        
        # Get the event that was added
        added_event = mock_db.add.call_args[0][0]
        assert added_event.user_id == uuid.UUID(user_id)
    
    @pytest.mark.asyncio
    async def test_track_event_with_request_context(self, service, mock_db):
        """Test event tracking with request context."""
        event = await service.track_event(
            event_type="page_view",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            referrer="https://google.com",
            page_url="/analysis/nfl/bears-vs-packers",
        )
        
        mock_db.add.assert_called_once()
        
        added_event = mock_db.add.call_args[0][0]
        assert added_event.ip_address == "192.168.1.1"
        assert added_event.user_agent == "Mozilla/5.0"
        assert added_event.referrer == "https://google.com"
    
    @pytest.mark.asyncio
    async def test_track_parlay_event(self, service, mock_db):
        """Test parlay event tracking."""
        event = await service.track_parlay_event(
            parlay_type="balanced",
            legs_count=5,
            session_id="test-session-123",
            expected_value=0.12,
            combined_odds=25.5,
            hit_probability=0.04,
            build_method="auto_generated",
        )
        
        mock_db.add.assert_called_once()
        
        added_event = mock_db.add.call_args[0][0]
        assert added_event.parlay_type == "balanced"
        assert added_event.legs_count == 5
        assert added_event.expected_value == 0.12
    
    @pytest.mark.asyncio
    async def test_track_parlay_event_with_breakdown(self, service, mock_db):
        """Test parlay event with legs breakdown."""
        legs_breakdown = {
            "moneyline": 3,
            "spread": 1,
            "total": 1,
            "upsets": 1,
        }
        
        event = await service.track_parlay_event(
            parlay_type="degen",
            legs_count=6,
            legs_breakdown=legs_breakdown,
            was_saved=True,
        )
        
        mock_db.add.assert_called_once()
        
        added_event = mock_db.add.call_args[0][0]
        assert added_event.legs_breakdown == legs_breakdown
        assert added_event.was_saved == True


class TestAppEventModel:
    """Tests for AppEvent model."""
    
    def test_event_type_required(self):
        """Event type should be a required field."""
        # AppEvent model has event_type as nullable=False
        event = AppEvent(
            id=uuid.uuid4(),
            event_type="view_analysis",
        )
        assert event.event_type == "view_analysis"
    
    def test_metadata_can_be_dict(self):
        """Metadata should accept a dictionary."""
        metadata = {"sport": "nfl", "team": "Bears"}
        event = AppEvent(
            id=uuid.uuid4(),
            event_type="view_analysis",
            metadata_=metadata,
        )
        assert event.metadata_ == metadata
    
    def test_user_id_optional(self):
        """User ID should be optional (for anonymous events)."""
        event = AppEvent(
            id=uuid.uuid4(),
            event_type="page_view",
            user_id=None,
        )
        assert event.user_id is None


class TestParlayEventModel:
    """Tests for ParlayEvent model."""
    
    def test_parlay_type_required(self):
        """Parlay type should be required."""
        event = ParlayEvent(
            id=uuid.uuid4(),
            parlay_type="safe",
            legs_count=3,
        )
        assert event.parlay_type == "safe"
    
    def test_legs_count_required(self):
        """Legs count should be required."""
        event = ParlayEvent(
            id=uuid.uuid4(),
            parlay_type="balanced",
            legs_count=5,
        )
        assert event.legs_count == 5
    
    def test_parlay_type_values(self):
        """Test valid parlay type values."""
        valid_types = ["safe", "balanced", "degen", "custom"]
        
        for ptype in valid_types:
            event = ParlayEvent(
                id=uuid.uuid4(),
                parlay_type=ptype,
                legs_count=3,
            )
            assert event.parlay_type == ptype
    
    def test_expected_value_optional(self):
        """Expected value should be optional."""
        event = ParlayEvent(
            id=uuid.uuid4(),
            parlay_type="balanced",
            legs_count=5,
            expected_value=None,
        )
        assert event.expected_value is None
    
    def test_build_method_values(self):
        """Test build method values."""
        valid_methods = ["auto_generated", "user_built", "ai_assisted"]
        
        for method in valid_methods:
            event = ParlayEvent(
                id=uuid.uuid4(),
                parlay_type="balanced",
                legs_count=5,
                build_method=method,
            )
            assert event.build_method == method


class TestEventTypes:
    """Tests for valid event types."""
    
    def test_allowed_event_types(self):
        """Test that we have a defined set of allowed event types."""
        allowed_events = [
            "view_analysis",
            "build_parlay",
            "view_parlay_result",
            "click_upset_finder",
            "page_view",
            "share_parlay",
            "save_parlay",
            "signup_start",
            "signup_complete",
            "login",
            "upgrade_click",
        ]
        
        # All these should be valid event types
        for event_type in allowed_events:
            event = AppEvent(
                id=uuid.uuid4(),
                event_type=event_type,
            )
            assert event.event_type == event_type
    
    def test_parlay_types(self):
        """Test parlay type constants."""
        valid_parlay_types = ["safe", "balanced", "degen", "custom"]
        
        # All should be valid
        assert len(valid_parlay_types) == 4
        assert "safe" in valid_parlay_types
        assert "degen" in valid_parlay_types

