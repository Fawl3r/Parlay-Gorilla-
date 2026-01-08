#!/bin/bash
set -e

# Run Alembic migrations before starting the server
echo "[STARTUP] Running Alembic migrations..."
alembic upgrade head

# Start the FastAPI server
echo "[STARTUP] Starting uvicorn server..."
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT



