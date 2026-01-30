"""Unit tests: AnalysisContentNormalizer applies player-reference sanitizer to full_article."""

from app.services.analysis_content_normalizer import AnalysisContentNormalizer


def test_normalizer_sanitizes_full_article_with_player_name():
    content = {
        "opening_summary": "Preview.",
        "full_article": "## Opening Summary\n\nThe Seahawks are led by Geno Smith on offense.",
        "ats_trends": {},
        "totals_trends": {},
        "ai_spread_pick": {},
        "ai_total_pick": {},
        "best_bets": [],
        "model_win_probability": {},
        "confidence_breakdown": {},
    }
    normalizer = AnalysisContentNormalizer()
    out = normalizer.normalize(content)
    assert "full_article" in out
    assert "Geno Smith" not in out["full_article"]
    assert "led by its core playmakers" in out["full_article"]
    assert "## Opening Summary" in out["full_article"]


def test_normalizer_sanitizes_empty_full_article():
    content = {"full_article": ""}
    normalizer = AnalysisContentNormalizer()
    out = normalizer.normalize(content)
    assert out["full_article"] == ""


def test_normalizer_sanitizes_full_article_with_no_player_mentions():
    content = {
        "full_article": "## Best Bets\n\nTake the under. Defense wins.",
    }
    normalizer = AnalysisContentNormalizer()
    out = normalizer.normalize(content)
    assert out["full_article"] == "## Best Bets\n\nTake the under. Defense wins."
