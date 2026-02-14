#!/usr/bin/env bash
# Health watchdog for Parlay Gorilla: if origin /health fails, restart the stack.
# Used by systemd parlaygorilla-watchdog.service (triggered by timer).
# Run from repo root or set APP_DIR; expects docker-compose.prod.yml and systemd unit parlaygorilla.

set -e
APP_DIR="${APP_DIR:-/opt/parlaygorilla}"
HEALTH_URL="${HEALTH_URL:-http://127.0.0.1/health}"
MAX_WAIT="${MAX_WAIT:-5}"

if [ ! -d "$APP_DIR" ] || [ ! -f "$APP_DIR/docker-compose.prod.yml" ]; then
  echo "[watchdog] ERROR: $APP_DIR or docker-compose.prod.yml not found" >&2
  exit 2
fi

if curl -fsS --max-time "$MAX_WAIT" "$HEALTH_URL" >/dev/null 2>&1; then
  exit 0
fi

echo "[watchdog] FAIL: $HEALTH_URL did not return 200; restarting parlaygorilla"
systemctl restart parlaygorilla
exit 0
