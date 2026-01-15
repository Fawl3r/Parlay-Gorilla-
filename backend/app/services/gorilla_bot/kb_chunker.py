"""
Chunking utilities for Gorilla Bot knowledgebase.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class GorillaBotChunk:
    index: int
    content: str
    token_estimate: int


class GorillaBotChunker:
    """Split documents into overlapping chunks for semantic search."""

    def __init__(self, max_tokens: int = 320, overlap_tokens: int = 60):
        self._max_tokens = max(50, int(max_tokens))
        self._overlap_tokens = max(0, min(int(overlap_tokens), self._max_tokens - 1))

    def chunk(self, text: str) -> List[GorillaBotChunk]:
        normalized = self._normalize(text)
        tokens = self._tokenize(normalized)
        if not tokens:
            return []

        chunks: List[GorillaBotChunk] = []
        start = 0
        index = 0
        step = max(1, self._max_tokens - self._overlap_tokens)

        while start < len(tokens):
            end = min(len(tokens), start + self._max_tokens)
            window = tokens[start:end]
            content = self._detokenize(window)
            chunks.append(GorillaBotChunk(index=index, content=content, token_estimate=len(window)))
            index += 1
            start += step

        return chunks

    def _normalize(self, text: str) -> str:
        return " ".join((text or "").replace("\r", " ").replace("\n", " ").split())

    def _tokenize(self, text: str) -> List[str]:
        return [token for token in text.split(" ") if token]

    def _detokenize(self, tokens: List[str]) -> str:
        return " ".join(tokens).strip()
