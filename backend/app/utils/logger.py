"""
app/utils/logger.py — Structured JSON logging configuration.

All log output is JSON-formatted so it can be parsed by monitoring tools
(Datadog, Grafana Loki, Cloud Logging, etc.).
"""

import logging
import sys
from pythonjsonlogger import jsonlogger
from app.config import settings


def configure_logging() -> None:
    """
    Configure the root 'agentic_crm' logger with JSON formatting.

    Call this once at application startup (inside `lifespan` or module top-level).
    All sub-loggers will inherit this configuration.
    """
    logger = logging.getLogger("agentic_crm")

    # Avoid duplicate handlers if called multiple times
    if logger.handlers:
        return

    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
    logger.propagate = False
