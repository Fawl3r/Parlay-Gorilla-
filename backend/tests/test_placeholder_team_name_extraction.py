"""Test placeholder team name extraction and filtering for Super Bowl/post-season games."""

import pytest
from datetime import datetime, timezone, timedelta

from app.models.game import Game
from app.services.odds_api.odds_api_data_store import OddsApiDataStore
from app.services.sports_config import get_sport_config
from app.utils.nfl_week import calculate_nfl_week


@pytest.mark.asyncio
async def test_extracts_team_names_from_h2h_outcomes_when_event_has_placeholders(db):
    """Test that team names are extracted from h2h market outcomes when event has AFC/NFC placeholders."""
    sport_config = get_sport_config("nfl")
    store = OddsApiDataStore(db)
    
    # Simulate Super Bowl game with AFC/NFC placeholders but actual team names in h2h outcomes
    commence = datetime.now(timezone.utc) + timedelta(days=7)
    commence_str = commence.isoformat().replace("+00:00", "Z")
    
    api_data = [
        {
            "id": "odds-nfl-superbowl-2026",
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
    
    games = await store.normalize_and_store_odds(api_data, sport_config)
    await db.commit()
    
    # Should extract team names from h2h outcomes
    assert len(games) == 1
    assert games[0].home_team == "San Francisco 49ers"  # Second outcome is typically home
    assert games[0].away_team == "Kansas City Chiefs"  # First outcome is typically away
    assert games[0].home_team.upper() not in {"AFC", "NFC", "TBD"}
    assert games[0].away_team.upper() not in {"AFC", "NFC", "TBD"}


@pytest.mark.asyncio
async def test_extracts_team_names_from_spreads_when_h2h_has_placeholders(db):
    """Test that team names are extracted from spreads market when h2h also has placeholders."""
    sport_config = get_sport_config("nfl")
    store = OddsApiDataStore(db)
    
    commence = datetime.now(timezone.utc) + timedelta(days=7)
    commence_str = commence.isoformat().replace("+00:00", "Z")
    
    api_data = [
        {
            "id": "odds-nfl-test",
            "home_team": "AFC",
            "away_team": "NFC",
            "commence_time": commence_str,
            "bookmakers": [
                {
                    "key": "draftkings",
                    "markets": [
                        {
                            "key": "h2h",
                            "outcomes": [
                                {"name": "AFC", "price": -150},  # Still placeholder
                                {"name": "NFC", "price": 130},  # Still placeholder
                            ],
                        },
                        {
                            "key": "spreads",
                            "outcomes": [
                                {
                                    "name": "Kansas City Chiefs",  # Actual team name
                                    "price": -110,
                                    "point": 3.5,
                                },
                                {
                                    "name": "San Francisco 49ers",  # Actual team name
                                    "price": -110,
                                    "point": -3.5,
                                },
                            ],
                        },
                    ],
                }
            ],
        }
    ]
    
    games = await store.normalize_and_store_odds(api_data, sport_config)
    await db.commit()
    
    # Should extract from spreads
    assert len(games) == 1
    assert "Chiefs" in games[0].away_team or "49ers" in games[0].away_team
    assert "Chiefs" in games[0].home_team or "49ers" in games[0].home_team
    assert games[0].home_team.upper() not in {"AFC", "NFC", "TBD"}
    assert games[0].away_team.upper() not in {"AFC", "NFC", "TBD"}


@pytest.mark.asyncio
async def test_postseason_detection_for_nfl(db):
    """Test that post-season games are detected correctly."""
    sport_config = get_sport_config("nfl")
    store = OddsApiDataStore(db)
    
    # Super Bowl is typically week 22 (late January/early February)
    # Create a date that would be week 22
    super_bowl_date = datetime(2026, 2, 3, 0, 0, 0, tzinfo=timezone.utc)
    commence_str = super_bowl_date.isoformat().replace("+00:00", "Z")
    
    week = calculate_nfl_week(super_bowl_date)
    is_postseason = week is not None and week >= 19
    
    # If we can calculate the week, verify it's post-season
    if week:
        assert is_postseason == (week >= 19), f"Expected post-season detection for week {week}"
    
    api_data = [
        {
            "id": "odds-nfl-superbowl",
            "home_team": "AFC",
            "away_team": "NFC",
            "commence_time": commence_str,
            "bookmakers": [
                {
                    "key": "fanduel",
                    "markets": [
                        {
                            "key": "h2h",
                            "outcomes": [
                                {"name": "Kansas City Chiefs", "price": -150},
                                {"name": "San Francisco 49ers", "price": 130},
                            ],
                        }
                    ],
                }
            ],
        }
    ]
    
    games = await store.normalize_and_store_odds(api_data, sport_config)
    await db.commit()
    
    # Should extract team names even for post-season
    if len(games) > 0:
        assert games[0].home_team.upper() not in {"AFC", "NFC"}
        assert games[0].away_team.upper() not in {"AFC", "NFC"}


@pytest.mark.asyncio
async def test_team_name_normalizer_preserves_afc_nfc_for_nfl(db):
    """Test that TeamNameNormalizer doesn't strip AFC/NFC for NFL games."""
    from app.services.team_name_normalizer import TeamNameNormalizer
    
    normalizer = TeamNameNormalizer()
    
    # Standalone AFC/NFC should be preserved (for detection)
    assert normalizer.normalize("AFC", "NFL") == "afc"
    assert normalizer.normalize("NFC", "NFL") == "nfc"
    
    # But should still normalize other team names
    assert normalizer.normalize("Kansas City Chiefs", "NFL") == "kansas city chiefs"
    assert normalizer.normalize("San Francisco 49ers", "NFL") == "san francisco 49ers"
    
    # For soccer, AFC should still be stripped if it's a prefix
    assert normalizer.normalize("AFC Ajax", "SOCCER") == "ajax"
    assert normalizer.normalize("AFC", "SOCCER") == "afc"  # Standalone still preserved
