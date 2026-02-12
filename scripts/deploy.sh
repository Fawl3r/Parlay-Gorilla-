#!/usr/bin/env bash
# Deploy/restart production stack on Oracle (or any VM).
# Run from app dir (e.g. /opt/parlaygorilla): bash scripts/deploy.sh
set -e
APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$APP_DIR"
echo "[deploy] Pulling latest code..."
sudo git pull
echo "[deploy] Building and starting services..."
sudo docker compose --project-directory "$APP_DIR" -f docker-compose.prod.yml build --no-cache
sudo docker compose --project-directory "$APP_DIR" -f docker-compose.prod.yml up -d
echo "[deploy] Done. Showing last logs..."
sudo docker compose --project-directory "$APP_DIR" -f docker-compose.prod.yml logs --tail=50
