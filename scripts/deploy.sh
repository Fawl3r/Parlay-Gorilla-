#!/usr/bin/env bash
# Deploy/restart production stack on Oracle (or any VM).
# Run from app dir (e.g. /opt/parlaygorilla): bash scripts/deploy.sh
# Requires .env.prod at repo root (see OPS_RUNBOOK.md); not committed.
set -e
APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$APP_DIR"

if [ ! -f .env.prod ]; then
  echo "[deploy] ERROR: .env.prod not found at $APP_DIR/.env.prod" >&2
  echo "Create it from backend/.env.example or see docs/OPS_RUNBOOK.md. Do not commit .env.prod." >&2
  exit 1
fi

echo "[deploy] Pulling latest code..."
sudo git pull
echo "[deploy] Building and starting services..."
sudo docker compose --project-directory "$APP_DIR" -f docker-compose.prod.yml build --no-cache
sudo docker compose --project-directory "$APP_DIR" -f docker-compose.prod.yml up -d --remove-orphans

# Nginx reads config on process start. Since the config is mounted as a volume,
# a container that stays running across deploys will NOT automatically reload it.
# Restart nginx so config changes (e.g. /health behavior) take effect immediately.
echo "[deploy] Restarting nginx (reload config)..."
sudo docker compose --project-directory "$APP_DIR" -f docker-compose.prod.yml restart nginx

dump_debug() {
  set +e
  echo "[deploy] === docker compose ps ==="
  sudo docker compose --project-directory "$APP_DIR" -f docker-compose.prod.yml ps
  echo
  echo "[deploy] === nginx logs (tail) ==="
  sudo docker compose --project-directory "$APP_DIR" -f docker-compose.prod.yml logs --tail=200 nginx
  echo
  echo "[deploy] === api logs (tail) ==="
  sudo docker compose --project-directory "$APP_DIR" -f docker-compose.prod.yml logs --tail=400 api
  echo
  echo "[deploy] === scheduler logs (tail) ==="
  sudo docker compose --project-directory "$APP_DIR" -f docker-compose.prod.yml logs --tail=200 scheduler
  echo
  echo "[deploy] === verifier logs (tail) ==="
  sudo docker compose --project-directory "$APP_DIR" -f docker-compose.prod.yml logs --tail=200 verifier
  echo
  echo "[deploy] === OOM / memory pressure (dmesg tail) ==="
  sudo dmesg -T | grep -Ei "oom|killed process|out of memory" | tail -n 50
  echo
  set -e
}

wait_for_200() {
  local url="$1"
  local label="$2"
  local attempts="$3"
  local delay_seconds="$4"

  echo "[deploy] Waiting for ${label} (${url})..."
  for i in $(seq 1 "$attempts"); do
    if curl -fsS --max-time 2 "$url" >/dev/null; then
      echo "[deploy] OK: ${label}"
      return 0
    fi
    sleep "$delay_seconds"
  done

  echo "[deploy] ERROR: ${label} did not become healthy at ${url}" >&2
  return 1
}

echo "[deploy] Verifying stack health..."

# 1) Ensure nginx is accepting connections on host :80.
wait_for_200 "http://127.0.0.1/health" "nginx /health (origin liveness)" 30 1 || { dump_debug; exit 1; }

# 2) Ensure the API process is up (liveness on host :8000).
#    This is independent of DB/Redis readiness and catches crash loops (SyntaxError, missing deps, etc).
wait_for_200 "http://127.0.0.1:8000/healthz" "api /healthz (liveness)" 90 1 || { dump_debug; exit 1; }

# 3) Ensure DB + Redis are reachable (production readiness).
wait_for_200 "http://127.0.0.1:8000/readyz" "api /readyz (readiness: DB+Redis)" 60 1 || { dump_debug; exit 1; }

echo "[deploy] Done. Showing last logs..."
sudo docker compose --project-directory "$APP_DIR" -f docker-compose.prod.yml logs --tail=50
