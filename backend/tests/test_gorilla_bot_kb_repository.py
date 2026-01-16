"""Tests for Gorilla Bot knowledgebase repository."""

import uuid
import pytest

from app.services.gorilla_bot.kb_repository import GorillaBotKnowledgeRepository


@pytest.mark.asyncio
async def test_upsert_document_populates_id(db):
    repo = GorillaBotKnowledgeRepository(db)

    doc = await repo.upsert_document(
        source_path=f"docs/gorilla-bot/kb/test-{uuid.uuid4()}.md",
        title="Test Doc",
        checksum="abc123",
        source_url=None,
        is_active=True,
    )

    assert doc.id is not None

