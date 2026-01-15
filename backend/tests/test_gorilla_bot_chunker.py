"""Tests for Gorilla Bot chunking."""

from app.services.gorilla_bot.kb_chunker import GorillaBotChunker


def test_chunker_respects_overlap():
    chunker = GorillaBotChunker(max_tokens=10, overlap_tokens=2)
    text = " ".join([f"token{i}" for i in range(25)])

    chunks = chunker.chunk(text)

    assert len(chunks) == 3
    assert chunks[0].token_estimate == 10
    assert chunks[1].token_estimate == 10
    assert chunks[2].token_estimate == 9
    assert chunks[1].content.split(" ")[0] == "token8"
