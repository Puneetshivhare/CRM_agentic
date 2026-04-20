"""
app/main.py — FastAPI application entry point.

Responsibilities:
  - App creation with metadata
  - CORS middleware configuration
  - Structured JSON logging setup (via lifespan)
  - Health check endpoint
  - Router registration
  - Database connectivity check on startup
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import Base, check_db_connection, engine
from app.utils.logger import configure_logging

# ── Import all models so Base.metadata is populated for table creation ────────
import app.models  # noqa: F401  (side-effect import)

# ── Import routers ────────────────────────────────────────────────────────────
from app.routes import auth as auth_router
from app.routes import prospects as prospects_router
from app.routes import enrichment as enrichment_router
from app.routes import documents as documents_router

logger = logging.getLogger("agentic_crm")


# ── Lifespan: startup / shutdown logic ────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    FastAPI lifespan context manager.

    Startup:
      1. Configure structured logging
      2. Verify DB connectivity
      3. Create all tables (if running without Alembic in dev)

    Shutdown:
      - Dispose DB connection pool
    """
    # ── Startup ──────────────────────────────────────────────────────────
    configure_logging()
    logger.info("Starting Agentic CRM API", extra={"environment": settings.environment})

    if not check_db_connection():
        logger.critical("Cannot connect to database — check DATABASE_URL and Postgres container")
    else:
        logger.info("Database connection verified ✓")
        # Create tables for development; in production use `alembic upgrade head`
        if settings.environment == "development":
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created/verified via SQLAlchemy ✓")

    yield  # ← Application runs here

    # ── Shutdown ─────────────────────────────────────────────────────────
    engine.dispose()
    logger.info("Database connections closed. Goodbye!")


# ── FastAPI application ───────────────────────────────────────────────────────
app = FastAPI(
    title="Agentic CRM API",
    description=(
        "AI-powered prospect enrichment and CRM system. "
        "Agents autonomously research, enrich, and monitor prospects using Gemini LLM."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth_router.router)
app.include_router(prospects_router.router)
app.include_router(enrichment_router.router)
app.include_router(documents_router.router)


# ── Health check ──────────────────────────────────────────────────────────────
@app.get(
    "/health",
    tags=["System"],
    summary="Health check",
    response_description="Service health status",
)
async def health_check() -> JSONResponse:
    """
    Lightweight health check endpoint.

    Returns 200 with DB status. Used by Docker HEALTHCHECK and load balancers.
    """
    db_ok = check_db_connection()
    payload = {
        "status": "ok" if db_ok else "degraded",
        "service": "agentic-crm-api",
        "version": "1.0.0",
        "database": "connected" if db_ok else "unreachable",
        "environment": settings.environment,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    status_code = 200 if db_ok else 503
    return JSONResponse(content=payload, status_code=status_code)


@app.get("/", tags=["System"], include_in_schema=False)
async def root() -> dict:
    """Redirect hint for the root URL."""
    return {"message": "Agentic CRM API — visit /docs for API documentation"}
