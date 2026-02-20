#!/usr/bin/env python3
"""
Verify production backend is serving the same commit as local repo.
Compares local git SHA with GET <BACKEND_URL>/ops/verify (or /ops/version).
Requires OPS_VERIFY_TOKEN when BACKEND_URL is not localhost (Cloudflare/WAF).
"""
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

BACKEND_URL = os.environ.get("BACKEND_URL", "https://api.parlaygorilla.com").rstrip("/")
OPS_VERIFY_TOKEN = os.environ.get("OPS_VERIFY_TOKEN", "").strip()
# Prefer /ops/verify for CI; same token protection
VERIFY_PATH = "/ops/verify"


def get_local_sha() -> str:
    """Short commit SHA of current branch (main or HEAD)."""
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


def get_production_version() -> tuple[str, str]:
    """Returns (git_sha from /ops/verify or /ops/version, error_message). error_message empty on success."""
    is_local = "localhost" in BACKEND_URL or "127.0.0.1" in BACKEND_URL
    url = f"{BACKEND_URL}{VERIFY_PATH}"
    headers = {
        # Use explicit JSON/curl-like headers to avoid edge bot heuristics from generic urllib defaults.
        "User-Agent": "curl/8.0 (parlaygorilla-sync-check)",
        "Accept": "application/json",
        "Cache-Control": "no-store",
    }
    if OPS_VERIFY_TOKEN:
        headers["x-ops-token"] = OPS_VERIFY_TOKEN
    elif not is_local:
        print("FAIL: OPS_VERIFY_TOKEN not set. Production backend requires x-ops-token (see docs/deploy/oracle_bluegreen_setup.md).")
        return "", "OPS_VERIFY_TOKEN required for non-local BACKEND_URL"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read().decode()
    except urllib.error.HTTPError as e:
        if e.code == 403:
            return "", "403 forbidden (missing or invalid x-ops-token; set OPS_VERIFY_TOKEN)"
        return "", str(e)
    except Exception as e:
        return "", str(e)
    try:
        payload = json.loads(data)
        sha = (payload.get("git_sha") or "").strip()
        return sha, ""
    except Exception as e:
        return "", f"Parse error: {e}"


def main() -> None:
    local = get_local_sha()
    if not local:
        print("FAIL: Could not get local git SHA (not a git repo or git failed)")
        sys.exit(1)
    prod_sha, err = get_production_version()
    if err:
        print(f"FAIL: Could not get production version: {err}")
        print("  (Backend may be down, wrong BACKEND_URL, or network issue)")
        if "api.parlaygorilla.com" in BACKEND_URL:
            print("  For production: ensure GitHub repo variable BACKEND_URL and secret OPS_VERIFY_TOKEN are set (docs/deploy/PROD_VARS_AND_SECRETS.md).")
        sys.exit(1)
    if local == prod_sha:
        print("PASS: Production backend matches local commit:", local)
        sys.exit(0)
    print("FAIL: SHA mismatch")
    print(f"  Local:     {local}")
    print(f"  Production: {prod_sha}")
    print()
    print("Likely cause:")
    print("  - Backend deploy: backend not restarted or deploy script not run on Oracle VM.")
    print("    Fix: Run backend/scripts/deploy_bluegreen.sh on the VM and ensure systemctl restarted.")
    print("  - Frontend deploy: if you only care about backend, ignore. Otherwise ensure Vercel")
    print("    production branch is main and root directory is frontend; redeploy from dashboard.")
    print("  - Caching: Cloudflare or browser may be serving old backend response.")
    print("    Fix: Purge Cloudflare cache or hit /ops/version with cache-busting query param.")
    sys.exit(1)


if __name__ == "__main__":
    main()
