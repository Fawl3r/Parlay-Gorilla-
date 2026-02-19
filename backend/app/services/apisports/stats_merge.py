"""
Stats merge policy: raw (on-demand) team stats override standings-derived.
Only fill missing values from fallback; never overwrite existing primary values.
"""

from __future__ import annotations

from typing import Any, Dict


def merge_stats(primary: Dict[str, Any], fallback: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge primary (raw team stats) with fallback (standings-derived).
    Precedence: primary overrides. Only keys missing in primary are filled from fallback.
    Never overwrite existing primary values.
    """
    out: Dict[str, Any] = dict(primary)
    for k, v in fallback.items():
        if k not in out and v is not None:
            out[k] = v
    return out
