from __future__ import annotations

from copy import deepcopy

from pg_content_engine.models import XContentItem
from pg_content_engine.rules.shared.banned_phrase_catalog import BannedPhraseCatalog
from pg_content_engine.rules.shared.certainty_phrase_catalog import CertaintyPhraseCatalog
from pg_content_engine.rules.shared.emoji_detector import EmojiDetector
from pg_content_engine.rules.shared.hashtag_extractor import HashtagExtractor
from pg_content_engine.rules.shared.hype_phrase_catalog import HypePhraseCatalog
from pg_content_engine.rules.shared.uppercase_token_detector import UppercaseTokenDetector
from pg_content_engine.rules.x.all_caps_rule import XAllCapsRule
from pg_content_engine.rules.x.banned_phrases_rule import XBannedPhrasesRule
from pg_content_engine.rules.x.compliance_rule import XComplianceRule
from pg_content_engine.rules.x.hashtag_rule import XHashtagRule
from pg_content_engine.rules.x.length_rule import XLengthRule
from pg_content_engine.rules.x.no_emoji_rule import XNoEmojiRule
from pg_content_engine.rules.x.no_hype_rule import XNoHypeRule
from pg_content_engine.rules.x.outcome_certainty_rule import XOutcomeCertaintyRule
from pg_content_engine.rules.x.schedule_rule import XScheduleRule


class XItemFactory:
    def __init__(self) -> None:
        self._base = {
            "id": "pg_x_001",
            "type": "post",
            "topic": "discipline",
            "text": "Calm, direct guidance.",
            "style_tag": "discipline",
            "compliance": {"no_guarantees": True, "no_hype": True, "no_emojis": True},
            "hashtags": [],
            "schedule": {
                "priority": "normal",
                "window": "evening",
                "cadence": "daily",
                "evergreen": True,
                "expiration_hours": None,
            },
            "status": "pending",
        }

    def build(self, overrides: dict) -> dict:
        data = deepcopy(self._base)
        data.update(overrides)
        return data


def test_x_no_emoji_rule_rejects() -> None:
    factory = XItemFactory()
    item = XContentItem.from_dict(factory.build({"text": "No emoji \U0001F642"}))
    rule = XNoEmojiRule(EmojiDetector())
    assert rule.evaluate(item)


def test_x_all_caps_rule_rejects() -> None:
    factory = XItemFactory()
    item = XContentItem.from_dict(factory.build({"text": "THIS is loud"}))
    rule = XAllCapsRule(UppercaseTokenDetector())
    assert rule.evaluate(item)


def test_x_banned_phrases_rule_rejects() -> None:
    factory = XItemFactory()
    item = XContentItem.from_dict(factory.build({"text": "That is free money."}))
    rule = XBannedPhrasesRule(BannedPhraseCatalog())
    assert rule.evaluate(item)


def test_x_outcome_certainty_rule_rejects() -> None:
    factory = XItemFactory()
    item = XContentItem.from_dict(factory.build({"text": "This will win tonight."}))
    rule = XOutcomeCertaintyRule(CertaintyPhraseCatalog())
    assert rule.evaluate(item)


def test_x_no_hype_rule_rejects() -> None:
    factory = XItemFactory()
    item = XContentItem.from_dict(factory.build({"text": "Bet now and act now."}))
    rule = XNoHypeRule(HypePhraseCatalog())
    assert rule.evaluate(item)


def test_x_hashtag_rule_rejects_mismatch() -> None:
    factory = XItemFactory()
    item = XContentItem.from_dict(factory.build({"text": "Calm post #edge", "hashtags": []}))
    rule = XHashtagRule(HashtagExtractor())
    assert rule.evaluate(item)


def test_x_length_rule_rejects_long_text() -> None:
    factory = XItemFactory()
    item = XContentItem.from_dict(factory.build({"text": "x" * 281}))
    rule = XLengthRule()
    assert rule.evaluate(item)


def test_x_schedule_rule_rejects_invalid_expiration() -> None:
    factory = XItemFactory()
    schedule_override = {
        "schedule": {
            "priority": "normal",
            "window": "evening",
            "cadence": "daily",
            "evergreen": True,
            "expiration_hours": 24,
        }
    }
    item = XContentItem.from_dict(factory.build(schedule_override))
    rule = XScheduleRule()
    assert rule.evaluate(item)


def test_x_compliance_rule_rejects_false_flags() -> None:
    factory = XItemFactory()
    item = XContentItem.from_dict(
        factory.build({"compliance": {"no_guarantees": True, "no_hype": False, "no_emojis": True}})
    )
    rule = XComplianceRule()
    assert rule.evaluate(item)
