from __future__ import annotations

from copy import deepcopy

from pg_content_engine.models import VideoContentItem
from pg_content_engine.rules.shared.banned_phrase_catalog import BannedPhraseCatalog
from pg_content_engine.rules.shared.certainty_phrase_catalog import CertaintyPhraseCatalog
from pg_content_engine.rules.shared.emoji_detector import EmojiDetector
from pg_content_engine.rules.shared.hype_phrase_catalog import HypePhraseCatalog
from pg_content_engine.rules.shared.uppercase_token_detector import UppercaseTokenDetector
from pg_content_engine.rules.shared.word_counter import WordCounter
from pg_content_engine.rules.video.all_caps_rule import VideoAllCapsRule
from pg_content_engine.rules.video.banned_phrases_rule import VideoBannedPhrasesRule
from pg_content_engine.rules.video.compliance_rule import VideoComplianceRule
from pg_content_engine.rules.video.duration_rule import VideoDurationRule
from pg_content_engine.rules.video.no_emoji_rule import VideoNoEmojiRule
from pg_content_engine.rules.video.no_hype_rule import VideoNoHypeRule
from pg_content_engine.rules.video.outcome_certainty_rule import VideoOutcomeCertaintyRule
from pg_content_engine.rules.video.schedule_rule import VideoScheduleRule


class VideoItemFactory:
    def __init__(self) -> None:
        self._base = {
            "id": "pg_v_001",
            "type": "video_script",
            "topic": "discipline",
            "script": "Short, calm statement about discipline and risk.",
            "format_tag": "discipline_reminder",
            "compliance": {"no_guarantees": True, "no_hype": True, "no_emojis": True},
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


def test_video_no_emoji_rule_rejects() -> None:
    factory = VideoItemFactory()
    item = VideoContentItem.from_dict(factory.build({"script": "No emoji \U0001F642"}))
    rule = VideoNoEmojiRule(EmojiDetector())
    assert rule.evaluate(item)


def test_video_all_caps_rule_rejects() -> None:
    factory = VideoItemFactory()
    item = VideoContentItem.from_dict(factory.build({"script": "THIS is loud."}))
    rule = VideoAllCapsRule(UppercaseTokenDetector())
    assert rule.evaluate(item)


def test_video_banned_phrases_rule_rejects() -> None:
    factory = VideoItemFactory()
    item = VideoContentItem.from_dict(factory.build({"script": "That's easy money."}))
    rule = VideoBannedPhrasesRule(BannedPhraseCatalog())
    assert rule.evaluate(item)


def test_video_outcome_certainty_rule_rejects() -> None:
    factory = VideoItemFactory()
    item = VideoContentItem.from_dict(factory.build({"script": "This will win today."}))
    rule = VideoOutcomeCertaintyRule(CertaintyPhraseCatalog())
    assert rule.evaluate(item)


def test_video_no_hype_rule_rejects() -> None:
    factory = VideoItemFactory()
    item = VideoContentItem.from_dict(factory.build({"script": "Bet now, act now."}))
    rule = VideoNoHypeRule(HypePhraseCatalog())
    assert rule.evaluate(item)


def test_video_duration_rule_rejects_too_short() -> None:
    factory = VideoItemFactory()
    item = VideoContentItem.from_dict(factory.build({"script": "Too short."}))
    rule = VideoDurationRule(WordCounter())
    assert rule.evaluate(item)


def test_video_schedule_rule_rejects_invalid_expiration() -> None:
    factory = VideoItemFactory()
    schedule_override = {
        "schedule": {
            "priority": "normal",
            "window": "evening",
            "cadence": "daily",
            "evergreen": False,
            "expiration_hours": None,
        }
    }
    item = VideoContentItem.from_dict(factory.build(schedule_override))
    rule = VideoScheduleRule()
    assert rule.evaluate(item)


def test_video_compliance_rule_rejects_false_flags() -> None:
    factory = VideoItemFactory()
    item = VideoContentItem.from_dict(
        factory.build({"compliance": {"no_guarantees": True, "no_hype": False, "no_emojis": True}})
    )
    rule = VideoComplianceRule()
    assert rule.evaluate(item)
