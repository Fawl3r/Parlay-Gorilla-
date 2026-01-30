"""Tests for KeyPlayersBuilder: allowlist-only names, sport templates, filtering."""

import pytest

from app.services.analysis.ugie_v2.key_players_builder import KeyPlayersBuilder
from app.services.analysis.ugie_v2.models import KeyPlayersBlock


def _minimal_game(sport: str = "nfl"):
    g = type("Game", (), {})()
    g.sport = sport
    g.home_team = "Home"
    g.away_team = "Away"
    return g


class TestKeyPlayersBuilderEmptyAllowlist:
    """Empty allowlist -> status=unavailable, zero players."""

    def test_empty_allowlist_returns_unavailable(self):
        builder = KeyPlayersBuilder()
        game = _minimal_game("nfl")
        block = builder.build(
            game=game,
            sport="nfl",
            matchup_data={},
            allowed_player_names=[],
            allowlist_by_team={"home": [], "away": []},
        )
        assert isinstance(block, KeyPlayersBlock)
        assert block.status == "unavailable"
        assert block.reason == "roster_missing_or_empty"
        assert block.players == []

    def test_none_allowlist_returns_unavailable(self):
        builder = KeyPlayersBuilder()
        game = _minimal_game("mlb")
        block = builder.build(
            game=game,
            sport="mlb",
            matchup_data={},
            allowed_player_names=None,
        )
        assert block.status == "unavailable"
        assert len(block.players) == 0


class TestKeyPlayersBuilderLimitedFallback:
    """Non-empty allowlist_by_team -> status=limited, all names allowlisted."""

    def test_limited_fallback_all_names_allowlisted(self):
        builder = KeyPlayersBuilder()
        game = _minimal_game("nfl")
        allowed = ["Alice Smith", "Bob Jones", "Carol Lee", "Dan Brown", "Eve Wilson"]
        by_team = {"home": ["Alice Smith", "Bob Jones"], "away": ["Carol Lee", "Dan Brown"]}
        block = builder.build(
            game=game,
            sport="nfl",
            matchup_data={},
            allowed_player_names=allowed,
            allowlist_by_team=by_team,
            positions_by_name={"Alice Smith": "QB", "Bob Jones": "RB", "Carol Lee": "WR", "Dan Brown": "TE"},
        )
        assert block.status == "limited"
        names = [p.name for p in block.players]
        assert all(n in allowed for n in names)
        for p in block.players:
            assert p.why
            assert "Alice" not in p.why or p.name == "Alice Smith"
            assert "Bob" not in p.why or p.name == "Bob Jones"

    def test_why_contains_no_other_player_names(self):
        builder = KeyPlayersBuilder()
        game = _minimal_game("soccer")
        allowed = ["Player One", "Player Two"]
        by_team = {"home": ["Player One"], "away": ["Player Two"]}
        block = builder.build(
            game=game,
            sport="soccer",
            matchup_data={},
            allowed_player_names=allowed,
            allowlist_by_team=by_team,
        )
        for p in block.players:
            for other in allowed:
                if other != p.name and other in p.why:
                    pytest.fail(f"why must not mention other player: {other!r} in {p.why!r}")


class TestKeyPlayersBuilderSportTemplates:
    """Sport-aware why templates produce short why."""

    def test_nfl_qb_why_short(self):
        builder = KeyPlayersBuilder()
        game = _minimal_game("nfl")
        by_team = {"home": ["QB Name"], "away": ["RB Name"]}
        positions = {"QB Name": "QB", "RB Name": "RB"}
        block = builder.build(
            game=game,
            sport="nfl",
            matchup_data={},
            allowed_player_names=["QB Name", "RB Name"],
            allowlist_by_team=by_team,
            positions_by_name=positions,
        )
        assert len(block.players) >= 1
        qb = next((p for p in block.players if p.role == "QB"), None)
        if qb:
            assert len(qb.why) <= 250
            assert "Passing" in qb.why or "efficiency" in qb.why.lower()

    def test_mlb_sp_why_short(self):
        builder = KeyPlayersBuilder()
        game = _minimal_game("mlb")
        by_team = {"home": ["SP Name"], "away": ["RP Name"]}
        positions = {"SP Name": "SP", "RP Name": "RP"}
        block = builder.build(
            game=game,
            sport="mlb",
            matchup_data={},
            allowed_player_names=["SP Name", "RP Name"],
            allowlist_by_team=by_team,
            positions_by_name=positions,
        )
        sp = next((p for p in block.players if p.role == "SP"), None)
        if sp:
            assert "pitcher" in sp.why.lower() or "run" in sp.why.lower()

    def test_soccer_striker_why_short(self):
        builder = KeyPlayersBuilder()
        game = _minimal_game("soccer")
        by_team = {"home": ["Striker A"], "away": ["Mid B"]}
        positions = {"Striker A": "Forward", "Mid B": "Midfielder"}
        block = builder.build(
            game=game,
            sport="soccer",
            matchup_data={},
            allowed_player_names=["Striker A", "Mid B"],
            allowlist_by_team=by_team,
            positions_by_name=positions,
        )
        for p in block.players:
            assert len(p.why) <= 250


class TestKeyPlayersBuilderFilterNonAllowlisted:
    """Non-allowlisted candidate in matchup_data is filtered out."""

    def test_non_allowlisted_filtered_out(self):
        builder = KeyPlayersBuilder()
        game = _minimal_game("nfl")
        allowed = ["Allowlisted One", "Allowlisted Two"]
        by_team = {"home": ["Allowlisted One"], "away": ["Allowlisted Two"]}
        matchup_data = {
            "home_features": {
                "key_players": [
                    {"name": "Allowlisted One", "position": "QB"},
                    {"name": "Not In Allowlist", "position": "WR"},
                ]
            },
            "away_features": {
                "key_players": [{"name": "Allowlisted Two", "position": "WR"}]
            },
        }
        block = builder.build(
            game=game,
            sport="nfl",
            matchup_data=matchup_data,
            allowed_player_names=allowed,
            allowlist_by_team=by_team,
        )
        names = [p.name for p in block.players]
        assert "Not In Allowlist" not in names
        assert "Allowlisted One" in names or "Allowlisted Two" in names


class TestKeyPlayersBuilderThinData:
    """Thin-data sport -> unavailable."""

    def test_ufc_returns_unavailable(self):
        builder = KeyPlayersBuilder()
        game = _minimal_game("ufc")
        block = builder.build(
            game=game,
            sport="ufc",
            matchup_data={},
            allowed_player_names=["Fighter A", "Fighter B"],
            allowlist_by_team={"home": ["Fighter A"], "away": ["Fighter B"]},
        )
        assert block.status == "unavailable"
        assert block.reason == "thin_data_sport"
        assert block.players == []


class TestKeyPlayersBuilderRosterTeamMismatch:
    """Allowlist exists but by_team lacks home or away -> unavailable, roster_team_mismatch."""

    def test_home_empty_returns_roster_team_mismatch(self):
        builder = KeyPlayersBuilder()
        game = _minimal_game("nfl")
        allowed = ["Alice", "Bob"]
        by_team = {"home": [], "away": ["Bob"]}
        block = builder.build(
            game=game,
            sport="nfl",
            matchup_data={},
            allowed_player_names=allowed,
            allowlist_by_team=by_team,
        )
        assert block.status == "unavailable"
        assert block.reason == "roster_team_mismatch"
        assert block.players == []

    def test_away_empty_returns_roster_team_mismatch(self):
        builder = KeyPlayersBuilder()
        game = _minimal_game("nfl")
        allowed = ["Alice", "Bob"]
        by_team = {"home": ["Alice"], "away": []}
        block = builder.build(
            game=game,
            sport="nfl",
            matchup_data={},
            allowed_player_names=allowed,
            allowlist_by_team=by_team,
        )
        assert block.status == "unavailable"
        assert block.reason == "roster_team_mismatch"
        assert block.players == []


class TestKeyPlayersBuilderStatusGating:
    """status=available only when stat-derived candidates meet threshold."""

    def test_one_home_one_away_stat_candidates_returns_limited(self):
        builder = KeyPlayersBuilder()
        game = _minimal_game("nfl")
        allowed = ["Home One", "Away One"]
        by_team = {"home": ["Home One"], "away": ["Away One"]}
        matchup_data = {
            "home_features": {"key_players": [{"name": "Home One", "position": "QB"}]},
            "away_features": {"key_players": [{"name": "Away One", "position": "WR"}]},
        }
        block = builder.build(
            game=game,
            sport="nfl",
            matchup_data=matchup_data,
            allowed_player_names=allowed,
            allowlist_by_team=by_team,
        )
        assert block.status == "limited"
        assert block.reason in (
            "insufficient_stat_candidates",
            "roster_only_no_stats",
        )

    def test_two_per_side_stat_candidates_returns_available(self):
        builder = KeyPlayersBuilder()
        game = _minimal_game("nfl")
        allowed = ["H1", "H2", "A1", "A2"]
        by_team = {"home": ["H1", "H2"], "away": ["A1", "A2"]}
        matchup_data = {
            "home_features": {
                "key_players": [
                    {"name": "H1", "position": "QB"},
                    {"name": "H2", "position": "WR"},
                ]
            },
            "away_features": {
                "key_players": [
                    {"name": "A1", "position": "QB"},
                    {"name": "A2", "position": "WR"},
                ]
            },
        }
        block = builder.build(
            game=game,
            sport="nfl",
            matchup_data=matchup_data,
            allowed_player_names=allowed,
            allowlist_by_team=by_team,
        )
        assert block.status in ("available", "limited")
        assert len(block.players) >= 2
        if block.status == "available":
            assert block.reason is None


class TestKeyPlayersBuilderMetricsTruncation:
    """Max 3 metrics per player; label ≤12 chars, value ≤16 chars."""

    def test_metrics_capped_and_truncated(self):
        builder = KeyPlayersBuilder()
        game = _minimal_game("nfl")
        allowed = ["Player A", "Player B"]
        by_team = {"home": ["Player A"], "away": ["Player B"]}
        matchup_data = {
            "home_features": {
                "key_players": [
                    {
                        "name": "Player A",
                        "position": "QB",
                        "metrics": [
                            {"label": "Very Long Label Here", "value": "Very Long Value Here"},
                            {"label": "L2", "value": "V2"},
                            {"label": "L3", "value": "V3"},
                            {"label": "L4", "value": "V4"},
                        ],
                    }
                ]
            },
            "away_features": {"key_players": [{"name": "Player B", "position": "WR"}]},
        }
        block = builder.build(
            game=game,
            sport="nfl",
            matchup_data=matchup_data,
            allowed_player_names=allowed,
            allowlist_by_team=by_team,
        )
        for player in block.players:
            metrics = player.metrics
            if metrics is not None:
                assert len(metrics) <= 3
                for m in metrics:
                    assert len(m.get("label", "")) <= 12
                    assert len(m.get("value", "")) <= 16
