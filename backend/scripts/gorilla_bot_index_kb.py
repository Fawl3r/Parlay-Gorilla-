"""
CLI script to index Gorilla Bot knowledgebase documents.

Usage:
  python scripts/gorilla_bot_index_kb.py
  python scripts/gorilla_bot_index_kb.py --force
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.database.session import AsyncSessionLocal
from app.services.gorilla_bot.kb_chunker import GorillaBotChunker
from app.services.gorilla_bot.kb_indexer import GorillaBotKnowledgeBaseIndexer
from app.services.gorilla_bot.kb_repository import GorillaBotKnowledgeRepository
from app.services.gorilla_bot.openai_client import GorillaBotOpenAIClient


class GorillaBotIndexCommand:
    def __init__(self, force: bool):
        self._force = force

    async def run(self) -> int:
        async with AsyncSessionLocal() as db:
            indexer = GorillaBotKnowledgeBaseIndexer(
                db=db,
                openai_client=GorillaBotOpenAIClient(),
                chunker=GorillaBotChunker(),
                repository=GorillaBotKnowledgeRepository(db),
            )
            summary = await indexer.index_from_settings(force=self._force)

        print("Gorilla Bot KB index complete.")
        print(f"Documents: {summary.total_documents}")
        print(f"Indexed: {summary.indexed_documents}")
        print(f"Skipped: {summary.skipped_documents}")
        print(f"Chunks: {summary.total_chunks}")
        return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Index Gorilla Bot knowledgebase.")
    parser.add_argument("--force", action="store_true", help="Reindex all documents.")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    command = GorillaBotIndexCommand(force=bool(args.force))
    return asyncio.run(command.run())


if __name__ == "__main__":
    raise SystemExit(main())
