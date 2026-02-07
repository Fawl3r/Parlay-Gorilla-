"""
Lightweight memory instrumentation for parlay generation (OOM diagnosis on 512MB instances).

Uses psutil if available; fallback to resource (Unix) or /proc/self/status on Linux.
Does not add new dependencies (psutil is already in requirements).
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict


def get_rss_mb() -> float:
    """Return current process RSS in MB. Safe on Windows (psutil) and Linux."""
    try:
        import psutil
        return psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
    except Exception:
        pass
    try:
        import resource
        usage = resource.getrusage(resource.RUSAGE_SELF)
        return getattr(usage, "ru_maxrss", 0) / 1024.0  # Linux returns KB
    except Exception:
        pass
    try:
        with open("/proc/self/status", "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    parts = line.split()
                    if len(parts) >= 2:
                        return float(parts[1]) / 1024.0  # kB -> MB
                    break
    except Exception:
        pass
    return 0.0


def log_mem(logger: logging.Logger, label: str, extra: Dict[str, Any] | None = None) -> None:
    """Log current RSS (MB) with a label and optional extra fields for correlation."""
    rss_mb = get_rss_mb()
    extra_str = " ".join(f"{k}={v}" for k, v in (extra or {}).items())
    logger.info("memory %s rss_mb=%.1f %s", label, rss_mb, extra_str)
