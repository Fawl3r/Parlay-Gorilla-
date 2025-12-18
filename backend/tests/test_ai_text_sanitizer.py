from app.services.ai_text_sanitizer import AiTextSanitizer


def test_sanitizer_removes_bold_markdown():
    s = AiTextSanitizer()
    text = "1. **Ravens @ Bengals** (Odds: +115)\n\n2. **Packers @ Broncos**"
    assert s.sanitize(text) == "Ravens @ Bengals (Odds: +115)\n\nPackers @ Broncos"


def test_sanitizer_removes_bullets_and_stray_asterisks():
    s = AiTextSanitizer()
    text = "- **Leg 1:** Something *weird*\n- Leg 2: Clean"
    assert s.sanitize(text) == "Leg 1: Something weird\n\nLeg 2: Clean"


def test_sanitizer_keeps_negative_odds_and_plus_signs():
    s = AiTextSanitizer()
    text = "- Pick: home (Odds -110)\n- Pick: away (Odds +135)"
    assert s.sanitize(text) == "Pick: home (Odds -110)\n\nPick: away (Odds +135)"





