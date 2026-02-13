"""Contract tests for ugie_v2: required keys, ranges, missing-data behavior."""

from app.services.analysis.ugie_v2.ugie_v2_builder import UgieV2Builder, get_minimal_ugie_v2
from app.services.analysis.ugie_v2.validation import validate_and_clamp_ugie_v2, REQUIRED_PILLARS
from tests.ugie_fixtures import minimal_draft, minimal_matchup_data, minimal_game, minimal_odds, minimal_model_probs

REQUIRED_UGIE_KEYS = ("pillars", "confidence_score", "risk_level", "data_quality", "recommended_action", "market_snapshot")


class TestUgieV2RequiredKeys:
    """Ensure ugie_v2 contains all required keys."""

    def test_builder_output_has_required_keys(self):
        draft = minimal_draft()
        matchup_data = minimal_matchup_data()
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
        for key in REQUIRED_UGIE_KEYS:
            assert key in ugie, f"missing key: {key}"
        assert "pillars" in ugie
        for name in REQUIRED_PILLARS:
            assert name in ugie["pillars"], f"missing pillar: {name}"

    def test_minimal_fallback_has_required_keys(self):
        ugie = get_minimal_ugie_v2()
        for key in REQUIRED_UGIE_KEYS:
            assert key in ugie
        for name in REQUIRED_PILLARS:
            assert name in ugie["pillars"]


class TestUgieV2Ranges:
    """Ensure pillar score/confidence and confidence_score are in [0, 1]."""

    def test_pillar_scores_in_range(self):
        ugie = get_minimal_ugie_v2()
        for name, p in ugie["pillars"].items():
            assert isinstance(p, dict)
            s = p.get("score", 0.5)
            c = p.get("confidence", 0.0)
            assert 0.0 <= s <= 1.0, f"pillar {name} score {s} out of range"
            assert 0.0 <= c <= 1.0, f"pillar {name} confidence {c} out of range"
        assert 0.0 <= ugie["confidence_score"] <= 1.0

    def test_validation_clamps_scores(self):
        ugie = {
            "pillars": {
                "availability": {"score": 1.5, "confidence": -0.1, "signals": [], "why_summary": "", "top_edges": []},
                "efficiency": {"score": 0.5, "confidence": 0.5, "signals": [], "why_summary": "", "top_edges": []},
                "matchup_fit": {"score": 0.5, "confidence": 0.5, "signals": [], "why_summary": "", "top_edges": []},
                "script_stability": {"score": 0.5, "confidence": 0.5, "signals": [], "why_summary": "", "top_edges": []},
                "market_alignment": {"score": 0.5, "confidence": 0.5, "signals": [], "why_summary": "", "top_edges": []},
            },
            "confidence_score": 2.0,
            "risk_level": "Medium",
            "data_quality": {"status": "Good", "missing": [], "stale": [], "provider": ""},
            "recommended_action": "",
            "market_snapshot": {},
        }
        out = validate_and_clamp_ugie_v2(ugie)
        assert out["pillars"]["availability"]["score"] <= 1.0
        assert out["pillars"]["availability"]["confidence"] >= 0.0
        assert out["confidence_score"] <= 1.0


class TestUgieV2MissingData:
    """Missing injuries/weather cause data_quality downgrade and lower confidence."""

    def test_missing_injuries_adds_to_data_quality_missing(self):
        draft = minimal_draft()
        matchup_data = minimal_matchup_data()
        matchup_data["home_injuries"] = {}
        matchup_data["away_injuries"] = {}
        game = minimal_game()
        ugie = UgieV2Builder.build(
            draft=draft,
            matchup_data=matchup_data,
            game=game,
            odds_snapshot=minimal_odds(),
            model_probs=minimal_model_probs(),
            weather_block=None,
        )
        missing = ugie["data_quality"].get("missing") or []
        assert "injuries" in missing

    def test_missing_weather_for_nfl_adds_weather_to_missing(self):
        draft = minimal_draft()
        matchup_data = minimal_matchup_data()
        matchup_data["weather"] = None
        game = minimal_game("nfl")
        ugie = UgieV2Builder.build(
            draft=draft,
            matchup_data=matchup_data,
            game=game,
            odds_snapshot=minimal_odds(),
            model_probs=minimal_model_probs(),
            weather_block={"weather_confidence_modifier": 0.95, "weather_efficiency_modifier": 1.0, "weather_volatility_modifier": 1.0, "why": "Weather data missing.", "rules_fired": ["weather_missing"]},
        )
        missing = ugie["data_quality"].get("missing") or []
        assert "weather" in missing

    def test_minimal_fallback_has_poor_data_quality(self):
        ugie = get_minimal_ugie_v2()
        assert ugie["data_quality"]["status"] == "Poor"
        assert "ugie_v2_builder_error" in ugie["data_quality"]["missing"] or len(ugie["data_quality"]["missing"]) > 0


class TestUgieV2ValidationNeverFails:
    """Validation never raises; always returns valid dict."""

    def test_validate_none_returns_minimal(self):
        out = validate_and_clamp_ugie_v2(None)
        assert isinstance(out, dict)
        assert "pillars" in out
        assert "confidence_score" in out

    def test_validate_empty_dict_fills_required(self):
        out = validate_and_clamp_ugie_v2({})
        for key in REQUIRED_UGIE_KEYS:
            assert key in out
        for name in REQUIRED_PILLARS:
            assert name in out["pillars"]

    def test_validate_ugie_with_key_players_tolerates_and_normalizes(self):
        ugie = {
            "pillars": {p: {"score": 0.5, "confidence": 0.5, "signals": [], "why_summary": "", "top_edges": []} for p in REQUIRED_PILLARS},
            "confidence_score": 0.6,
            "risk_level": "Medium",
            "data_quality": {"status": "Good", "missing": [], "stale": [], "provider": ""},
            "recommended_action": "",
            "market_snapshot": {},
            "key_players": {
                "status": "limited",
                "reason": "roster_only_no_stats",
                "players": [
                    {"name": "A", "team": "home", "role": "QB", "impact": "High", "why": "Short why.", "confidence": 1.5},
                    {"name": "B", "team": "away", "role": "WR", "impact": "Medium", "why": "X" * 300, "confidence": -0.1},
                ],
                "allowlist_source": "roster_current_matchup_teams",
            },
        }
        out = validate_and_clamp_ugie_v2(ugie)
        assert "key_players" in out
        kp = out["key_players"]
        assert kp["status"] == "limited"
        assert len(kp["players"]) == 2
        assert kp["players"][0]["confidence"] <= 1.0
        assert kp["players"][1]["confidence"] >= 0.0
        assert len(kp["players"][1]["why"]) <= 200


class TestUgieV2AvailabilityDedupe:
    """When home and away have identical placeholder text, why_summary should contain only one instance."""

    def test_availability_why_summary_dedupes_identical_placeholder(self):
        # Use a sport with no UGIE adapter (e.g. nba) so the builder uses the fallback path
        # where dedupe runs. NFL/MLB/soccer adapters build why_summary themselves.
        placeholder = "Unable to assess injury impact."
        draft = minimal_draft()
        matchup_data = minimal_matchup_data()
        matchup_data["home_injuries"] = {
            "impact_scores": {"overall_impact": 0.5},
            "injury_severity_score": 0.5,
            "impact_assessment": placeholder,
        }
        matchup_data["away_injuries"] = {
            "impact_scores": {"overall_impact": 0.5},
            "injury_severity_score": 0.5,
            "impact_assessment": placeholder,
        }
        game = minimal_game("nba")
        ugie = UgieV2Builder.build(
            draft=draft,
            matchup_data=matchup_data,
            game=game,
            odds_snapshot=minimal_odds(),
            model_probs=minimal_model_probs(),
            weather_block=None,
        )
        av = ugie["pillars"]["availability"]
        why = (av.get("why_summary") or "").strip()
        assert placeholder in why, "placeholder should appear in why_summary"
        assert why.count(placeholder) == 1, (
            "identical home/away placeholder must appear only once in why_summary"
        )


class TestUgieV2DataQualityRosterInjuries:
    """data_quality includes roster and injuries for UI 'Fetching roster…' badges."""

    def test_data_quality_has_roster_and_injuries(self):
        draft = minimal_draft()
        matchup_data = minimal_matchup_data()
        matchup_data["home_injuries"] = {
            "impact_scores": {"overall_impact": 0.5},
            "injury_severity_score": 0.5,
            "impact_assessment": "Some impact.",
        }
        matchup_data["away_injuries"] = {
            "impact_scores": {"overall_impact": 0.5},
            "injury_severity_score": 0.5,
            "impact_assessment": "Some impact.",
        }
        game = minimal_game("nba")
        ugie = UgieV2Builder.build(
            draft=draft,
            matchup_data=matchup_data,
            game=game,
            odds_snapshot=minimal_odds(),
            model_probs=minimal_model_probs(),
            weather_block=None,
        )
        dq = ugie.get("data_quality") or {}
        assert "roster" in dq, "data_quality should include roster"
        assert dq["roster"] in ("ready", "stale", "missing", "unavailable")
        assert "injuries" in dq, "data_quality should include injuries"
        assert dq["injuries"] in ("ready", "stale", "missing", "unavailable")

    def test_team_mapping_missing_sets_roster_unavailable(self):
        """When team_mapping_resolved is False, roster is unavailable with reason team_mapping_missing."""
        draft = minimal_draft()
        matchup_data = minimal_matchup_data()
        game = minimal_game()
        ugie = UgieV2Builder.build(
            draft=draft,
            matchup_data=matchup_data,
            game=game,
            odds_snapshot=minimal_odds(),
            model_probs=minimal_model_probs(),
            weather_block=None,
            team_mapping_resolved=False,
        )
        dq = ugie.get("data_quality") or {}
        assert dq.get("roster") == "unavailable"
        assert dq.get("roster_reason") == "team_mapping_missing"
