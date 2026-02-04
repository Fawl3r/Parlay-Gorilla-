"""
Lightweight memory telemetry for parlay and custom-parlay routes.

Logs RSS (MB) before/after each request and on exceptions for:
- /api/parlay/suggest
- /api/parlay/*
- /api/custom-parlay/*

Use for diagnosing OOM on 512MB Render instances.
"""

import logging
import os
import time
from typing import Callable

import psutil
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

# Path prefixes that get memory logging (avoid log spam elsewhere)
_MEMORY_LOG_PREFIXES = ("/api/parlay/", "/api/custom-parlay/")


def _should_log_memory(path: str) -> bool:
    return path.startswith(_MEMORY_LOG_PREFIXES)


def _rss_mb() -> float:
    try:
        return psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
    except Exception:
        return 0.0


class MemoryLogMiddleware(BaseHTTPMiddleware):
    """Log RSS memory before/after for parlay-related paths only."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path or ""
        if not _should_log_memory(path):
            return await call_next(request)

        method = request.method or ""
        rss_before_mb = _rss_mb()
        start = time.perf_counter()
        status = 500
        try:
            response = await call_next(request)
            status = getattr(response, "status_code", 500)
            return response
        except Exception:
            status = 500
            raise
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            rss_after_mb = _rss_mb()
            delta_mb = rss_after_mb - rss_before_mb
            logger.info(
                "memory_telemetry path=%s method=%s status=%s duration_ms=%.0f "
                "rss_before_mb=%.1f rss_after_mb=%.1f delta_mb=%.1f",
                path,
                method,
                status,
                duration_ms,
                rss_before_mb,
                rss_after_mb,
                delta_mb,
            )
