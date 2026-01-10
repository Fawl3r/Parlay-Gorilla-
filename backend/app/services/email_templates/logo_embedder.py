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


def embed_logo_as_data_uri(logo_path: Optional[str | Path] = None) -> Optional[str]:
    """
    Read a logo image file and convert it to a base64 data URI.
    
    Args:
        logo_path: Path to the logo image file. If None, tries common locations.
        
    Returns:
        Base64 data URI string (e.g., "data:image/png;base64,...") or None if file not found.
    """
    if logo_path is None:
        # Try to find the logo in common locations
        # First, try relative to backend directory (if frontend is sibling)
        backend_dir = Path(__file__).parent.parent.parent.parent
        possible_paths = [
            backend_dir.parent / "frontend" / "public" / "images" / "newlogo.png",
            backend_dir / "static" / "images" / "newlogo.png",
            Path("frontend/public/images/newlogo.png"),
            Path("static/images/newlogo.png"),
        ]
        
        for path in possible_paths:
            if path.exists() and path.is_file():
                logo_path = path
                break
        else:
            logger.warning("Logo file not found in common locations. Using URL fallback.")
            return None
    
    try:
        logo_file = Path(logo_path)
        if not logo_file.exists() or not logo_file.is_file():
            logger.warning(f"Logo file not found: {logo_path}")
            return None
        
        # Read the image file
        image_data = logo_file.read_bytes()
        
        # Determine MIME type from file extension
        ext = logo_file.suffix.lower()
        mime_types = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        mime_type = mime_types.get(ext, "image/png")
        
        # Encode to base64
        base64_data = base64.b64encode(image_data).decode("utf-8")
        
        # Return as data URI
        return f"data:{mime_type};base64,{base64_data}"
    except Exception as e:
        logger.warning(f"Failed to embed logo image: {e}")
        return None


def get_logo_src(logo_url: str, embedded_data_uri: Optional[str] = None) -> str:
    """
    Get the image src attribute, preferring embedded data URI over URL.
    
    Args:
        logo_url: Fallback URL for the logo
        embedded_data_uri: Optional base64 data URI for embedded image
        
    Returns:
        Image src attribute value (data URI if available, otherwise URL)
    """
    if embedded_data_uri:
        return embedded_data_uri
    return logo_url

