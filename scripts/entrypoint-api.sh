#!/bin/bash
# Production API entrypoint: run migrations under advisory lock, then start Gunicorn.
# On migration failure, exit non-zero so restart policy applies.
# Scheduler uses the same image but overrides CMD and does NOT run this script.
set -e
echo "Running DB migrations (locked)…"
cd /app
python -m app.ops.migrate_with_lock
echo "Starting API…"
exec gunicorn -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000 --workers "${WEB_CONCURRENCY:-2}" --timeout "${GUNICORN_TIMEOUT:-120}"
