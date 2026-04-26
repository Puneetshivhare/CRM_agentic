# syntax=docker/dockerfile:1
# ────────────────────────────────────────────────────────────────────────────
# Hermes Agent — Multi-tenant SaaS Dockerfile for Agentic CRM
# Base: python:3.11-slim with security hardening
# ────────────────────────────────────────────────────────────────────────────

FROM python:3.11-slim AS base

# ── System prerequisites ─────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libpq-dev \
    sqlite3 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# ── Security: Create non-root user ───────────────────────────────────────────
RUN groupadd -r hermes && useradd -r -g hermes -s /bin/false hermes

WORKDIR /app

# ── Python dependencies ────────────────────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Application code ─────────────────────────────────────────────────────────
COPY . .

# ── Setup directories with proper permissions ────────────────────────────────
RUN mkdir -p /app/data /app/skills /app/tenants /app/logs /app/guardrails && \
    chown -R hermes:hermes /app

# ── Copy guardrails configuration ────────────────────────────────────────────
COPY guardrails.yml /app/guardrails/guardrails.yml
RUN chown hermes:hermes /app/guardrails/guardrails.yml

# ── Security: Switch to non-root user ────────────────────────────────────────
USER hermes

# ── Runtime configuration ────────────────────────────────────────────────────
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    HERMES_HOME=/app \
    HERMES_DATA_DIR=/app/data \
    HERMES_SKILLS_DIR=/app/skills \
    HERMES_TENANTS_DIR=/app/tenants

# ── Health check ─────────────────────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

EXPOSE ${PORT}

# ── Default command ───────────────────────────────────────────────────────────
CMD ["python", "-m", "uvicorn", "hermes_app.main:app", "--host", "0.0.0.0", "--port", "8000"]
