#!/usr/bin/env python3
"""
Autonomous Deploy Guardian: detect production drift (frontend Vercel, backend Oracle)
and deployment failures. Read-only checks; sends Telegram alerts on mismatch/failure.
Rate-limited: alert on state change or at most once per 60 minutes for same failure.

Env: BACKEND_URL, FRONTEND_URL, OPS_VERIFY_TOKEN (required for backend check),
EXPECTED_SHA (optional; else from GitHub API via GITHUB_REPOSITORY + GITHUB_TOKEN),
TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID (optional; no-op if missing),
GUARDIAN_STATE_PATH (optional; default: script_dir/.deploy_guardian_state.json),
GITHUB_RUN_ID (optional; link in alert).
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# Script dir for default state file
_SCRIPT_DIR = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# Config (env only; no secrets in repo)
# ---------------------------------------------------------------------------

BACKEND_URL = (os.environ.get("BACKEND_URL") or "https://api.parlaygorilla.com").rstrip("/")
FRONTEND_URL = (os.environ.get("FRONTEND_URL") or "https://parlaygorilla.com").rstrip("/")
OPS_VERIFY_TOKEN = (os.environ.get("OPS_VERIFY_TOKEN") or "").strip()
EXPECTED_SHA = (os.environ.get("EXPECTED_SHA") or "").strip()
GITHUB_REPOSITORY = (os.environ.get("GITHUB_REPOSITORY") or "").strip()
GITHUB_TOKEN = (os.environ.get("GITHUB_TOKEN") or "").strip()
TELEGRAM_BOT_TOKEN = (os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
TELEGRAM_CHAT_ID = (os.environ.get("TELEGRAM_CHAT_ID") or "").strip()
GUARDIAN_STATE_PATH = os.environ.get("GUARDIAN_STATE_PATH") or str(_SCRIPT_DIR / ".deploy_guardian_state.json")
GITHUB_RUN_ID = (os.environ.get("GITHUB_RUN_ID") or "").strip()

TIMEOUT = 15
ALERT_COOLDOWN_SEC = 60 * 60  # 1 hour

# Drift states (script exits 1 for all except OK and UNKNOWN)
STATE_OK = "OK"
STATE_BACKEND_DRIFT = "BACKEND_DRIFT"
STATE_FRONTEND_DRIFT = "FRONTEND_DRIFT"
STATE_SPLIT_BRAIN = "SPLIT_BRAIN"
STATE_UNKNOWN = "UNKNOWN"
STATE_ERROR = "ERROR"


def _get_expected_sha() -> str:
    """Expected SHA: from EXPECTED_SHA env or GitHub API (main branch)."""
    if EXPECTED_SHA:
        return EXPECTED_SHA
    if not GITHUB_REPOSITORY or not GITHUB_TOKEN:
        return ""
    url = f"https://api.github.com/repos/{GITHUB_REPOSITORY}/commits/main"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {GITHUB_TOKEN}")
    req.add_header("Accept", "application/vnd.github.v3+json")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            sha = (data.get("sha") or "").strip()
            return sha[:7] if len(sha) >= 7 else sha
    except Exception:
        return ""


def _backend_sha() -> tuple[str, str]:
    """GET BACKEND_URL/ops/verify with x-ops-token. Returns (sha, error). error empty on success."""
    if not OPS_VERIFY_TOKEN:
        return "", "OPS_VERIFY_TOKEN not set (required for backend check)"
    url = f"{BACKEND_URL}/ops/verify"
    req = urllib.request.Request(url, headers={"x-ops-token": OPS_VERIFY_TOKEN})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            payload = json.loads(resp.read().decode())
            sha = (payload.get("git_sha") or "").strip()
            return sha, ""
    except urllib.error.HTTPError as e:
        if e.code == 403:
            return "", "403 forbidden (missing or invalid x-ops-token)"
        return "", f"HTTP {e.code}"
    except Exception as e:
        return "", str(e)


def _frontend_sha() -> tuple[str, str]:
    """GET FRONTEND_URL/api/version. Returns (sha, error). error empty on success."""
    url = f"{FRONTEND_URL}/api/version"
    req = urllib.request.Request(url)
    req.add_header("Cache-Control", "no-store")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            payload = json.loads(resp.read().decode())
            sha = (payload.get("git_sha") or "").strip() or "unknown"
            return sha, ""
    except urllib.error.HTTPError as e:
        return "", f"HTTP {e.code}"
    except Exception as e:
        return "", str(e)


def _classify(
    expected: str,
    backend_sha: str,
    frontend_sha: str,
    backend_err: str,
    frontend_err: str,
) -> tuple[str, str]:
    """
    Classify drift state. Returns (state, reason).
    """
    if backend_err:
        return STATE_ERROR, f"backend: {backend_err}"
    if frontend_err:
        return STATE_ERROR, f"frontend: {frontend_err}"
    if not backend_sha or backend_sha == "unknown":
        return STATE_UNKNOWN, "backend sha unknown"
    if not frontend_sha or frontend_sha == "unknown":
        return STATE_UNKNOWN, "frontend sha unknown"
    if backend_sha != frontend_sha:
        return STATE_SPLIT_BRAIN, "backend and frontend sha differ"
    if expected:
        if backend_sha != expected:
            return STATE_BACKEND_DRIFT, f"backend ({backend_sha}) != expected ({expected})"
        if frontend_sha != expected:
            return STATE_FRONTEND_DRIFT, f"frontend ({frontend_sha}) != expected ({expected})"
        return STATE_OK, ""
    return STATE_OK, ""


def _send_telegram(text: str) -> bool:
    """Send one Telegram message. No-op if token or chat_id missing. Never raises."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID or not text:
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = json.dumps({"chat_id": TELEGRAM_CHAT_ID, "text": text[:4096], "parse_mode": "HTML"}).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except Exception:
        return False


def _load_state() -> dict:
    """Load state file for rate limiting."""
    try:
        with open(GUARDIAN_STATE_PATH, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except Exception:
        return {}


def _save_state(state: dict) -> None:
    """Write state file (best effort)."""
    try:
        with open(GUARDIAN_STATE_PATH, "w") as f:
            json.dump(state, f, indent=0)
    except Exception:
        pass


def _should_alert(current_state: str, last_state: str, last_alert_at: float | None) -> bool:
    """Alert on state change, or at most once per ALERT_COOLDOWN_SEC for same failure."""
    if current_state == STATE_OK:
        return False
    if current_state != last_state:
        return True
    if last_alert_at is None:
        return True
    return (time.time() - last_alert_at) >= ALERT_COOLDOWN_SEC


def main() -> int:
    expected = _get_expected_sha()
    backend_sha, backend_err = _backend_sha()
    frontend_sha, frontend_err = _frontend_sha()

    state, reason = _classify(
        expected, backend_sha, frontend_sha, backend_err, frontend_err
    )

    # State payload for workflow (stdout JSON + state file)
    now = time.time()
    payload = {
        "state": state,
        "reason": reason,
        "expected_sha": expected or "(none)",
        "backend_sha": backend_sha or "(error)",
        "frontend_sha": frontend_sha or "(error)",
        "timestamp": now,
    }

    prev = _load_state()
    last_state = prev.get("last_state", "")
    last_alert_at = prev.get("last_alert_at")

    if _should_alert(state, last_state, last_alert_at):
        run_url = ""
        if GITHUB_RUN_ID and GITHUB_REPOSITORY:
            run_url = f"https://github.com/{GITHUB_REPOSITORY}/actions/runs/{GITHUB_RUN_ID}"
        lines = [
            f"<b>Deploy Guardian</b> — {state}",
            reason and f"Reason: {reason}" or "",
            f"Expected: {expected or 'n/a'}",
            f"Backend:  {backend_sha or backend_err or 'n/a'}",
            f"Frontend: {frontend_sha or frontend_err or 'n/a'}",
            f"Time: {payload['timestamp']}",
        ]
        if run_url:
            lines.append(run_url)
        msg = "\n".join(x for x in lines if x)
        _send_telegram(msg)
        prev["last_state"] = state
        prev["last_alert_at"] = now
        _save_state(prev)
    else:
        prev["last_state"] = state
        _save_state(prev)

    # Emit JSON for workflow (e.g. output or artifact)
    print(json.dumps(payload))

    if state in (STATE_BACKEND_DRIFT, STATE_FRONTEND_DRIFT, STATE_SPLIT_BRAIN, STATE_ERROR):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
