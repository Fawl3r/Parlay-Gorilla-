"""Unit tests for ArticlePlayerReferenceSanitizer."""

from app.services.analysis.article_player_reference_sanitizer import (
    ArticlePlayerReferenceSanitizer,
)


def test_sanitize_empty_or_none():
    s = ArticlePlayerReferenceSanitizer()
    assert s.sanitize("") == ""
    assert s.sanitize(None) == ""


def test_sanitize_led_by_name():
    s = ArticlePlayerReferenceSanitizer()
    text = "The Seahawks are led by Geno Smith on offense."
    assert "Geno Smith" not in s.sanitize(text)
    assert "led by its core playmakers" in s.sanitize(text)


def test_sanitize_quarterback_name():
    s = ArticlePlayerReferenceSanitizer()
    text = "Quarterback Patrick Mahomes will need to be sharp."
    out = s.sanitize(text)
    assert "Patrick Mahomes" not in out
    assert "Quarterback" in out or "quarterback" in out


def test_sanitize_qb_name():
    s = ArticlePlayerReferenceSanitizer()
    text = "QB Josh Allen has been elite."
    out = s.sanitize(text)
    assert "Josh Allen" not in out
    assert "QB" in out


def test_sanitize_rb_wr_name():
    s = ArticlePlayerReferenceSanitizer()
    text = "Running back Derrick Henry and WR Tyreek Hill are key."
    out = s.sanitize(text)
    assert "Derrick Henry" not in out
    assert "Tyreek Hill" not in out
    assert "Running back" in out or "running back" in out


def test_sanitize_star_leading_scorer():
    s = ArticlePlayerReferenceSanitizer()
    text = "Star LeBron James and leading scorer Kevin Durant."
    out = s.sanitize(text)
    assert "LeBron James" not in out
    assert "Kevin Durant" not in out
    assert "Star" in out or "star" in out


def test_sanitize_name_will():
    s = ArticlePlayerReferenceSanitizer()
    text = "Geno Smith will need to avoid turnovers."
    out = s.sanitize(text)
    assert "Geno Smith" not in out
    assert "The unit will" in out


def test_sanitize_preserves_headings():
    s = ArticlePlayerReferenceSanitizer()
    text = "## Opening Summary\n\nThe Seahawks are led by Geno Smith.\n\n## Matchup Breakdown"
    out = s.sanitize(text)
    assert "## Opening Summary" in out
    assert "## Matchup Breakdown" in out
    assert "led by its core playmakers" in out
    assert "Geno Smith" not in out


def test_sanitize_preserves_unchanged_content():
    s = ArticlePlayerReferenceSanitizer()
    text = "## Best Bets\n\nTake the under. The defense has been stout."
    assert s.sanitize(text) == text


def test_sanitize_multiple_patterns_in_one_paragraph():
    s = ArticlePlayerReferenceSanitizer()
    text = "Led by Geno Smith, the offense relies on QB Geno Smith. Geno Smith will need to deliver."
    out = s.sanitize(text)
    assert "Geno Smith" not in out
    assert "led by its core playmakers" in out or "Led by its core playmakers" in out
    assert "The unit will" in out
