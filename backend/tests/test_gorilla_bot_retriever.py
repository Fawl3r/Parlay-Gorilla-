"""Tests for Gorilla Bot retriever ordering."""

import pytest

from app.models.gorilla_bot_kb_document import GorillaBotKnowledgeDocument
from app.models.gorilla_bot_kb_chunk import GorillaBotKnowledgeChunk
from app.services.gorilla_bot.kb_retriever import GorillaBotKnowledgeRetriever


class FakeOpenAIClient:
    enabled = True

    async def embed_texts(self, texts):
        _ = texts
        return [[1.0, 0.0]]


@pytest.mark.asyncio
async def test_retriever_orders_by_similarity(db):
    document = GorillaBotKnowledgeDocument(
        source_path="docs/sample.md",
        title="Sample Doc",
        checksum="abc123",
        is_active=True,
    )
    db.add(document)
    await db.flush()

    chunk_a = GorillaBotKnowledgeChunk(
        document_id=document.id,
        chunk_index=0,
        content="Chunk A",
        embedding_json=[1.0, 0.0],
    )
    chunk_b = GorillaBotKnowledgeChunk(
        document_id=document.id,
        chunk_index=1,
        content="Chunk B",
        embedding_json=[0.0, 1.0],
    )
    db.add_all([chunk_a, chunk_b])
    await db.commit()

    retriever = GorillaBotKnowledgeRetriever(FakeOpenAIClient())
    results = await retriever.retrieve("does not matter")

    assert results
    assert results[0].content == "Chunk A"
