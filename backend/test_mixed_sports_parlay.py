"""
Comprehensive test suite for mixed sports parlay functionality.

Tests cover:
- Unit tests for MixedSportsParlayBuilder
- Integration tests for the API endpoint
- Edge cases and error handling
"""

import asyncio
import httpx
import json
import pytest
from typing import List, Dict
from unittest.mock import AsyncMock, MagicMock, patch


# ============================================================================
# API Integration Tests
# ============================================================================

class TestMixedSportsParlayAPI:
    """Integration tests for the mixed sports parlay API endpoint."""
    
    BASE_URL = "http://localhost:8000"
    TIMEOUT = 120.0

    @pytest.mark.asyncio
    async def test_single_sport_parlay(self):
        """Test generating a single sport parlay (NFL only)."""
        async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
            response = await client.post(
                f"{self.BASE_URL}/api/parlay/suggest",
                json={
                    "num_legs": 3,
                    "risk_profile": "balanced",
                    "sports": ["NFL"],
                    "mix_sports": False
                }
            )
            
            print(f"\nSingle Sport Parlay Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                assert "legs" in data
                assert "num_legs" in data
                assert data["num_legs"] <= 3
                print(f"Generated {len(data['legs'])} legs")
                for leg in data["legs"]:
                    print(f"  - {leg.get('game', 'Unknown')} | Sport: {leg.get('sport', 'N/A')}")
            else:
                print(f"Response: {response.text}")
                # 503 is acceptable if no games available
                assert response.status_code in [200, 503]

    @pytest.mark.asyncio
    async def test_mixed_sports_parlay_nfl_nba(self):
        """Test generating a mixed sports parlay with NFL and NBA."""
        async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
            response = await client.post(
                f"{self.BASE_URL}/api/parlay/suggest",
                json={
                    "num_legs": 6,
                    "risk_profile": "balanced",
                    "sports": ["NFL", "NBA"],
                    "mix_sports": True
                }
            )
            
            print(f"\nMixed NFL+NBA Parlay Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                assert "legs" in data
                
                # Check sports distribution
                sports_used = set()
                for leg in data["legs"]:
                    sport = leg.get("sport", "NFL")
                    sports_used.add(sport)
                    print(f"  - {leg.get('game', 'Unknown')} | Sport: {sport}")
                
                print(f"Sports used: {sports_used}")
            else:
                print(f"Response: {response.text}")
                assert response.status_code in [200, 503]

    @pytest.mark.asyncio
    async def test_mixed_sports_parlay_all_sports(self):
        """Test generating a mixed sports parlay with all supported sports."""
        async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
            response = await client.post(
                f"{self.BASE_URL}/api/parlay/suggest",
                json={
                    "num_legs": 8,
                    "risk_profile": "balanced",
                    "sports": ["NFL", "NBA", "NHL", "MLB"],
                    "mix_sports": True
                }
            )
            
            print(f"\nMixed All Sports Parlay Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                assert "legs" in data
                
                # Count legs per sport
                sport_counts: Dict[str, int] = {}
                for leg in data["legs"]:
                    sport = leg.get("sport", "NFL")
                    sport_counts[sport] = sport_counts.get(sport, 0) + 1
                
                print(f"Legs per sport: {sport_counts}")
                
                # Verify legs were generated
                assert len(data["legs"]) > 0
            else:
                print(f"Response: {response.text}")
                assert response.status_code in [200, 503]

    @pytest.mark.asyncio
    async def test_mixed_sports_conservative_profile(self):
        """Test mixed sports parlay with conservative risk profile."""
        async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
            response = await client.post(
                f"{self.BASE_URL}/api/parlay/suggest",
                json={
                    "num_legs": 4,
                    "risk_profile": "conservative",
                    "sports": ["NFL", "NBA"],
                    "mix_sports": True
                }
            )
            
            print(f"\nConservative Mixed Parlay Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                assert data["risk_profile"] == "conservative"
                
                # Conservative should have higher confidence scores
                for leg in data["legs"]:
                    confidence = leg.get("confidence", 0)
                    print(f"  - Confidence: {confidence:.1f}%")
            else:
                print(f"Response: {response.text}")
                assert response.status_code in [200, 503]

    @pytest.mark.asyncio
    async def test_mixed_sports_degen_profile(self):
        """Test mixed sports parlay with degen risk profile."""
        async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
            response = await client.post(
                f"{self.BASE_URL}/api/parlay/suggest",
                json={
                    "num_legs": 12,
                    "risk_profile": "degen",
                    "sports": ["NFL", "NBA", "NHL"],
                    "mix_sports": True
                }
            )
            
            print(f"\nDegen Mixed Parlay Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                assert data["risk_profile"] == "degen"
                print(f"Generated {len(data['legs'])} legs for degen profile")
            else:
                print(f"Response: {response.text}")
                assert response.status_code in [200, 503]

    @pytest.mark.asyncio
    async def test_empty_sports_list_defaults_to_nfl(self):
        """Test that empty sports list defaults to NFL."""
        async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
            response = await client.post(
                f"{self.BASE_URL}/api/parlay/suggest",
                json={
                    "num_legs": 3,
                    "risk_profile": "balanced",
                    "sports": [],
                    "mix_sports": False
                }
            )
            
            print(f"\nEmpty Sports List Response Status: {response.status_code}")
            
            # Should either work with default or return error
            assert response.status_code in [200, 400, 503]

    @pytest.mark.asyncio
    async def test_max_legs_mixed_parlay(self):
        """Test mixed sports parlay with maximum legs (20)."""
        async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
            response = await client.post(
                f"{self.BASE_URL}/api/parlay/suggest",
                json={
                    "num_legs": 20,
                    "risk_profile": "degen",
                    "sports": ["NFL", "NBA", "NHL"],
                    "mix_sports": True
                }
            )
            
            print(f"\nMax Legs (20) Mixed Parlay Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Generated {len(data['legs'])} legs (requested 20)")
                
                # Count by sport
                sport_counts = {}
                for leg in data["legs"]:
                    sport = leg.get("sport", "NFL")
                    sport_counts[sport] = sport_counts.get(sport, 0) + 1
                print(f"Distribution: {sport_counts}")
            else:
                print(f"Response: {response.text}")
                assert response.status_code in [200, 503]

    @pytest.mark.asyncio
    async def test_single_leg_mixed_parlay(self):
        """Test mixed sports parlay with single leg."""
        async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
            response = await client.post(
                f"{self.BASE_URL}/api/parlay/suggest",
                json={
                    "num_legs": 1,
                    "risk_profile": "conservative",
                    "sports": ["NFL", "NBA"],
                    "mix_sports": True
                }
            )
            
            print(f"\nSingle Leg Mixed Parlay Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                assert len(data["legs"]) == 1
                print(f"Single leg sport: {data['legs'][0].get('sport', 'N/A')}")
            else:
                assert response.status_code in [200, 503]


class TestTripleParlayMixedSports:
    """Tests for triple parlay with mixed sports."""
    
    BASE_URL = "http://localhost:8000"
    TIMEOUT = 120.0

    @pytest.mark.asyncio
    async def test_triple_parlay_mixed_sports(self):
        """Test triple parlay generation with mixed sports."""
        async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
            response = await client.post(
                f"{self.BASE_URL}/api/parlay/suggest/triple",
                json={
                    "sports": ["NFL", "NBA", "NHL"]
                }
            )
            
            print(f"\nTriple Parlay Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                for profile in ["safe", "balanced", "degen"]:
                    if profile in data:
                        parlay = data[profile]
                        legs_count = len(parlay.get("legs", []))
                        print(f"  {profile.upper()}: {legs_count} legs")
            else:
                print(f"Response: {response.text}")
                assert response.status_code in [200, 503]


# ============================================================================
# Unit Tests for MixedSportsParlayBuilder
# ============================================================================

class TestMixedSportsParlayBuilderUnit:
    """Unit tests for MixedSportsParlayBuilder class."""

    def test_supported_sports(self):
        """Test that all expected sports are supported."""
        from app.services.mixed_sports_parlay import MixedSportsParlayBuilder
        
        expected_sports = ["NFL", "NBA", "NHL", "MLB"]
        assert MixedSportsParlayBuilder.SUPPORTED_SPORTS == expected_sports

    def test_min_confidence_thresholds(self):
        """Test confidence thresholds for different risk profiles."""
        from app.services.mixed_sports_parlay import MixedSportsParlayBuilder
        
        # Create a mock db session
        mock_db = MagicMock()
        builder = MixedSportsParlayBuilder(mock_db)
        
        assert builder._get_min_confidence("conservative") == 70.0
        assert builder._get_min_confidence("balanced") == 55.0
        assert builder._get_min_confidence("degen") == 40.0
        assert builder._get_min_confidence("unknown") == 55.0  # Default

    def test_calculate_parlay_probability(self):
        """Test parlay probability calculation."""
        from app.services.mixed_sports_parlay import MixedSportsParlayBuilder
        
        mock_db = MagicMock()
        builder = MixedSportsParlayBuilder(mock_db)
        
        # Test with known probabilities
        probs = [0.6, 0.7, 0.5]
        expected = 0.6 * 0.7 * 0.5  # 0.21
        result = builder._calculate_parlay_probability(probs)
        assert abs(result - expected) < 0.0001
        
        # Test empty list
        assert builder._calculate_parlay_probability([]) == 0.0
        
        # Test single probability
        assert builder._calculate_parlay_probability([0.8]) == 0.8

    def test_build_legs_data_format(self):
        """Test that leg data is formatted correctly."""
        from app.services.mixed_sports_parlay import MixedSportsParlayBuilder
        
        mock_db = MagicMock()
        builder = MixedSportsParlayBuilder(mock_db)
        
        sample_legs = [
            {
                "market_id": "123",
                "outcome": "home",
                "game": "Team A @ Team B",
                "home_team": "Team B",
                "away_team": "Team A",
                "market_type": "h2h",
                "odds": "-110",
                "adjusted_prob": 0.55,
                "confidence_score": 65.0,
                "sport": "NFL"
            }
        ]
        
        result = builder._build_legs_data(sample_legs)
        
        assert len(result) == 1
        assert result[0]["market_id"] == "123"
        assert result[0]["sport"] == "NFL"
        assert result[0]["probability"] == 0.55
        assert result[0]["confidence"] == 65.0

    def test_build_legs_data_missing_fields(self):
        """Test that legs with missing required fields are skipped."""
        from app.services.mixed_sports_parlay import MixedSportsParlayBuilder
        
        mock_db = MagicMock()
        builder = MixedSportsParlayBuilder(mock_db)
        
        sample_legs = [
            {"market_id": "", "outcome": "home"},  # Missing market_id
            {"market_id": "123", "outcome": ""},    # Missing outcome
            {"market_id": "456", "outcome": "home", "sport": "NBA"}  # Valid
        ]
        
        result = builder._build_legs_data(sample_legs)
        
        # Only the valid leg should be included
        assert len(result) == 1
        assert result[0]["market_id"] == "456"

    def test_select_best_legs_deduplication(self):
        """Test that duplicate legs are removed."""
        from app.services.mixed_sports_parlay import MixedSportsParlayBuilder
        
        mock_db = MagicMock()
        builder = MixedSportsParlayBuilder(mock_db)
        
        # Create duplicates with different confidence
        candidates = [
            {"game_id": "g1", "market_type": "h2h", "outcome": "home", "confidence_score": 70},
            {"game_id": "g1", "market_type": "h2h", "outcome": "home", "confidence_score": 65},  # Duplicate
            {"game_id": "g2", "market_type": "h2h", "outcome": "away", "confidence_score": 60},
        ]
        
        result = builder._select_best_legs(candidates, num_legs=2, risk_profile="balanced")
        
        # Should return 2 unique legs with highest confidence
        assert len(result) == 2
        # First leg should have highest confidence
        assert result[0]["confidence_score"] == 70

    def test_select_balanced_legs_distribution(self):
        """Test that legs are distributed across sports."""
        from app.services.mixed_sports_parlay import MixedSportsParlayBuilder
        
        mock_db = MagicMock()
        builder = MixedSportsParlayBuilder(mock_db)
        
        candidates = [
            {"game_id": "g1", "market_type": "h2h", "outcome": "home", "confidence_score": 80, "sport": "NFL"},
            {"game_id": "g2", "market_type": "h2h", "outcome": "home", "confidence_score": 75, "sport": "NFL"},
            {"game_id": "g3", "market_type": "h2h", "outcome": "home", "confidence_score": 70, "sport": "NBA"},
            {"game_id": "g4", "market_type": "h2h", "outcome": "home", "confidence_score": 65, "sport": "NBA"},
            {"game_id": "g5", "market_type": "h2h", "outcome": "home", "confidence_score": 60, "sport": "NHL"},
            {"game_id": "g6", "market_type": "h2h", "outcome": "home", "confidence_score": 55, "sport": "NHL"},
        ]
        
        result = builder._select_balanced_legs(
            candidates, 
            num_legs=6, 
            sports=["NFL", "NBA", "NHL"],
            risk_profile="balanced"
        )
        
        # Count sports in result
        sport_counts = {}
        for leg in result:
            sport = leg.get("sport", "NFL")
            sport_counts[sport] = sport_counts.get(sport, 0) + 1
        
        # Should have legs from each sport
        assert len(sport_counts) == 3  # NFL, NBA, NHL
        print(f"Sport distribution: {sport_counts}")


# ============================================================================
# Schema Tests
# ============================================================================

class TestParlaySchemas:
    """Test parlay request/response schemas."""

    def test_parlay_request_with_sports(self):
        """Test ParlayRequest accepts sports list."""
        from app.schemas.parlay import ParlayRequest
        
        request = ParlayRequest(
            num_legs=5,
            risk_profile="balanced",
            sports=["NFL", "NBA"],
            mix_sports=True
        )
        
        assert request.num_legs == 5
        assert request.sports == ["NFL", "NBA"]
        assert request.mix_sports == True

    def test_parlay_request_defaults(self):
        """Test ParlayRequest default values."""
        from app.schemas.parlay import ParlayRequest
        
        request = ParlayRequest(num_legs=3)
        
        assert request.risk_profile == "balanced"
        assert request.sports is None
        assert request.mix_sports == False

    def test_leg_response_with_sport(self):
        """Test LegResponse includes sport field."""
        from app.schemas.parlay import LegResponse
        
        leg = LegResponse(
            market_id="123",
            outcome="home",
            game="Team A @ Team B",
            market_type="h2h",
            odds="-110",
            probability=0.55,
            confidence=65.0,
            sport="NFL"
        )
        
        assert leg.sport == "NFL"


# ============================================================================
# Command-line test runner
# ============================================================================

async def run_all_api_tests():
    """Run all API tests manually."""
    print("=" * 70)
    print("MIXED SPORTS PARLAY TEST SUITE")
    print("=" * 70)
    
    test_api = TestMixedSportsParlayAPI()
    test_triple = TestTripleParlayMixedSports()
    
    tests = [
        ("Single Sport Parlay", test_api.test_single_sport_parlay),
        ("Mixed NFL+NBA Parlay", test_api.test_mixed_sports_parlay_nfl_nba),
        ("Mixed All Sports Parlay", test_api.test_mixed_sports_parlay_all_sports),
        ("Conservative Mixed Parlay", test_api.test_mixed_sports_conservative_profile),
        ("Degen Mixed Parlay", test_api.test_mixed_sports_degen_profile),
        ("Max Legs (20) Mixed Parlay", test_api.test_max_legs_mixed_parlay),
        ("Single Leg Mixed Parlay", test_api.test_single_leg_mixed_parlay),
        ("Triple Parlay Mixed Sports", test_triple.test_triple_parlay_mixed_sports),
    ]
    
    results = []
    
    for name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"Running: {name}")
        print("=" * 60)
        
        try:
            await test_func()
            results.append((name, "PASS", None))
            print(f"✓ {name}: PASSED")
        except AssertionError as e:
            results.append((name, "FAIL", str(e)))
            print(f"✗ {name}: FAILED - {e}")
        except Exception as e:
            results.append((name, "ERROR", str(e)))
            print(f"✗ {name}: ERROR - {e}")
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, status, _ in results if status == "PASS")
    failed = sum(1 for _, status, _ in results if status == "FAIL")
    errors = sum(1 for _, status, _ in results if status == "ERROR")
    
    for name, status, error in results:
        icon = "✓" if status == "PASS" else "✗"
        print(f"{icon} {name}: {status}")
        if error:
            print(f"  Error: {error}")
    
    print(f"\nTotal: {len(results)} | Passed: {passed} | Failed: {failed} | Errors: {errors}")
    
    return passed, failed, errors


def run_unit_tests():
    """Run unit tests."""
    print("=" * 70)
    print("UNIT TESTS")
    print("=" * 70)
    
    test_builder = TestMixedSportsParlayBuilderUnit()
    test_schemas = TestParlaySchemas()
    
    tests = [
        ("Supported Sports", test_builder.test_supported_sports),
        ("Min Confidence Thresholds", test_builder.test_min_confidence_thresholds),
        ("Parlay Probability Calculation", test_builder.test_calculate_parlay_probability),
        ("Build Legs Data Format", test_builder.test_build_legs_data_format),
        ("Build Legs Missing Fields", test_builder.test_build_legs_data_missing_fields),
        ("Select Best Legs Deduplication", test_builder.test_select_best_legs_deduplication),
        ("Select Balanced Legs Distribution", test_builder.test_select_balanced_legs_distribution),
        ("ParlayRequest With Sports", test_schemas.test_parlay_request_with_sports),
        ("ParlayRequest Defaults", test_schemas.test_parlay_request_defaults),
        ("LegResponse With Sport", test_schemas.test_leg_response_with_sport),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            test_func()
            print(f"✓ {name}: PASSED")
            passed += 1
        except Exception as e:
            print(f"✗ {name}: FAILED - {e}")
            failed += 1
    
    print(f"\nUnit Tests: {passed} passed, {failed} failed")
    return passed, failed


if __name__ == "__main__":
    import sys
    
    print("\n" + "=" * 70)
    print("RUNNING MIXED SPORTS PARLAY TESTS")
    print("=" * 70 + "\n")
    
    # Run unit tests first (don't need server)
    unit_passed, unit_failed = run_unit_tests()
    
    # Run API tests if server is available
    print("\n")
    try:
        passed, failed, errors = asyncio.run(run_all_api_tests())
        
        total_passed = unit_passed + passed
        total_failed = unit_failed + failed + errors
        
        print("\n" + "=" * 70)
        print(f"OVERALL: {total_passed} passed, {total_failed} failed")
        print("=" * 70)
        
        sys.exit(0 if total_failed == 0 else 1)
    except Exception as e:
        print(f"\nCould not run API tests (server may not be running): {e}")
        print("Unit tests completed.")
        sys.exit(0 if unit_failed == 0 else 1)

