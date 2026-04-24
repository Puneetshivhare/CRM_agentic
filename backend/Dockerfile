# syntax=docker/dockerfile:1
# ────────────────────────────────────────────────────────────────────────────
# Agentic CRM — Backend Dockerfile
# Base: python:3.11-slim (minimal footprint, security-focused)
# ────────────────────────────────────────────────────────────────────────────

FROM python:3.11-slim AS base

# ── System prerequisites ─────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── Python dependencies (installed before copying app code for layer caching) ─
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m playwright install --with-deps chromium

# ── Application code ──────────────────────────────────────────────────────────
COPY . .

# ── Runtime configuration ─────────────────────────────────────────────────────
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

# ── Health check (Docker will call this every 30 s) ──────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

EXPOSE ${PORT}

# ── Default command (override in docker-compose for reload in dev) ────────────
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
