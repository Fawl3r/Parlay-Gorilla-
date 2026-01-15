"""
Utility for embedding logo images in email templates.

This module provides functionality to embed logo images as base64 data URIs
in email HTML, ensuring images display even when email clients block external images.
"""

from __future__ import annotations

import base64
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class EmailLogoEmbedder:
    """Encode logo images as data URIs when size limits allow."""

    DEFAULT_MAX_INLINE_BYTES = 12_000

    def __init__(self, max_inline_bytes: int = DEFAULT_MAX_INLINE_BYTES) -> None:
        self._max_inline_bytes = max(0, int(max_inline_bytes))

    def embed_logo_as_data_uri(self, logo_path: Optional[str | Path] = None) -> Optional[str]:
        """
        Read a logo image file and convert it to a base64 data URI.

        Args:
            logo_path: Path to the logo image file. If None, tries common locations.

        Returns:
            Base64 data URI string (e.g., "data:image/png;base64,...") or None if disabled/missing.
        """
        resolved_path = self._resolve_logo_path(logo_path)
        if not resolved_path:
            return None
        if not self._is_inline_size_allowed(resolved_path):
            return None
        return self._encode_as_data_uri(resolved_path)

    def _resolve_logo_path(self, logo_path: Optional[str | Path]) -> Optional[Path]:
        if logo_path is not None:
            resolved = Path(logo_path)
            if resolved.exists() and resolved.is_file():
                return resolved
            logger.warning(f"Logo file not found: {resolved}")
            return None

        backend_dir = Path(__file__).parent.parent.parent.parent
        possible_paths = [
            backend_dir.parent / "frontend" / "public" / "images" / "newlogo.png",
            backend_dir / "static" / "images" / "newlogo.png",
            Path("frontend/public/images/newlogo.png"),
            Path("static/images/newlogo.png"),
        ]

        for path in possible_paths:
            if path.exists() and path.is_file():
                return path

        logger.warning("Logo file not found in common locations. Using URL fallback.")
        return None

    def _is_inline_size_allowed(self, logo_file: Path) -> bool:
        if self._max_inline_bytes <= 0:
            logger.info("Inline logo embedding disabled by size limit. Using URL fallback.")
            return False

        file_size = logo_file.stat().st_size
        if file_size > self._max_inline_bytes:
            logger.info(
                "Logo file too large for inline embedding (size=%s bytes, max=%s). Using URL fallback.",
                file_size,
                self._max_inline_bytes,
            )
            return False
        return True

    @staticmethod
    def _encode_as_data_uri(logo_file: Path) -> Optional[str]:
        try:
            image_data = logo_file.read_bytes()
        except Exception as exc:
            logger.warning(f"Failed to read logo image: {exc}")
            return None

        ext = logo_file.suffix.lower()
        mime_types = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        mime_type = mime_types.get(ext, "image/png")
        base64_data = base64.b64encode(image_data).decode("utf-8")
        return f"data:{mime_type};base64,{base64_data}"

