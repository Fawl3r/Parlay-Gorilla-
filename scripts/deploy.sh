#!/usr/bin/env bash
# Deploy/restart production stack on Oracle (or any VM).
# Run from app dir (e.g. /opt/parlaygorilla): bash scripts/deploy.sh
set -e
cd "$(dirname "$0")/.."
echo "[deploy] Pulling latest code..."
git pull
echo "[deploy] Building and starting services..."
docker compose -f docker-compose.prod.yml build --no-cache
docker compose -f docker-compose.prod.yml up -d
echo "[deploy] Done. Showing last logs..."
docker compose -f docker-compose.prod.yml logs --tail=50
