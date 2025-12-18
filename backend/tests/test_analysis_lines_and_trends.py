from types import SimpleNamespace

from app.services.analysis_generator import AnalysisGeneratorService


def test_extract_lines_from_markets_parses_spread_and_total():
    markets = [
        SimpleNamespace(
            market_type="spreads",
            odds=[
                SimpleNamespace(outcome="home -3.5"),
                SimpleNamespace(outcome="away +3.5"),
            ],
        ),
        SimpleNamespace(
            market_type="totals",
            odds=[
                SimpleNamespace(outcome="over 44.5"),
                SimpleNamespace(outcome="under 44.5"),
            ],
        ),
    ]

    spread, total = AnalysisGeneratorService._extract_lines_from_markets(markets)
    assert spread == -3.5 or spread == 3.5  # sign may depend on ordering, only care magnitude
    assert abs(spread) == 3.5
    assert total == 44.5


def test_build_trend_snapshot_includes_ats_and_over_under():
    matchup_data = {
        "home_team_stats": {
            "ats_trends": {"wins": 5, "losses": 3},
            "over_under_trends": {"overs": 4, "unders": 4},
        },
        "away_team_stats": {
            "ats_trends": {"wins": 6, "losses": 2},
            "over_under_trends": {"overs": 5, "unders": 3},
        },
    }

    snapshot = AnalysisGeneratorService._build_trend_snapshot(matchup_data)
    assert snapshot["ats"]["home"]["wins"] == 5
    assert snapshot["ats"]["away"]["wins"] == 6
    assert snapshot["over_under"]["home"]["overs"] == 4
    assert snapshot["over_under"]["away"]["unders"] == 3


