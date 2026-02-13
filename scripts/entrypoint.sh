#!/bin/bash
# Production API entrypoint: run migrations then start Gunicorn.
# On migration failure, exit non-zero so restart policy applies.
set -e
echo "Running migrations..."
cd /app && alembic upgrade head
echo "Starting API..."
exec gunicorn -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000 --workers 2 --timeout 120
