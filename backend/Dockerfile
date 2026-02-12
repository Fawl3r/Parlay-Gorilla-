# ARM-safe (amd64/arm64) backend image for API and Pattern A verifier.
# Same image used for api and verifier services; command differs in compose.
FROM python:3.12-slim

WORKDIR /app

# System deps if needed (e.g. for psycopg2; slim has minimal libs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
# Default: run API (overridden by compose for verifier).
# Migrations run in api service via compose command.
ENV PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head 2>/dev/null || true && exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
