"""
Run Alembic migrations under a Postgres advisory lock so only one process migrates
when multiple API replicas start. Safe for scaling; no per-request overhead.

Usage:
  python -m app.ops.migrate_with_lock

Exits 0 on success, non-zero on failure. Reads DATABASE_URL from env.
Optional: MIGRATION_LOCK_TIMEOUT_SECONDS (default 600) to cap wait for lock.
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
import time

import psycopg2

# Fixed key for migration lock; same across all replicas.
LOCK_KEY = 987654321

# Logging: structured messages, no secrets (do not log DATABASE_URL).
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s [%(name)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("app.ops.migrate_with_lock")


def _get_sync_postgres_url() -> str:
    """Read DATABASE_URL from env and convert to sync Postgres URL for psycopg2."""
    raw = (os.environ.get("DATABASE_URL") or "").strip()
    if not raw:
        raise ValueError("DATABASE_URL is required")
    url = (
        raw.replace("postgresql+asyncpg://", "postgresql://", 1)
        .replace("postgres://", "postgresql://", 1)
    )
    if "sqlite" in url:
        raise ValueError("Migration lock requires PostgreSQL; DATABASE_URL is SQLite")
    return url


def _acquire_lock_blocking(conn) -> None:
    """Acquire advisory lock; blocks until available."""
    with conn.cursor() as cur:
        cur.execute("SELECT pg_advisory_lock(%s)", (LOCK_KEY,))


def _try_acquire_lock(conn) -> bool:
    """Try to acquire advisory lock; returns True if acquired, False otherwise."""
    with conn.cursor() as cur:
        cur.execute("SELECT pg_try_advisory_lock(%s)", (LOCK_KEY,))
        row = cur.fetchone()
        return row is not None and row[0] is True


def _release_lock(conn) -> None:
    """Release advisory lock (best-effort)."""
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT pg_advisory_unlock(%s)", (LOCK_KEY,))
    except Exception as e:
        logger.warning("Lock release reported: %s", e)


def _run_alembic_upgrade(cwd: str) -> int:
    """Shell out to alembic upgrade head. Returns exit code."""
    env = os.environ.copy()
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=cwd,
        env=env,
        capture_output=False,
    )
    return result.returncode


def _backend_root() -> str:
    """Directory containing alembic.ini (backend root)."""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main() -> int:
    """Acquire lock, run migrations, release lock. Exit 0 on success."""
    timeout_seconds: int | None = None
    raw_timeout = os.environ.get("MIGRATION_LOCK_TIMEOUT_SECONDS", "").strip()
    if raw_timeout:
        try:
            timeout_seconds = int(raw_timeout)
            if timeout_seconds <= 0:
                timeout_seconds = None
        except ValueError:
            logger.warning("Invalid MIGRATION_LOCK_TIMEOUT_SECONDS, ignoring")

    try:
        db_url = _get_sync_postgres_url()
    except ValueError as e:
        logger.error("%s", e)
        return 1

    backend_root = _backend_root()
    conn = None

    try:
        logger.info("acquiring migration lock…")
        conn = psycopg2.connect(db_url)
        conn.autocommit = True

        if timeout_seconds is not None:
            deadline = time.monotonic() + timeout_seconds
            while not _try_acquire_lock(conn):
                if time.monotonic() >= deadline:
                    logger.error("migration lock timeout after %s seconds", timeout_seconds)
                    return 1
                time.sleep(2)
        else:
            _acquire_lock_blocking(conn)

        logger.info("lock acquired")
        logger.info("running alembic upgrade head…")
        code = _run_alembic_upgrade(backend_root)
        if code != 0:
            logger.error("alembic upgrade head exited with code %s", code)
            return code
        logger.info("migration complete")
        return 0
    except psycopg2.OperationalError as e:
        logger.error("database unreachable: %s", e)
        return 1
    except Exception as e:
        logger.exception("migration failed: %s", e)
        return 1
    finally:
        if conn:
            logger.info("lock released")
            _release_lock(conn)
            try:
                conn.close()
            except Exception:
                pass


if __name__ == "__main__":
    sys.exit(main())
