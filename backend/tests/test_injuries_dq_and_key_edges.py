"""Tests for injuries DQ (no_updates, unavailable) and key-edges fallback when splits incomplete."""

import pytest
from app.services.analysis.ugie_v2.ugie_v2_builder import UgieV2Builder
from app.services.analysis.core_analysis_edges import CoreAnalysisEdgesBuilder, KEY_EDGES_FALLBACK_NOTE
from tests.ugie_fixtures import minimal_draft, minimal_game, minimal_odds, minimal_model_probs


class TestInjuriesDqNoUpdates:
    """When provider returns empty list and pipeline is healthy -> ready + no_updates."""

    def test_injuries_dq_no_updates(self):
        draft = minimal_draft()
        matchup_data = {
            "home_injuries": {
                "key_players_out": [],
                "entries": [],
                "injuries_status": "ready",
                "injuries_reason": "no_updates",
                "total_injured": 0,
            },
            "away_injuries": {
                "key_players_out": [],
                "entries": [],
                "injuries_status": "ready",
                "injuries_reason": "no_updates",
                "total_injured": 0,
            },
            "home_team_stats": {},
            "away_team_stats": {},
        }
        game = minimal_game()
        ugie = UgieV2Builder.build(
            draft=draft,
            matchup_data=matchup_data,
            game=game,
            odds_snapshot=minimal_odds(),
            model_probs=minimal_model_probs(),
            weather_block=None,
            team_mapping_resolved=True,
        )
        dq = ugie.get("data_quality") or {}
        assert dq.get("injuries") == "ready"
        assert dq.get("injuries_reason") == "no_updates"
        assert "injuries_by_team" in ugie
        assert ugie.get("injuries_by_team", {}).get("home") == []
        assert ugie.get("injuries_by_team", {}).get("away") == []


class TestInjuriesUnavailableTeamMapping:
    """When team mapping missing -> unavailable + team_mapping_missing."""

    def test_injuries_unavailable_team_mapping_missing(self):
        draft = minimal_draft()
        matchup_data = {
            "home_injuries": {
                "key_players_out": [],
                "entries": [],
                "injuries_status": "unavailable",
                "injuries_reason": "team_mapping_missing",
            },
            "away_injuries": {
                "key_players_out": [],
                "entries": [],
                "injuries_status": "unavailable",
                "injuries_reason": "team_mapping_missing",
            },
            "home_team_stats": {},
            "away_team_stats": {},
        }
        game = minimal_game()
        ugie = UgieV2Builder.build(
            draft=draft,
            matchup_data=matchup_data,
            game=game,
            odds_snapshot=minimal_odds(),
            model_probs=minimal_model_probs(),
            weather_block=None,
            team_mapping_resolved=True,
        )
        dq = ugie.get("data_quality") or {}
        assert dq.get("injuries") == "unavailable"
        assert dq.get("injuries_reason") == "team_mapping_missing"


class TestKeyEdgesFallbackWhenSplitsMissing:
    """When season-long splits incomplete -> one note + fallback edges."""

    def test_key_edges_fallback_returns_note_and_edges(self):
        game = minimal_game()
        matchup_data = {
            "home_team_stats": {"record": {}, "offense": {}, "defense": {}},
            "away_team_stats": {"record": {}, "offense": {}, "defense": {}},
        }
        model_probs = minimal_model_probs()
        builder = CoreAnalysisEdgesBuilder()
        off, def_, note, fallback = builder.build(game=game, matchup_data=matchup_data, model_probs=model_probs)
        assert note == KEY_EDGES_FALLBACK_NOTE
        assert isinstance(fallback, list)
        assert len(fallback) >= 3
        for e in fallback:
            assert "title" in e
            assert "strength" in e
            assert "explanation" in e
        assert "Using market and recent form" in (off.get("home_advantage") or "")
        assert "Using market and recent form" in (def_.get("home_advantage") or "")
