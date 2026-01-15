"""
OpenAI client wrapper for Gorilla Bot.
"""

from __future__ import annotations

import asyncio
from typing import List, Dict, Any

from openai import AsyncOpenAI

from app.core.config import settings


class GorillaBotOpenAIClient:
    """Thin wrapper around OpenAI SDK with Gorilla Bot defaults."""

    def __init__(self):
        self._enabled = bool(settings.openai_enabled) and bool(settings.openai_api_key)
        self._client = AsyncOpenAI(api_key=settings.openai_api_key) if self._enabled else None
        self._chat_model = settings.gorilla_bot_model
        self._embedding_model = settings.gorilla_bot_embedding_model
        self._chat_timeout = float(settings.gorilla_bot_chat_timeout_seconds)
        self._embedding_timeout = float(settings.gorilla_bot_embedding_timeout_seconds)

    @property
    def enabled(self) -> bool:
        return self._enabled

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not self._enabled or not self._client:
            raise RuntimeError("OpenAI is disabled for Gorilla Bot embeddings.")
        if not texts:
            return []

        response = await asyncio.wait_for(
            self._client.embeddings.create(
                model=self._embedding_model,
                input=texts,
            ),
            timeout=self._embedding_timeout,
        )
        return [item.embedding for item in response.data]

    async def chat_completion(self, messages: List[Dict[str, Any]], max_tokens: int) -> str:
        if not self._enabled or not self._client:
            raise RuntimeError("OpenAI is disabled for Gorilla Bot chat.")

        response = await asyncio.wait_for(
            self._client.chat.completions.create(
                model=self._chat_model,
                messages=messages,
                temperature=0.2,
                max_tokens=max_tokens,
            ),
            timeout=self._chat_timeout,
        )
        return (response.choices[0].message.content or "").strip()
