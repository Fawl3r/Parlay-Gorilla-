#!/usr/bin/env bash
# Deploy backend on Oracle VM: pull latest, install deps, set GIT_SHA, restart service, verify.
# Run from repo root (e.g. /opt/parlaygorilla/current) or from backend/.
# Idempotent; requires: git, pip, systemctl (parlaygorilla-backend.service).
set -e

REPO_ROOT=
if [[ -f backend/requirements.txt ]]; then
  REPO_ROOT="$(pwd)"
elif [[ -f requirements.txt ]]; then
  REPO_ROOT="$(pwd)/.."
  cd "$REPO_ROOT"
else
  echo "FAIL: Run from repo root or backend/ (requirements.txt not found)"
  exit 1
fi

BACKEND_DIR="${REPO_ROOT}/backend"
PORT="${BACKEND_PORT:-8000}"
SERVICE_NAME="${BACKEND_SERVICE_NAME:-parlaygorilla-backend}"

echo "== Deploy backend (repo_root=$REPO_ROOT, backend=$BACKEND_DIR) =="

# 1) Pull latest
git fetch origin
git reset --hard origin/main
GIT_SHA=$(git rev-parse --short HEAD)
echo "Git SHA: $GIT_SHA"

# 2) Install dependencies
cd "$BACKEND_DIR"
pip install -r requirements.txt
cd "$REPO_ROOT"

# 3) Export GIT_SHA for the service (optional env file used by systemd)
ENV_DEPLOY="${REPO_ROOT}/.env.deploy"
echo "GIT_SHA=$GIT_SHA" > "$ENV_DEPLOY"
echo "BUILD_TIME=$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$ENV_DEPLOY"

# 4) Restart backend service
if ! command -v systemctl &>/dev/null; then
  echo "WARN: systemctl not found; skip restart. Start app manually with GIT_SHA=$GIT_SHA"
else
  sudo systemctl restart "$SERVICE_NAME"
  echo "Restarted $SERVICE_NAME"
fi

# 5) Verify health
sleep 2
URL="http://127.0.0.1:${PORT}/ops/version"
if command -v curl &>/dev/null; then
  if curl -sf "$URL" >/dev/null; then
    echo "PASS: $URL OK"
    curl -s "$URL" | head -c 200
    echo
  else
    echo "FAIL: $URL not OK (service may still be starting)"
    exit 1
  fi
else
  echo "WARN: curl not found; skip version check. Verify manually: $URL"
fi

echo "== Deploy finished =="
