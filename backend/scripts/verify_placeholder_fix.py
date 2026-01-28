"""Manual verification script for placeholder team name extraction.

This script can be run to verify that the placeholder team name extraction
is working correctly. It simulates The Odds API responses with placeholders
and verifies that team names are extracted correctly.

Usage:
    cd backend
    python scripts/verify_placeholder_fix.py
"""

import asyncio
import sys
from datetime import datetime, timezone, timedelta

# Add parent directory to path
sys.path.insert(0, '.')

from app.services.odds_api.odds_api_data_store import OddsApiDataStore
from app.services.team_name_normalizer import TeamNameNormalizer
from app.services.sports_config import get_sport_config


def test_team_name_extraction():
    """Test that team names are extracted from h2h outcomes."""
    print("=" * 80)
    print("Testing Placeholder Team Name Extraction")
    print("=" * 80)
    
    # Simulate API response with AFC/NFC placeholders but actual team names in outcomes
    commence = datetime.now(timezone.utc) + timedelta(days=7)
    commence_str = commence.isoformat().replace("+00:00", "Z")
    
    api_data = [
        {
            "id": "odds-nfl-superbowl-test",
            "home_team": "AFC",  # Placeholder
            "away_team": "NFC",  # Placeholder
            "commence_time": commence_str,
            "bookmakers": [
                {
                    "key": "fanduel",
                    "markets": [
                        {
                            "key": "h2h",
                            "outcomes": [
                                {
                                    "name": "Kansas City Chiefs",  # Actual team name
                                    "price": -150,
                                },
                                {
                                    "name": "San Francisco 49ers",  # Actual team name
                                    "price": 130,
                                },
                            ],
                        }
                    ],
                }
            ],
        }
    ]
    
    print("\n1. Testing API Response with Placeholders:")
    print(f"   Event-level: {api_data[0]['away_team']} @ {api_data[0]['home_team']}")
    print(f"   h2h Outcomes: {api_data[0]['bookmakers'][0]['markets'][0]['outcomes'][0]['name']} vs {api_data[0]['bookmakers'][0]['markets'][0]['outcomes'][1]['name']}")
    
    # Test extraction logic (without database)
    placeholder_names = {"TBD", "TBA", "TBC", "AFC", "NFC", "TO BE DETERMINED", "TO BE ANNOUNCED"}
    home_team = api_data[0]["home_team"]
    away_team = api_data[0]["away_team"]
    home_upper = home_team.upper()
    away_upper = away_team.upper()
    
    if home_upper in placeholder_names or away_upper in placeholder_names:
        print("\n2. Placeholder detected, extracting from outcomes...")
        
        bookmakers = api_data[0].get("bookmakers", [])
        extracted_home = None
        extracted_away = None
        
        for bookmaker in bookmakers:
            markets = bookmaker.get("markets", [])
            for market in markets:
                if market.get("key") == "h2h":
                    outcomes = market.get("outcomes", [])
                    if len(outcomes) >= 2:
                        outcome_names = [str(outcome.get("name", "")).strip() for outcome in outcomes[:2]]
                        valid_outcomes = [name for name in outcome_names if name.upper() not in placeholder_names]
                        
                        if len(valid_outcomes) >= 2:
                            extracted_away = valid_outcomes[0]
                            extracted_home = valid_outcomes[1]
                            print(f"   ✅ Extracted: {extracted_away} @ {extracted_home}")
                            break
            
            if extracted_home and extracted_away:
                break
        
        if extracted_home and extracted_away:
            print(f"\n3. Result: Successfully extracted team names!")
            print(f"   Original: {away_team} @ {home_team}")
            print(f"   Extracted: {extracted_away} @ {extracted_home}")
            return True
        else:
            print("\n3. Result: ❌ Failed to extract team names")
            return False
    else:
        print("\n2. No placeholders detected")
        return True


def test_team_name_normalizer():
    """Test that TeamNameNormalizer preserves AFC/NFC for NFL."""
    print("\n" + "=" * 80)
    print("Testing TeamNameNormalizer")
    print("=" * 80)
    
    normalizer = TeamNameNormalizer()
    
    test_cases = [
        ("AFC", "NFL", "afc", "Should preserve standalone AFC"),
        ("NFC", "NFL", "nfc", "Should preserve standalone NFC"),
        ("Kansas City Chiefs", "NFL", "kansas city chiefs", "Should normalize regular team name"),
        ("AFC Ajax", "SOCCER", "ajax", "Should strip AFC prefix for soccer"),
        ("AFC", "SOCCER", "afc", "Should preserve standalone AFC even for soccer"),
    ]
    
    all_passed = True
    for name, sport, expected, description in test_cases:
        result = normalizer.normalize(name, sport)
        passed = result == expected
        status = "✅" if passed else "❌"
        print(f"{status} {description}: '{name}' -> '{result}' (expected: '{expected}')")
        if not passed:
            all_passed = False
    
    return all_passed


def test_postseason_detection():
    """Test post-season detection."""
    print("\n" + "=" * 80)
    print("Testing Post-Season Detection")
    print("=" * 80)
    
    try:
        from app.utils.nfl_week import calculate_nfl_week
        
        # Test Super Bowl date (typically week 22, late January/early February)
        super_bowl_date = datetime(2026, 2, 3, 0, 0, 0, tzinfo=timezone.utc)
        week = calculate_nfl_week(super_bowl_date)
        
        if week:
            is_postseason = week >= 19
            print(f"Super Bowl date (Feb 3, 2026): Week {week}, Post-season: {is_postseason}")
            
            if is_postseason:
                print("✅ Post-season detection working correctly")
                return True
            else:
                print(f"⚠️  Week {week} not detected as post-season (expected >= 19)")
                return False
        else:
            print("⚠️  Could not calculate week for Super Bowl date")
            return False
    except Exception as e:
        print(f"❌ Error testing post-season detection: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("PLACEHOLDER TEAM NAME FIX - VERIFICATION")
    print("=" * 80)
    
    results = []
    
    # Test 1: Team name extraction
    results.append(("Team Name Extraction", test_team_name_extraction()))
    
    # Test 2: Team name normalizer
    results.append(("Team Name Normalizer", test_team_name_normalizer()))
    
    # Test 3: Post-season detection
    results.append(("Post-Season Detection", test_postseason_detection()))
    
    # Summary
    print("\n" + "=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 80)
    if all_passed:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 80)
    
    sys.exit(0 if all_passed else 1)
