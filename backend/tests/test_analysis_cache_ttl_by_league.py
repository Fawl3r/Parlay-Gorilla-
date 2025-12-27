from app.core.config import settings
from app.services.analysis.analysis_repository import AnalysisRepository


def test_analysis_cache_ttl_hours_for_nfl_uses_nfl_setting():
    ttl = AnalysisRepository._analysis_cache_ttl_hours_for_league(league="NFL")
    assert ttl == settings.analysis_cache_ttl_hours


def test_analysis_cache_ttl_hours_for_non_nfl_uses_non_nfl_setting():
    ttl = AnalysisRepository._analysis_cache_ttl_hours_for_league(league="NBA")
    assert ttl == settings.analysis_cache_ttl_hours_non_nfl


def test_analysis_cache_ttl_hours_for_league_is_case_insensitive():
    ttl_upper = AnalysisRepository._analysis_cache_ttl_hours_for_league(league="NHL")
    ttl_lower = AnalysisRepository._analysis_cache_ttl_hours_for_league(league="nhl")
    assert ttl_upper == ttl_lower


