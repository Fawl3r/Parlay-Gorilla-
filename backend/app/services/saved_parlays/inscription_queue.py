"""Redis-backed queue producer for Solana inscription jobs.

We intentionally keep this minimal and JSON-based so a Node worker can consume it.
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from app.services.redis.redis_client_provider import RedisClientProvider, get_redis_provider

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class InscriptionQueueConfig:
    key: str = "parlay_gorilla:queue:inscribe_custom_parlay"


class InscriptionQueue:
    """Enqueues inscription jobs for background processing."""

    def __init__(
        self,
        *,
        provider: Optional[RedisClientProvider] = None,
        config: Optional[InscriptionQueueConfig] = None,
    ):
        self._provider = provider or get_redis_provider()
        self._config = config or InscriptionQueueConfig()

    def is_available(self) -> bool:
        return self._provider.is_configured()

    async def enqueue_custom_parlay(self, *, saved_parlay_id: str) -> str:
        """
        Enqueue a job to inscribe a custom saved parlay.

        Returns a job_id for logging/tracing (not currently persisted).
        """
        if not self.is_available():
            raise RuntimeError("Redis is not configured (missing REDIS_URL)")

        client = self._provider.get_client()
        job_id = uuid.uuid4().hex
        payload = {
            "job_name": "inscribe_custom_parlay",
            "job_id": job_id,
            "savedParlayId": saved_parlay_id,
            "attempt": 0,
            "enqueued_at": datetime.now(timezone.utc).isoformat(),
        }
        body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        await client.rpush(self._config.key, body)
        return job_id



