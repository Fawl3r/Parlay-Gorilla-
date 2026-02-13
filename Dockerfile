# Production Dockerfile at repo root. Build: docker build -f Dockerfile .
# Same image for api and scheduler; compose overrides CMD for scheduler.
# Multi-stage: builder has gcc for pysui-fastcrypto (Rust); runtime is slim.

# Stage 1: install deps (need gcc for pysui/maturin)
FROM python:3.11-slim AS builder
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --target /install -r requirements.txt

# Stage 2: runtime (no compiler)
FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*
RUN useradd --create-home --shell /bin/bash appuser
WORKDIR /app
ENV PYTHONPATH=/install:/app
COPY --from=builder /install /install
COPY backend/ .
COPY scripts/entrypoint-api.sh /entrypoint-api.sh
RUN chown -R appuser:appuser /app /install && chmod +x /entrypoint-api.sh
USER appuser
EXPOSE 8000
# Default: run API (migrate-with-lock + gunicorn). Compose overrides CMD for scheduler (no migrations).
CMD ["/entrypoint-api.sh"]
