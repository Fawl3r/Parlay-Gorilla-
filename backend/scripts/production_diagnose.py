#!/usr/bin/env python3
"""
Read-only production sync diagnostics. No SSH, no data modification.
Fetches LOCAL_SHA, /ops/version and /ops/verify (with OPS_VERIFY_TOKEN if set),
compares SHAs, derives FRONTEND_EXPECTED_SHA, and outputs one of:
  SYNCED | BACKEND_OUT_OF_DATE | CACHE_OR_FRONTEND_STALE
"""
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

BACKEND_URL = os.environ.get("BACKEND_URL", "https://api.parlaygorilla.com").rstrip("/")
OPS_VERIFY_TOKEN = os.environ.get("OPS_VERIFY_TOKEN", "").strip()


def get_local_sha() -> str:
    """Short commit SHA of repo HEAD (backend parent = repo root)."""
    try:
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=backend_dir,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if out.returncode == 0 and out.stdout:
            return out.stdout.strip()
    except Exception:
        pass
    return ""


def fetch_ops(path: str) -> tuple[dict, str]:
    """Returns (parsed JSON, error_message). error_message empty on success."""
    url = f"{BACKEND_URL}{path}"
    try:
        if OPS_VERIFY_TOKEN:
            req = urllib.request.Request(url, headers={"x-ops-token": OPS_VERIFY_TOKEN})
        else:
            req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read().decode()
    except urllib.error.HTTPError as e:
        if e.code == 403:
            return {}, "403 (set OPS_VERIFY_TOKEN for production)"
        return {}, str(e)
    except Exception as e:
        return {}, str(e)
    try:
        return json.loads(data), ""
    except Exception as e:
        return {}, f"Parse error: {e}"


def main() -> None:
    local_sha = get_local_sha()
    if not local_sha:
        print("LOCAL_SHA: (unable to read git HEAD)")
    else:
        print(f"LOCAL_SHA: {local_sha}")

    # Frontend expected SHA: same as Vercel would inject (VERCEL_GIT_COMMIT_SHA or NEXT_PUBLIC_GIT_SHA or fallback to local)
    frontend_expected_sha = (
        os.environ.get("VERCEL_GIT_COMMIT_SHA", "").strip()
        or os.environ.get("NEXT_PUBLIC_GIT_SHA", "").strip()
        or local_sha
    )
    if not frontend_expected_sha:
        frontend_expected_sha = "unknown"
    print(f"FRONTEND_EXPECTED_SHA: {frontend_expected_sha}")

    version_payload, version_err = fetch_ops("/ops/version")
    verify_payload, verify_err = fetch_ops("/ops/verify")

    backend_sha = ""
    if not verify_err and isinstance(verify_payload, dict) and verify_payload is not None:
        backend_sha = (verify_payload.get("git_sha") or "").strip()
    if not backend_sha and not version_err and isinstance(version_payload, dict) and version_payload is not None:
        backend_sha = (version_payload.get("git_sha") or "").strip()

    if verify_err or version_err:
        err = verify_err or version_err
        print(f"BACKEND: error — {err}")
        print("STATE: (cannot determine — backend unreachable or token required)")
        sys.exit(2)
    print(f"BACKEND_SHA: {backend_sha or 'unknown'}")

    # Determine state
    if not local_sha:
        print("STATE: (unknown — no local SHA)")
        sys.exit(2)
    if backend_sha == "unknown" or not backend_sha:
        print("STATE: BACKEND_OUT_OF_DATE (backend did not return a deploy SHA; .env.deploy or systemd ordering may be wrong)")
        sys.exit(1)
    if backend_sha != local_sha:
        print("STATE: BACKEND_OUT_OF_DATE (production backend SHA does not match repo HEAD)")
        sys.exit(1)
    if frontend_expected_sha != local_sha and frontend_expected_sha != "unknown":
        print("STATE: CACHE_OR_FRONTEND_STALE (backend matches HEAD; frontend build may show different SHA — purge CDN or redeploy frontend)")
        sys.exit(0)
    print("STATE: SYNCED")
    sys.exit(0)


if __name__ == "__main__":
    main()
