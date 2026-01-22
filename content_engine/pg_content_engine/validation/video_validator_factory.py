from __future__ import annotations

from ..rules.shared.banned_phrase_catalog import BannedPhraseCatalog
from ..rules.shared.certainty_phrase_catalog import CertaintyPhraseCatalog
from ..rules.shared.emoji_detector import EmojiDetector
from ..rules.shared.hype_phrase_catalog import HypePhraseCatalog
from ..rules.shared.uppercase_token_detector import UppercaseTokenDetector
from ..rules.shared.word_counter import WordCounter
from ..rules.video.all_caps_rule import VideoAllCapsRule
from ..rules.video.banned_phrases_rule import VideoBannedPhrasesRule
from ..rules.video.compliance_rule import VideoComplianceRule
from ..rules.video.duration_rule import VideoDurationRule
from ..rules.video.no_emoji_rule import VideoNoEmojiRule
from ..rules.video.no_hype_rule import VideoNoHypeRule
from ..rules.video.outcome_certainty_rule import VideoOutcomeCertaintyRule
from ..rules.video.schedule_rule import VideoScheduleRule
from .video_validator import VideoValidator


class VideoValidatorFactory:
    def build(self) -> VideoValidator:
        emoji_detector = EmojiDetector()
        uppercase_detector = UppercaseTokenDetector()
        word_counter = WordCounter()
        banned_catalog = BannedPhraseCatalog()
        certainty_catalog = CertaintyPhraseCatalog()
        hype_catalog = HypePhraseCatalog()
        rules = [
            VideoComplianceRule(),
            VideoNoEmojiRule(emoji_detector),
            VideoAllCapsRule(uppercase_detector),
            VideoBannedPhrasesRule(banned_catalog),
            VideoOutcomeCertaintyRule(certainty_catalog),
            VideoNoHypeRule(hype_catalog),
            VideoDurationRule(word_counter),
            VideoScheduleRule(),
        ]
        return VideoValidator(rules)
