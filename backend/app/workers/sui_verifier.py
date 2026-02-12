"""
Pattern A SUI verification worker: always-on DB-polling loop.

Claims queued verification records atomically, creates on-chain proof via SUI,
updates status to confirmed or failed. Idempotent and restart-safe.
Run with: python -m app.workers.sui_verifier
"""

from __future__ import annotations

import logging
import os
import random
import signal
import sys
import time
from dataclasses import dataclass
from typing import Any, Optional

# Ensure backend app is on path when run as __main__
if __name__ == "__main__":
    backend_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if backend_root not in sys.path:
        sys.path.insert(0, backend_root)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
logger = logging.getLogger("sui_verifier")

# Config from env (same as Render worker)
POLL_INTERVAL_SEC = int(os.environ.get("VERIFIER_POLL_INTERVAL_SEC", "15"))
HEARTBEAT_INTERVAL_SEC = int(os.environ.get("VERIFIER_HEARTBEAT_INTERVAL_SEC", "60"))
PROCESSING_TIMEOUT_SEC = int(os.environ.get("VERIFIER_PROCESSING_TIMEOUT_SEC", "900"))  # 15 min
MAX_VERIFICATION_ATTEMPTS = int(os.environ.get("VERIFICATION_MAX_ATTEMPTS", "5"))
BACKOFF_BASE_SEC = float(os.environ.get("VERIFIER_BACKOFF_BASE_SEC", "2.0"))
BACKOFF_MAX_SEC = float(os.environ.get("VERIFIER_BACKOFF_MAX_SEC", "120.0"))


@dataclass
class ClaimedRecord:
    id: str
    saved_parlay_id: Optional[str]
    data_hash: str
    created_at: Any
    attempt: int = 0


def _get_sync_database_url() -> str:
    url = (os.environ.get("DATABASE_URL") or "").strip()
    if not url:
        raise ValueError("DATABASE_URL is required")
    for prefix in ("postgresql+asyncpg://", "postgresql://", "postgres://"):
        if url.startswith(prefix):
            return url.replace("postgresql+asyncpg://", "postgresql://", 1).replace("postgres://", "postgresql://", 1)
    return url


def _claim_one(conn) -> Optional[ClaimedRecord]:
    """Atomically claim one queued record (or release stuck processing)."""
    with conn.cursor() as cur:
        # Release stuck processing rows so they can be retried
        cur.execute(
            """
            UPDATE verification_records
            SET status = 'queued', processing_started_at = NULL, error = 'released (stuck)'
            WHERE status = 'processing'
              AND processing_started_at IS NOT NULL
              AND processing_started_at < now() - (%s * interval '1 second')
            """,
            (PROCESSING_TIMEOUT_SEC,),
        )
        conn.commit()

        cur.execute(
            """
            WITH candidate AS (
                SELECT id FROM verification_records
                WHERE status = 'queued'
                ORDER BY created_at ASC
                LIMIT 1
                FOR UPDATE SKIP LOCKED
            )
            UPDATE verification_records v
            SET status = 'processing', processing_started_at = now()
            FROM candidate c
            WHERE v.id = c.id
            RETURNING v.id, v.saved_parlay_id, v.data_hash, v.created_at
            """
        )
        row = cur.fetchone()
        conn.commit()
        if not row:
            return None
        return ClaimedRecord(
            id=str(row[0]),
            saved_parlay_id=str(row[1]) if row[1] else None,
            data_hash=str(row[2]),
            created_at=row[3],
        )


def _mark_confirmed(conn, record_id: str, tx_digest: str, object_id: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE verification_records
            SET status = 'confirmed', tx_digest = %s, object_id = %s,
                confirmed_at = now(), error = NULL, processing_started_at = NULL
            WHERE id = %s
            """,
            (tx_digest, object_id, record_id),
        )
        conn.commit()


def _mark_failed(conn, record_id: str, error_message: str) -> None:
    err = (error_message or "")[:500]
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE verification_records
            SET status = 'failed', error = %s, processing_started_at = NULL
            WHERE id = %s
            """,
            (err, record_id),
        )
        conn.commit()


def _set_last_error(conn, record_id: str, error_message: str) -> None:
    err = (error_message or "")[:500]
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE verification_records SET error = %s WHERE id = %s",
            (err, record_id),
        )
        conn.commit()


def _run_one_cycle(conn, sui_rpc_url: str, sui_private_key: str, package_id: str, module_name: str, function_name: str) -> bool:
    """Claim one record, verify on SUI, update DB. Returns True if a job was processed."""
    from app.services.verification_records.sui_proof_client import create_proof, ProofCreationResult

    claimed = _claim_one(conn)
    if not claimed:
        return False

    record_id = claimed.id
    saved_parlay_id = claimed.saved_parlay_id or ""
    data_hash = claimed.data_hash
    created_at = claimed.created_at
    created_ts = 0
    if created_at and hasattr(created_at, "timestamp"):
        created_ts = int(created_at.timestamp())

    start_ms = time.time() * 1000
    try:
        result: ProofCreationResult = create_proof(
            data_hash_hex=data_hash,
            created_at_seconds=created_ts,
            rpc_url=sui_rpc_url,
            private_key=sui_private_key,
            package_id=package_id,
            module_name=module_name,
            function_name=function_name,
        )
        duration_ms = int(time.time() * 1000 - start_ms)
        _mark_confirmed(conn, record_id, result.tx_digest, result.object_id)
        logger.info(
            "verification confirmed record_id=%s parlay_id=%s tx_hash=%s duration_ms=%s",
            record_id, saved_parlay_id, result.tx_digest, duration_ms,
            extra={
                "parlay_id": saved_parlay_id,
                "record_id": record_id,
                "tx_hash": result.tx_digest,
                "verification_result": "confirmed",
                "duration_ms": duration_ms,
            },
        )
        return True
    except Exception as e:
        duration_ms = int(time.time() * 1000 - start_ms)
        err_msg = str(e)
        _set_last_error(conn, record_id, err_msg)
        logger.warning(
            "verification failed record_id=%s parlay_id=%s duration_ms=%s error=%s",
            record_id, saved_parlay_id, duration_ms, err_msg,
            extra={
                "parlay_id": saved_parlay_id,
                "record_id": record_id,
                "verification_result": "failed",
                "duration_ms": duration_ms,
                "error": err_msg,
            },
            exc_info=True,
        )
        _mark_failed(conn, record_id, err_msg)
        return True  # we did process (and failed) this job


def _backoff_with_jitter(attempt: int) -> float:
    sec = min(BACKOFF_MAX_SEC, BACKOFF_BASE_SEC * (2 ** min(attempt, 10)))
    jitter = sec * 0.2 * (random.random() * 2 - 1)
    return max(0.1, sec + jitter)


def main() -> None:
    db_url = _get_sync_database_url()
    sui_rpc_url = (os.environ.get("SUI_RPC_URL") or "").strip()
    sui_private_key = (os.environ.get("SUI_PRIVATE_KEY") or "").strip()
    package_id = (os.environ.get("SUI_PACKAGE_ID") or "").strip()
    module_name = (os.environ.get("SUI_MODULE") or "parlay_proof").strip()
    function_name = (os.environ.get("SUI_FUNCTION") or "create_proof").strip()

    if not sui_rpc_url or not sui_private_key or not package_id:
        logger.error("SUI_RPC_URL, SUI_PRIVATE_KEY, and SUI_PACKAGE_ID are required")
        sys.exit(1)

    try:
        import psycopg2
    except ImportError:
        logger.error("psycopg2 is required for the verifier; install psycopg2-binary")
        sys.exit(1)

    logger.info(
        "worker starting",
        extra={
            "poll_interval_sec": POLL_INTERVAL_SEC,
            "heartbeat_interval_sec": HEARTBEAT_INTERVAL_SEC,
            "sui_module": module_name,
            "sui_function": function_name,
        },
    )

    shutdown = False

    def on_signal(_signum, _frame):
        nonlocal shutdown
        shutdown = True
        logger.info("shutdown requested")

    signal.signal(signal.SIGINT, on_signal)
    signal.signal(signal.SIGTERM, on_signal)

    last_heartbeat = time.monotonic()
    consecutive_errors = 0

    while not shutdown:
        try:
            conn = psycopg2.connect(db_url)
            try:
                processed = _run_one_cycle(
                    conn, sui_rpc_url, sui_private_key,
                    package_id, module_name, function_name,
                )
                consecutive_errors = 0
                if not processed:
                    now = time.monotonic()
                    if now - last_heartbeat >= HEARTBEAT_INTERVAL_SEC:
                        logger.info("verifier alive")
                        last_heartbeat = now
            finally:
                conn.close()
        except Exception as e:
            consecutive_errors += 1
            logger.exception("cycle error: %s", e)
            sleep_sec = _backoff_with_jitter(consecutive_errors)
            logger.info("backoff %.1fs before retry", sleep_sec)
            deadline = time.monotonic() + sleep_sec
            while time.monotonic() < deadline and not shutdown:
                time.sleep(0.5)
            continue

        if not shutdown:
            time.sleep(POLL_INTERVAL_SEC)

    logger.info("worker stopped")


if __name__ == "__main__":
    main()
