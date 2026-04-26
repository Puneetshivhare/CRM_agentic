"""
hermes_app/main.py — Hermes Agent SaaS Entry Point.
Restricted agent with guardrails for CRM integration.
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import yaml
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from hermes_app.config import settings
from hermes_app.guardrails import GuardrailsManager

logger = logging.getLogger("hermes")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup and shutdown lifecycle."""
    # Load guardrails
    guardrails_path = os.path.join(os.path.dirname(__file__), "..", "guardrails.yml")
    app.state.guardrails = GuardrailsManager(guardrails_path)
    
    logger.info(
        "Starting Hermes Agent",
        extra={
            "mode": settings.mode,
            "tenant_isolation": settings.tenant_isolation,
            "allowed_actions": app.state.guardrails.allowed_actions,
        }
    )
    
    yield
    
    logger.info("Shutting down Hermes Agent")


app = FastAPI(
    title="Hermes Agent SaaS",
    description="Self-improving AI agent with guardrails for CRM integration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["System"])
async def health_check() -> JSONResponse:
    """Health check endpoint."""
    return JSONResponse(
        content={
            "status": "healthy",
            "service": "hermes-agent",
            "mode": settings.mode,
            "version": "1.0.0",
        },
        status_code=200
    )


# Import and include routers
from hermes_app.routes import tasks, tenant, skills, mcp

app.include_router(tasks.router, prefix="/api/v1")
app.include_router(tenant.router, prefix="/api/v1")
app.include_router(skills.router, prefix="/api/v1")
app.include_router(mcp.router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
