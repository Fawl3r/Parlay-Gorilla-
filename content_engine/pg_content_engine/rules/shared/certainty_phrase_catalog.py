from __future__ import annotations


class CertaintyPhraseCatalog:
    def phrases(self) -> list[str]:
        return [
            "will win",
            "can't miss",
            "can’t miss",
            "cannot miss",
            "guarantee",
            "guaranteed",
            "sure thing",
            "no doubt",
            "can't lose",
            "can’t lose",
        ]

    def regex_patterns(self) -> list[str]:
        return [r"\b100\s*%\b"]
