"""Structured logging and lightweight debug trace helpers."""

import json
import logging
import sys

from pythonjsonlogger import jsonlogger

from app.config import settings


def configure_logging() -> None:
    """Configure the root application logger once."""
    logger = logging.getLogger("agentic_crm")
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


def trace_logic(logger: logging.Logger, event: str, **context) -> None:
    """Write a structured log and optional stdout trace for backend debugging."""
    payload = {"event": event, **context}
    logger.info(event, extra={"debug_context": payload})
    if settings.debug_trace_enabled:
        print(json.dumps(payload, default=str), flush=True)
