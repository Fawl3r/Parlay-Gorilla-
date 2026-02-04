"""Contract tests for ugie_v2: required keys, ranges, missing-data behavior."""

from app.services.analysis.ugie_v2.ugie_v2_builder import UgieV2Builder, get_minimal_ugie_v2
from app.services.analysis.ugie_v2.validation import validate_and_clamp_ugie_v2, REQUIRED_PILLARS

REQUIRED_UGIE_KEYS = ("pillars", "confidence_score", "risk_level", "data_quality", "recommended_action", "market_snapshot")


def _minimal_draft():
    return {
        "offensive_matchup_edges": {},
        "defensive_matchup_edges": {},
        "outcome_paths": {},
        "confidence_breakdown": {},
        "best_bets": [],
        "ai_spread_pick": {},
        "ai_total_pick": {},
    }


def _minimal_matchup_data():
    return {
        "home_injuries": {},
        "away_injuries": {},
        "home_team_stats": {},
        "away_team_stats": {},
    }


def _minimal_game(sport: str = "nfl"):
    g = type("Game", (), {})()
    g.sport = sport
    g.home_team = "Home"
    g.away_team = "Away"
    return g


def _minimal_odds():
    return {"home_spread_point": -3.0, "total_line": 45.0, "home_ml": -150, "away_ml": 130}


def _minimal_model_probs():
    return {"home_win_prob": 0.55, "away_win_prob": 0.45, "ai_confidence": 60.0}


class TestUgieV2RequiredKeys:
    """Ensure ugie_v2 contains all required keys."""

    def test_builder_output_has_required_keys(self):
        draft = _minimal_draft()
        matchup_data = _minimal_matchup_data()
        game = _minimal_game()
        ugie = UgieV2Builder.build(
            draft=draft,
            matchup_data=matchup_data,
            game=game,
            odds_snapshot=_minimal_odds(),
            model_probs=_minimal_model_probs(),
            weather_block=None,
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
        draft = _minimal_draft()
        matchup_data = _minimal_matchup_data()
        matchup_data["home_injuries"] = {}
        matchup_data["away_injuries"] = {}
        game = _minimal_game()
        ugie = UgieV2Builder.build(
            draft=draft,
            matchup_data=matchup_data,
            game=game,
            odds_snapshot=_minimal_odds(),
            model_probs=_minimal_model_probs(),
            weather_block=None,
        )
        missing = ugie["data_quality"].get("missing") or []
        assert "injuries" in missing

    def test_missing_weather_for_nfl_adds_weather_to_missing(self):
        draft = _minimal_draft()
        matchup_data = _minimal_matchup_data()
        matchup_data["weather"] = None
        game = _minimal_game("nfl")
        ugie = UgieV2Builder.build(
            draft=draft,
            matchup_data=matchup_data,
            game=game,
            odds_snapshot=_minimal_odds(),
            model_probs=_minimal_model_probs(),
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
        draft = _minimal_draft()
        matchup_data = _minimal_matchup_data()
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
        game = _minimal_game("nba")
        ugie = UgieV2Builder.build(
            draft=draft,
            matchup_data=matchup_data,
            game=game,
            odds_snapshot=_minimal_odds(),
            model_probs=_minimal_model_probs(),
            weather_block=None,
        )
        av = ugie["pillars"]["availability"]
        why = (av.get("why_summary") or "").strip()
        assert placeholder in why, "placeholder should appear in why_summary"
        assert why.count(placeholder) == 1, (
            "identical home/away placeholder must appear only once in why_summary"
        )
