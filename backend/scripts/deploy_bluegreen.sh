#!/usr/bin/env bash
# Blue/green zero-downtime deploy for Parlay Gorilla backend (Oracle VM).
# Usage: bash deploy_bluegreen.sh <repo_url> <branch>
# Requires: flock, git, python3-venv, curl, jq; /etc/parlaygorilla/backend.env; systemd parlaygorilla-backend.
# Logs to /var/log/parlaygorilla/deploy.log. Writes /opt/parlaygorilla/last_deploy.json on success.
# Regression gate: post-cutover calls /ops/model-health; rollback if pipeline blocked by stale resolver.

set -euo pipefail

REPO_URL="${1:?Usage: deploy_bluegreen.sh <repo_url> <branch>}"
BRANCH="${2:-main}"
BASE="/opt/parlaygorilla"
RELEASES="${BASE}/releases"
CURRENT="${BASE}/current"
BACKEND_ENV="/etc/parlaygorilla/backend.env"
LOG_FILE="/var/log/parlaygorilla/deploy.log"
LOCK_FILE="/opt/parlaygorilla/.deploy.lock"
LAST_DEPLOY_JSON="${BASE}/last_deploy.json"
PREFLIGHT_PORT=8001
HEALTH_PATH="/ops/version"
VERIFY_PATH="/ops/verify"
MODEL_HEALTH_PATH="/ops/model-health"
HEALTH_RETRIES=30
HEALTH_INTERVAL=1
MAIN_PORT=8000

DEPLOY_START_TS=$(date -u +%s)
DEPLOY_ID="${DEPLOY_ID:-$(command -v uuidgen >/dev/null 2>&1 && uuidgen || echo "deploy-${DEPLOY_START_TS}")}"
CORRELATION_ID="$DEPLOY_ID"
export DEPLOY_ID CORRELATION_ID

# Ensure log dir exists and is writable by deploy user (bootstrap: sudo mkdir -p /var/log/parlaygorilla && sudo chown $DEPLOY_USER /var/log/parlaygorilla)
mkdir -p /var/log/parlaygorilla 2>/dev/null || true
[ -w /var/log/parlaygorilla ] || LOG_FILE="${BASE}/deploy.log"

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] [deploy_id=$DEPLOY_ID] [correlation_id=$CORRELATION_ID] $*" | tee -a "$LOG_FILE"; }

# Curl health with optional ops token (from env after sourcing backend.env)
_curl_health() {
  local url="$1"
  if [ -n "${OPS_VERIFY_TOKEN:-}" ]; then
    curl -fsS --max-time 2 -H "x-ops-token: $OPS_VERIFY_TOKEN" "$url"
  else
    curl -fsS --max-time 2 "$url"
  fi
}
_curl_health_silent() {
  _curl_health "$1" >/dev/null 2>&1
}

# Cleanup pre-flight process on exit
PREFLIGHT_PID=""
cleanup_preflight() {
  if [ -n "$PREFLIGHT_PID" ]; then
    log "Stopping pre-flight process (PID $PREFLIGHT_PID)"
    kill "$PREFLIGHT_PID" 2>/dev/null || true
    wait "$PREFLIGHT_PID" 2>/dev/null || true
    PREFLIGHT_PID=""
  fi
}
trap cleanup_preflight EXIT

# Lock: only one deploy at a time
exec 200>"$LOCK_FILE"
if ! flock -n 200; then
  log "ERROR: Another deploy holds the lock. Exiting."
  exit 1
fi

log "=== Deploy started (branch=$BRANCH, repo=$REPO_URL) ==="
# Load OPS_VERIFY_TOKEN for regression gate and verify (optional)
set -a
# shellcheck source=/dev/null
[ -f "$BACKEND_ENV" ] && { set +u; source "$BACKEND_ENV"; set -u; }
set +a

# Resolve current slot and choose target
if [ ! -L "$CURRENT" ]; then
  log "ERROR: $CURRENT is not a symlink. Bootstrap required (see docs/deploy/oracle_bluegreen_setup.md)."
  exit 1
fi
CURRENT_SLOT=$(basename "$(readlink -f "$CURRENT")")
if [ "$CURRENT_SLOT" = "blue" ]; then
  TARGET_SLOT="green"
else
  TARGET_SLOT="blue"
fi
TARGET_DIR="${RELEASES}/${TARGET_SLOT}"
log "Current slot: $CURRENT_SLOT, target slot: $TARGET_SLOT"

# Ensure slot dir exists
sudo mkdir -p "$TARGET_DIR"
sudo chown "$(whoami)" "$TARGET_DIR" 2>/dev/null || true

# Clone repo to temp and sync into target (exclude .venv and .git)
STAGING=$(mktemp -d)
log "Cloning $BRANCH into $STAGING"
git clone --depth 1 --branch "$BRANCH" "$REPO_URL" "$STAGING"

GIT_SHA=$(git -C "$STAGING" rev-parse --short HEAD)
log "Deploying commit: $GIT_SHA"

# Clean target slot (remove old app files; we will recreate .venv)
rm -rf "${TARGET_DIR:?}"/*
rm -rf "${TARGET_DIR:?}"/.[!.]* 2>/dev/null || true
# Copy repo contents into slot (entire repo root: backend/, docs/, etc.)
rsync -a --exclude='.git' "$STAGING/" "$TARGET_DIR/"
rm -rf "$STAGING"

# Python venv in slot
VENV="${TARGET_DIR}/.venv"
if [ ! -d "$VENV" ]; then
  log "Creating venv at $VENV"
  python3 -m venv "$VENV"
fi
log "Installing dependencies from backend/requirements.txt"
"$VENV/bin/pip" install --quiet -r "${TARGET_DIR}/backend/requirements.txt"

# Write GIT_SHA for this slot (for systemd via .env.deploy and for scripts)
echo "GIT_SHA=$GIT_SHA" > "${TARGET_DIR}/.gitsha"
echo "GIT_SHA=$GIT_SHA" > "${TARGET_DIR}/.env.deploy"
BUILD_TIME=$(date -u +%Y-%m-%dT%H:%M:%SZ)
echo "BUILD_TIME=$BUILD_TIME" >> "${TARGET_DIR}/.env.deploy"

# Pre-flight: start new slot on alternate port (do not touch main service)
log "Starting pre-flight on 127.0.0.1:$PREFLIGHT_PORT"
set -a
# shellcheck source=/dev/null
[ -f "$BACKEND_ENV" ] && { set +u; source "$BACKEND_ENV"; set -u; }
set +a
export GIT_SHA
export BUILD_TIME
cd "${TARGET_DIR}/backend"
"${VENV}/bin/uvicorn" app.main:app --host 127.0.0.1 --port "$PREFLIGHT_PORT" &
PREFLIGHT_PID=$!
cd - >/dev/null

# Wait for pre-flight health (use token if set)
log "Waiting for pre-flight health at http://127.0.0.1:${PREFLIGHT_PORT}${HEALTH_PATH} (max ${HEALTH_RETRIES}s)"
for i in $(seq 1 "$HEALTH_RETRIES"); do
  if _curl_health_silent "http://127.0.0.1:${PREFLIGHT_PORT}${HEALTH_PATH}"; then
    log "Pre-flight health OK"
    break
  fi
  if [ "$i" -eq "$HEALTH_RETRIES" ]; then
    log "ERROR: Pre-flight health check failed after ${HEALTH_RETRIES}s"
    exit 1
  fi
  sleep "$HEALTH_INTERVAL"
done

# Migrations (gated)
if grep -q '^[[:space:]]*MIGRATIONS_ALLOWED[[:space:]]*=[[:space:]]*true' "$BACKEND_ENV" 2>/dev/null; then
  log "Running alembic upgrade head in target slot"
  set -a
  # shellcheck source=/dev/null
  { set +u; source "$BACKEND_ENV"; set -u; }
  set +a
  export GIT_SHA
  (cd "${TARGET_DIR}/backend" && "${VENV}/bin/alembic" upgrade head) >> "$LOG_FILE" 2>&1 || log "WARNING: alembic upgrade returned non-zero"
else
  log "Skipping migrations (MIGRATIONS_ALLOWED != true)"
fi

# Remember previous slot SHA for rollback verify
PREVIOUS_SHA=""
[ -f "${RELEASES}/${CURRENT_SLOT}/.gitsha" ] && PREVIOUS_SHA=$(grep -E '^GIT_SHA=' "${RELEASES}/${CURRENT_SLOT}/.gitsha" 2>/dev/null | cut -d= -f2) || true

# Cutover: atomic symlink switch + restart
log "Cutover: switching current to $TARGET_SLOT"
ln -sfn "$TARGET_DIR" "$CURRENT"
sudo systemctl restart parlaygorilla-backend

# Post-cutover health
log "Waiting for post-cutover health at http://127.0.0.1:${MAIN_PORT}${HEALTH_PATH} (max ${HEALTH_RETRIES}s)"
for i in $(seq 1 "$HEALTH_RETRIES"); do
  if _curl_health_silent "http://127.0.0.1:${MAIN_PORT}${HEALTH_PATH}"; then
    log "Post-cutover health OK"
    break
  fi
  if [ "$i" -eq "$HEALTH_RETRIES" ]; then
    log "ERROR: Post-cutover health failed. Rolling back to $CURRENT_SLOT and restarting service."
    ln -sfn "${RELEASES}/${CURRENT_SLOT}" "$CURRENT"
    sudo systemctl restart parlaygorilla-backend
    for j in $(seq 1 "$HEALTH_RETRIES"); do
      if _curl_health_silent "http://127.0.0.1:${MAIN_PORT}${HEALTH_PATH}"; then
        log "Rollback complete: previous slot $CURRENT_SLOT is healthy again. Deploy failed (exit 1)."
        exit 1
      fi
      sleep "$HEALTH_INTERVAL"
    done
    log "ERROR: Rollback health check also failed"
    exit 1
  fi
  sleep "$HEALTH_INTERVAL"
done

# Regression gate: /ops/model-health must be 200 and (pipeline_ok or only insufficient-data blockers)
REGRESSION_FAIL=0
if command -v jq >/dev/null 2>&1; then
  MH_RESP="$(_curl_health "http://127.0.0.1:${MAIN_PORT}${MODEL_HEALTH_PATH}" 2>/dev/null)" || true
  if [ -n "$MH_RESP" ]; then
    PIPELINE_OK=$(echo "$MH_RESP" | jq -r '.pipeline_ok // false')
    BLOCKERS=$(echo "$MH_RESP" | jq -r '.pipeline_blockers | join(" ") // ""')
    if [ "$PIPELINE_OK" != "true" ] && echo "$BLOCKERS" | grep -q "result_resolution has not run in 2 hours"; then
      log "ERROR: Regression gate failed: pipeline not OK and resolver stale (result_resolution has not run in 2 hours)"
      REGRESSION_FAIL=1
    fi
  else
    log "WARNING: Could not fetch model-health; skipping regression gate"
  fi
else
  log "WARNING: jq not installed; skipping regression gate"
fi

if [ "$REGRESSION_FAIL" -eq 1 ]; then
  log "ERROR: Rolling back due to regression gate failure. Switching current to $CURRENT_SLOT and restarting."
  ln -sfn "${RELEASES}/${CURRENT_SLOT}" "$CURRENT"
  sudo systemctl restart parlaygorilla-backend
  for j in $(seq 1 "$HEALTH_RETRIES"); do
    if _curl_health_silent "http://127.0.0.1:${MAIN_PORT}${VERIFY_PATH}"; then
      VERIFY_SHA=$(_curl_health "http://127.0.0.1:${MAIN_PORT}${VERIFY_PATH}" 2>/dev/null | jq -r '.git_sha // empty')
      if [ -n "$PREVIOUS_SHA" ] && [ "$VERIFY_SHA" = "$PREVIOUS_SHA" ]; then
        log "Rollback verified: /ops/verify returns previous sha $PREVIOUS_SHA. Deploy failed (exit 1)."
      fi
      break
    fi
    sleep "$HEALTH_INTERVAL"
  done
  exit 1
fi

# Success: write last_deploy.json
DEPLOY_END_TS=$(date -u +%s)
DURATION_MS=$(( (DEPLOY_END_TS - DEPLOY_START_TS) * 1000 ))
DEPLOY_TIME=$(date -u +%Y-%m-%dT%H:%M:%SZ)
mkdir -p "$BASE"
printf '%s\n' "{\"deployed_sha\":\"$GIT_SHA\",\"slot\":\"$TARGET_SLOT\",\"deploy_time\":\"$DEPLOY_TIME\",\"deploy_id\":\"$DEPLOY_ID\",\"duration_ms\":$DURATION_MS}" > "$LAST_DEPLOY_JSON"
log "=== Deploy finished successfully. Deployed SHA: $GIT_SHA (duration_ms=$DURATION_MS) ==="
exit 0
