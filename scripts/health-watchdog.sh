#!/usr/bin/env bash
# Health watchdog for Parlay Gorilla: if nginx or api liveness fails, restart the stack.
#
# Used by systemd parlaygorilla-watchdog.service (triggered by timer).
# Run from repo root or set APP_DIR; expects docker-compose.prod.yml and systemd unit "parlaygorilla".
set -euo pipefail

SERVICE_NAME="${SERVICE_NAME:-parlaygorilla}"
APP_DIR="${APP_DIR:-/opt/parlaygorilla}"
COMPOSE_FILE="${COMPOSE_FILE:-$APP_DIR/docker-compose.prod.yml}"

# Back-compat: HEALTH_URL is treated as nginx health URL.
NGINX_HEALTH_URL="${NGINX_HEALTH_URL:-${HEALTH_URL:-http://127.0.0.1/health}}"
API_HEALTH_URL="${API_HEALTH_URL:-http://127.0.0.1:8000/healthz}"

MAX_WAIT="${MAX_WAIT:-3}"
FAIL_THRESHOLD="${FAIL_THRESHOLD:-2}"
STATE_FILE="${STATE_FILE:-/var/run/parlaygorilla-watchdog.failcount}"

_log() {
  logger -t parlaygorilla-watchdog -- "$*"
}

_curl_ok() {
  curl -fsS --max-time "$MAX_WAIT" "$1" >/dev/null 2>&1
}

_read_fail_count() {
  if [[ -f "$STATE_FILE" ]]; then
    cat "$STATE_FILE" 2>/dev/null || echo "0"
  else
    echo "0"
  fi
}

_write_fail_count() {
  local n="$1"
  (umask 022 && echo "$n" >"$STATE_FILE") 2>/dev/null || true
}

_reset_fail_count() {
  rm -f "$STATE_FILE" 2>/dev/null || true
}

_log_cmd_tail() {
  local label="$1"
  shift
  _log "$label: $*"
  # Avoid huge journal spam: keep tail bounded.
  ( "$@" 2>&1 || true ) | tail -n 200 | while IFS= read -r line; do
    logger -t parlaygorilla-watchdog -- "$label: $line"
  done
}

if [[ ! -d "$APP_DIR" ]] || [[ ! -f "$COMPOSE_FILE" ]]; then
  echo "[watchdog] ERROR: $APP_DIR or $COMPOSE_FILE not found" >&2
  exit 2
fi

nginx_ok="false"
api_ok="false"
if _curl_ok "$NGINX_HEALTH_URL"; then
  nginx_ok="true"
fi
if _curl_ok "$API_HEALTH_URL"; then
  api_ok="true"
fi

if [[ "$nginx_ok" == "true" && "$api_ok" == "true" ]]; then
  _reset_fail_count
  exit 0
fi

prev="$(_read_fail_count)"
if ! [[ "$prev" =~ ^[0-9]+$ ]]; then
  prev="0"
fi
next=$((prev + 1))
_write_fail_count "$next"

_log "health failed (nginx_ok=$nginx_ok api_ok=$api_ok) attempt=$next/$FAIL_THRESHOLD"

if (( next < FAIL_THRESHOLD )); then
  exit 0
fi

_log "threshold reached; capturing debug and restarting ${SERVICE_NAME}"
_log_cmd_tail "systemd" systemctl status "$SERVICE_NAME" --no-pager
_log_cmd_tail "compose" docker compose -f "$COMPOSE_FILE" ps
_log_cmd_tail "docker" docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
_log_cmd_tail "logs.nginx" docker compose -f "$COMPOSE_FILE" logs --tail=200 nginx
_log_cmd_tail "logs.api" docker compose -f "$COMPOSE_FILE" logs --tail=400 api
_log_cmd_tail "logs.scheduler" docker compose -f "$COMPOSE_FILE" logs --tail=200 scheduler
_log_cmd_tail "oom" bash -lc 'dmesg -T | grep -Ei "oom|killed process|out of memory" | tail -n 50'

systemctl restart "$SERVICE_NAME"
_reset_fail_count
exit 0
