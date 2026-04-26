"""FastAPI application entry point."""

import logging
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import app.models  # noqa: F401
from app.config import settings
from app.database import Base, check_db_connection, check_supabase_connection, engine
from app.routes import auth as auth_router
from app.routes import campaigns as campaigns_router
from app.routes import companies as companies_router
from app.routes import documents as documents_router
from app.routes import enrichment as enrichment_router
from app.routes import hermes as hermes_router
from app.routes import lead_scores as lead_scores_router
from app.routes import prospects as prospects_router
from app.routes import rules as rules_router
from app.routes import search as search_router
from app.utils.logger import configure_logging, trace_logic

logger = logging.getLogger("agentic_crm")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Configure logging and verify active and standby database connections."""
    configure_logging()
    logger.info(
        "Starting Agentic CRM API",
        extra={
            "environment": settings.environment,
            "active_db_provider": settings.normalized_db_provider,
        },
    )
    trace_logic(
        logger,
        "app.startup",
        active_db_provider=settings.normalized_db_provider,
        environment=settings.environment,
        has_supabase_url=bool(settings.supabase_url),
        has_supabase_db_url=bool(settings.supabase_database_url),
    )

    if check_db_connection():
        logger.info("Active database connection verified")
        if settings.environment == "development":
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created or verified")
    else:
        logger.critical("Cannot connect to active database")

    supabase_status = check_supabase_connection()
    if supabase_status is True:
        logger.info("Standby Supabase connection verified")
    elif supabase_status is False:
        logger.warning("Standby Supabase connection is configured but unreachable")

    yield

    engine.dispose()
    logger.info("Database connections closed")


app = FastAPI(
    title="Agentic CRM API",
    description="Minimal backend API for the current Agentic CRM frontend.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(prospects_router.router)
app.include_router(companies_router.router)
app.include_router(campaigns_router.router)
app.include_router(documents_router.router)
app.include_router(enrichment_router.router)
app.include_router(hermes_router.router)
app.include_router(lead_scores_router.router)
app.include_router(rules_router.router)
app.include_router(search_router.router)


@app.get("/health", tags=["System"], summary="Health check")
async def health_check() -> JSONResponse:
    """Return active database status for Docker and frontend diagnostics."""
    db_ok = check_db_connection()
    trace_logic(
        logger,
        "health.check",
        database_connected=db_ok,
        active_db_provider=settings.normalized_db_provider,
    )
    payload = {
        "status": "ok" if db_ok else "degraded",
        "service": "agentic-crm-api",
        "version": "1.0.0",
        "database": "connected" if db_ok else "unreachable",
        "active_db_provider": settings.normalized_db_provider,
        "environment": settings.environment,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    return JSONResponse(content=payload, status_code=200 if db_ok else 503)


@app.get("/", tags=["System"], include_in_schema=False)
async def root() -> dict[str, str]:
    return {"message": "Agentic CRM API - visit /docs for API documentation"}
