"""
app/database.py — SQLAlchemy engine, session factory, and dependency injection.

Provides:
  - `engine`       → SQLAlchemy Engine (used by Alembic + Base.metadata)
  - `SessionLocal` → Session factory for route-level DB access
  - `Base`         → Declarative base class (all models inherit this)
  - `get_db()`     → FastAPI dependency that yields a scoped DB session

DATABASE CONFIGURATION:
  Current: Supabase PostgreSQL (via settings.database_url from .env)
  Legacy: Local PostgreSQL (commented below)

TO REVERT TO LOCAL POSTGRES:
  1. In .env: uncomment DATABASE_URL=postgresql://crm_user:crm_password@localhost:5433/agentic_crm
  2. In docker-compose.yml: uncomment postgres service
  3. Keep everything else the same — SQLAlchemy works identically with both
"""

import logging
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.config import settings

logger = logging.getLogger("agentic_crm")

# ── Engine ────────────────────────────────────────────────────────────────────
# Current: Supabase PostgreSQL
engine = create_engine(
    settings.database_url,
    pool_size=10,        # persistent connections in the pool
    max_overflow=20,     # temporary connections above pool_size
    pool_pre_ping=True,  # test connection health before use
    pool_recycle=3600,   # recycle connections after 1 hour to avoid stale sockets
    echo=(settings.environment == "development"),  # log SQL in dev only
)

# Legacy: Local PostgreSQL engine (commented — to use, update config.py and docker-compose.yml)
# engine = create_engine(
#     "postgresql://crm_user:crm_password@localhost:5433/agentic_crm",
#     pool_size=10,
#     max_overflow=20,
#     pool_pre_ping=True,
#     pool_recycle=3600,
#     echo=(settings.environment == "development"),
# )


@event.listens_for(engine, "connect")
def set_timezone(dbapi_conn, connection_record) -> None:  # type: ignore[no-untyped-def]
    """Force UTC timezone for all DB connections."""
    cursor = dbapi_conn.cursor()
    cursor.execute("SET TIME ZONE 'UTC'")
    cursor.close()


# ── Session factory ───────────────────────────────────────────────────────────
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)

# ── Declarative base shared by all SQLAlchemy models ─────────────────────────
Base = declarative_base()


# ── FastAPI dependency ────────────────────────────────────────────────────────
def get_db():
    """
    Yield a database session for the duration of a single HTTP request.

    Usage in route:
        @router.get("/example")
        def example(db: Session = Depends(get_db)):
            ...

    The session is always closed, even if the route raises an exception.
    """
    db: Session = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def check_db_connection() -> bool:
    """
    Perform a lightweight connectivity check against the database.

    Returns:
        True if Postgres is reachable, False otherwise.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        logger.error("Database connectivity check failed: %s", exc)
        return False
