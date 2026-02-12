# ARM-safe (amd64/arm64) backend image for API and Pattern A verifier.
# Same image used for api and verifier services; command differs in compose.
# Multi-stage so pysui-fastcrypto (Rust) can be built with gcc in builder only.

# Stage 1: build deps (need gcc for pysui-fastcrypto / maturin linker)
FROM python:3.12-slim AS builder
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --target /install -r requirements.txt

# Stage 2: runtime (no compiler)
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
ENV PYTHONPATH=/install
COPY --from=builder /install /install
COPY . .
# Default: run API (overridden by compose for verifier).
# Migrations run in api service via compose command.
ENV PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "python -m alembic upgrade head 2>/dev/null || true && exec python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
