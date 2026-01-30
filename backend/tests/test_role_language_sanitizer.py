"""Unit tests for RoleLanguageSanitizer."""

from app.services.analysis.role_language_sanitizer import RoleLanguageSanitizer


def test_sanitize_empty_or_none():
    s = RoleLanguageSanitizer()
    out, count = s.sanitize("")
    assert out == ""
    assert count == 0
    out, count = s.sanitize(None)
    assert out == ""
    assert count == 0


def test_sanitize_his_ability_removes_pronouns():
    s = RoleLanguageSanitizer()
    text = "His ability to distribute the ball effectively has been key to Seattle's success."
    out, count = s.sanitize(text)
    assert "his" not in out.lower()
    assert "her" not in out.lower()
    assert "him" not in out.lower()
    assert "he " not in out.lower() or " he " not in out
    assert "she " not in out.lower() or " she " not in out
    assert "the offense's ability to" in out or "offense's" in out
    assert count >= 1


def test_sanitize_headings_unchanged():
    s = RoleLanguageSanitizer()
    text = "## Opening Summary\n\nHis ability to lead.\n\n## Matchup Breakdown"
    out, _ = s.sanitize(text)
    assert "## Opening Summary" in out
    assert "## Matchup Breakdown" in out
    assert "his" not in out.lower()


def test_sanitize_signal_caller_neutralized():
    s = RoleLanguageSanitizer()
    text = "The signal-caller has been sharp. The signal-caller's leadership matters."
    out, count = s.sanitize(text)
    assert "the quarterback" in out.lower() or "quarterback" in out.lower()
    assert "offensive leadership" in out or "quarterback play" in out
    assert count >= 1


def test_sanitize_star_player_neutralized():
    s = RoleLanguageSanitizer()
    text = "The star player will need to step up."
    out, count = s.sanitize(text)
    assert "the star player" not in out.lower()
    assert "key playmakers" in out
    assert count >= 1


def test_sanitize_no_player_names_introduced():
    s = RoleLanguageSanitizer()
    text = "He has been good. His performance is key. She will start."
    out, _ = s.sanitize(text)
    # Replacements are unit/team phrasing only; no proper-name patterns
    assert "the unit" in out or "the unit's" in out
    assert "his" not in out.lower()
    assert "her" not in out.lower()
    assert "she " not in out.lower()
    assert " he " not in out
