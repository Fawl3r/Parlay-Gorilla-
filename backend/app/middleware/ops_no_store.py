"""
Ensure all /ops debug endpoints are never cached by CDN, browser, or proxies.

Prevents stale debug data and avoids leaking internal state via caches.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

OPS_PATH_PREFIX = "/ops"
CACHE_CONTROL_NO_STORE = "no-store, no-cache, must-revalidate, max-age=0"
PRAGMA_NO_CACHE = "no-cache"


class OpsNoStoreMiddleware(BaseHTTPMiddleware):
    """Add Cache-Control and Pragma no-store to every response under /ops."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        if request.url.path.startswith(OPS_PATH_PREFIX):
            response.headers["Cache-Control"] = CACHE_CONTROL_NO_STORE
            response.headers["Pragma"] = PRAGMA_NO_CACHE
        return response
