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
sudo docker compose --project-directory "$APP_DIR" -f docker-compose.prod.yml up -d
echo "[deploy] Done. Showing last logs..."
sudo docker compose --project-directory "$APP_DIR" -f docker-compose.prod.yml logs --tail=50
