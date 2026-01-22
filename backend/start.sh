#!/bin/bash
set -e

# Run Alembic migrations before starting the server
echo "[STARTUP] Running Alembic migrations..."
if alembic upgrade head; then
    echo "[STARTUP] Migrations completed successfully"
else
    echo "[STARTUP] ⚠️  Migration failed, but continuing startup..."
    echo "[STARTUP] The server will start, but some features may not work correctly"
    echo "[STARTUP] Check logs and run 'alembic upgrade head' manually if needed"
fi

# Start the FastAPI server
echo "[STARTUP] Starting uvicorn server..."
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT




