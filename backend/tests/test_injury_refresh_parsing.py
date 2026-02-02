"""
Unit tests for API-Sports injury parsing and refresh grouping.
"""

import pytest

from app.services.apisports.injury_parser import (
    apisports_injury_payload_to_canonical,
    LEAGUE_TO_SPORT_KEY,
)


class TestApisportsInjuryPayloadToCanonical:
    """apisports_injury_payload_to_canonical with mocked payloads."""

    def test_three_injuries_grouped_unit_counts_nfl(self) -> None:
        payload = {
            "response": [
                {"player": {"name": "Player A", "position": "QB"}, "team": {"id": 1}},
                {"player": {"name": "Player B", "position": "RB"}, "team": {"id": 1}},
                {"player": {"name": "Player C", "position": "WR"}, "team": {"id": 1}},
            ]
        }
        out = apisports_injury_payload_to_canonical(payload, league="NFL")
        assert out["total_injured"] == 3
        assert out["key_players_out"]  # top 5 capped
        assert len(out["key_players_out"]) == 3
        assert out["unit_counts"].get("QB") == 1
        assert out["unit_counts"].get("RB") == 1
        assert out["unit_counts"].get("WR") == 1
        assert "impact_assessment" in out
        assert "injury_summary" in out

    def test_key_players_capped_at_five(self) -> None:
        payload = {
            "response": [
                {"player": {"name": f"Player {i}", "position": "WR"}, "team": {"id": 1}}
                for i in range(7)
            ]
        }
        out = apisports_injury_payload_to_canonical(payload, league="NFL")
        assert out["total_injured"] == 7
        assert len(out["key_players_out"]) == 5
        assert out["unit_counts"].get("WR") == 7

    def test_empty_payload_returns_canonical_empty(self) -> None:
        out = apisports_injury_payload_to_canonical({}, league="NFL")
        assert out["total_injured"] == 0
        assert out["key_players_out"] == []
        assert out["unit_counts"] == {}
        assert "No major injuries flagged" in out["impact_assessment"]

    def test_qb_injury_adds_qb_phrase_nfl(self) -> None:
        payload = {
            "response": [
                {"player": {"name": "QB1", "position": "QB"}, "team": {"id": 1}},
            ]
        }
        out = apisports_injury_payload_to_canonical(payload, league="NFL")
        assert "QB" in out["impact_assessment"] or "qb" in out["impact_assessment"].lower()


class TestLeagueToSportKey:
    def test_nfl_maps(self) -> None:
        assert LEAGUE_TO_SPORT_KEY.get("NFL") == "americanfootball_nfl"

    def test_nba_maps(self) -> None:
        assert LEAGUE_TO_SPORT_KEY.get("NBA") == "basketball_nba"
