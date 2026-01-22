from __future__ import annotations

from ..rules.shared.banned_phrase_catalog import BannedPhraseCatalog
from ..rules.shared.certainty_phrase_catalog import CertaintyPhraseCatalog
from ..rules.shared.emoji_detector import EmojiDetector
from ..rules.shared.hashtag_extractor import HashtagExtractor
from ..rules.shared.hype_phrase_catalog import HypePhraseCatalog
from ..rules.shared.uppercase_token_detector import UppercaseTokenDetector
from ..rules.x.all_caps_rule import XAllCapsRule
from ..rules.x.banned_phrases_rule import XBannedPhrasesRule
from ..rules.x.compliance_rule import XComplianceRule
from ..rules.x.hashtag_rule import XHashtagRule
from ..rules.x.length_rule import XLengthRule
from ..rules.x.no_emoji_rule import XNoEmojiRule
from ..rules.x.no_hype_rule import XNoHypeRule
from ..rules.x.outcome_certainty_rule import XOutcomeCertaintyRule
from ..rules.x.schedule_rule import XScheduleRule
from .x_validator import XValidator


class XValidatorFactory:
    def build(self) -> XValidator:
        emoji_detector = EmojiDetector()
        uppercase_detector = UppercaseTokenDetector()
        hashtag_extractor = HashtagExtractor()
        banned_catalog = BannedPhraseCatalog()
        certainty_catalog = CertaintyPhraseCatalog()
        hype_catalog = HypePhraseCatalog()
        rules = [
            XComplianceRule(),
            XNoEmojiRule(emoji_detector),
            XAllCapsRule(uppercase_detector),
            XBannedPhrasesRule(banned_catalog),
            XOutcomeCertaintyRule(certainty_catalog),
            XNoHypeRule(hype_catalog),
            XHashtagRule(hashtag_extractor),
            XLengthRule(),
            XScheduleRule(),
        ]
        return XValidator(rules)
