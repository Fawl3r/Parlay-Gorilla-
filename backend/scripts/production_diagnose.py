#!/usr/bin/env python3
"""
Read-only production sync diagnostics. No SSH, no data modification.
Confirms frontend (FRONTEND_URL) and backend (BACKEND_URL) reachable; warns if
Cloudflare Worker execution headers present (proxy-only architecture).
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
FRONTEND_URL = os.environ.get("FRONTEND_URL", "https://www.parlaygorilla.com").rstrip("/")
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


def fetch_url_headers(url: str, extra_headers: dict | None = None) -> tuple[bool, dict]:
    """GET url and return (success, dict of lowercased header names -> value)."""
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "curl/8.0 (parlaygorilla-production-diagnose)")
        req.add_header("Accept", "application/json,text/plain,*/*")
        if extra_headers:
            for k, v in extra_headers.items():
                req.add_header(k, v)
        with urllib.request.urlopen(req, timeout=10) as resp:
            _ = resp.read()
            return True, {k.lower(): v for k, v in resp.headers.items()}
    except Exception:
        return False, {}


def _warn_if_worker_headers(headers: dict, label: str) -> None:
    """If Cloudflare Worker execution headers present, print warning (proxy-only architecture)."""
    worker_indicators = ("cf-worker", "cf-execution-mode")
    for h in worker_indicators:
        if h in headers:
            print(f"WARNING: unexpected worker execution layer detected on {label} (header: {h})", file=sys.stderr)


def fetch_ops(path: str) -> tuple[dict, str]:
    """Returns (parsed JSON, error_message). error_message empty on success."""
    url = f"{BACKEND_URL}{path}"
    try:
        headers = {
            "User-Agent": "curl/8.0 (parlaygorilla-production-diagnose)",
            "Accept": "application/json",
            "Cache-Control": "no-store",
        }
        if OPS_VERIFY_TOKEN:
            headers["x-ops-token"] = OPS_VERIFY_TOKEN
        req = urllib.request.Request(url, headers=headers)
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


def fetch_frontend_version() -> tuple[str, str]:
    """Returns (frontend git_sha, error_message)."""
    url = f"{FRONTEND_URL}/api/version"
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "curl/8.0 (parlaygorilla-production-diagnose)",
                "Accept": "application/json",
                "Cache-Control": "no-store",
            },
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read().decode()
    except urllib.error.HTTPError as e:
        return "", f"HTTP {e.code}"
    except Exception as e:
        return "", str(e)
    try:
        payload = json.loads(data)
        return (payload.get("git_sha") or "").strip(), ""
    except Exception as e:
        return "", f"Parse error: {e}"


def main() -> None:
    local_sha = get_local_sha()
    if not local_sha:
        print("LOCAL_SHA: (unable to read git HEAD)")
    else:
        print(f"LOCAL_SHA: {local_sha}")

    # Confirm frontend and backend reachable; warn if Cloudflare Worker headers present (proxy-only architecture)
    frontend_ok, frontend_headers = fetch_url_headers(
        f"{FRONTEND_URL}/api/version",
        {"Cache-Control": "no-store"},
    )
    print(f"FRONTEND: {'reachable' if frontend_ok else 'unreachable'} ({FRONTEND_URL})")
    if frontend_ok:
        _warn_if_worker_headers(frontend_headers, "frontend")

    backend_headers_req = {"x-ops-token": OPS_VERIFY_TOKEN} if OPS_VERIFY_TOKEN else None
    backend_ok, backend_headers = fetch_url_headers(f"{BACKEND_URL}/ops/version", backend_headers_req)
    print(f"BACKEND: {'reachable' if backend_ok else 'unreachable'} ({BACKEND_URL})")
    if backend_ok:
        _warn_if_worker_headers(backend_headers, "backend")

    # Frontend expected SHA: same as Vercel would inject (VERCEL_GIT_COMMIT_SHA or NEXT_PUBLIC_GIT_SHA or fallback to local)
    frontend_expected_sha = (
        os.environ.get("VERCEL_GIT_COMMIT_SHA", "").strip()
        or os.environ.get("NEXT_PUBLIC_GIT_SHA", "").strip()
        or local_sha
    )
    if not frontend_expected_sha:
        frontend_expected_sha = "unknown"
    print(f"FRONTEND_EXPECTED_SHA: {frontend_expected_sha}")

    frontend_sha, frontend_version_err = fetch_frontend_version()
    if frontend_version_err:
        print(f"FRONTEND: error — {frontend_version_err}")
        print("STATE: FRONTEND_UNREACHABLE")
        sys.exit(1)
    print(f"FRONTEND_SHA: {frontend_sha or 'unknown'}")

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
    if frontend_sha == "unknown" or not frontend_sha:
        print("STATE: FRONTEND_OUT_OF_DATE (frontend did not return a deploy SHA)")
        sys.exit(1)
    if frontend_sha != local_sha:
        print("STATE: CACHE_OR_FRONTEND_STALE (frontend SHA does not match repo HEAD)")
        sys.exit(1)
    if frontend_expected_sha != local_sha and frontend_expected_sha != "unknown":
        print("STATE: CACHE_OR_FRONTEND_STALE (backend matches HEAD; frontend build may show different SHA — purge CDN or redeploy frontend)")
        sys.exit(0)
    print("STATE: SYNCED")
    sys.exit(0)


if __name__ == "__main__":
    main()
