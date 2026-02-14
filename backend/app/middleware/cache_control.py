"""
Response Cache-Control middleware: avoid stale /sports and game/analysis state at CDN.

Critical paths get short TTL or no-store so Cloudflare does not serve stale
season/break/offseason state. Static-ish paths can keep default or longer TTL.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Path prefixes that must not be cached long (sport state, games, analysis, game detail).
# Prevents Cloudflare from serving stale break/offseason state (e.g. preseason unlock day).
NO_STALE_PREFIXES = ("/api/sports", "/api/games", "/api/analysis", "/api/game")
# Short TTL so CDN revalidates often; keeps /api/sports fresh when is_enabled flips.
CACHE_CONTROL_DYNAMIC = "max-age=60, must-revalidate"
CACHE_CONTROL_NO_STORE = "no-store"


class CacheControlMiddleware(BaseHTTPMiddleware):
    """Set Cache-Control on responses by path prefix."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        path = request.url.path
        if path.startswith(NO_STALE_PREFIXES):
            response.headers["Cache-Control"] = CACHE_CONTROL_DYNAMIC
        return response
