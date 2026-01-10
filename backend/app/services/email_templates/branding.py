from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urljoin

from .logo_embedder import embed_logo_as_data_uri, get_logo_src


@dataclass(frozen=True)
class EmailBranding:
    """
    Visual + identity constants used across transactional emails.

    We keep this separate so templates stay small and consistent, and so we can
    inject branding in tests (no global config coupling).
    """

    app_name: str
    logo_url: str
    logo_data_uri: str | None  # Embedded base64 image for email clients
    primary_neon: str
    background: str

    @property
    def logo_src(self) -> str:
        """Get the image src attribute, preferring embedded data URI over URL."""
        return get_logo_src(self.logo_url, self.logo_data_uri)

    @staticmethod
    def parlay_gorilla(app_base_url: str, logo_url_override: str | None = None) -> "EmailBranding":
        base = (app_base_url or "").strip()
        if not base:
            # Safe local fallback; caller should prefer passing settings.app_url.
            base = "http://localhost:3000"
        if not base.endswith("/"):
            base = f"{base}/"

        override = (logo_url_override or "").strip()
        if override:
            # If a relative URL is provided, anchor it to APP_URL.
            logo_url = urljoin(base, override)
        else:
            logo_url = urljoin(base, "images/newlogo.png")
        
        # Try to embed the logo as base64 for better email client compatibility
        logo_data_uri = embed_logo_as_data_uri()
        
        return EmailBranding(
            app_name="Parlay Gorilla",
            logo_url=logo_url,
            logo_data_uri=logo_data_uri,
            primary_neon="#00ff7f",
            background="#050508",
        )


