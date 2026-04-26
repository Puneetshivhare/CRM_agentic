"""SQLAlchemy engine, sessions, and connectivity helpers."""

import logging

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.config import settings

logger = logging.getLogger("agentic_crm")


def _build_engine(database_url: str) -> Engine:
    # For Supabase, we need SSL mode
    connect_args = {}
    if "supabase" in database_url or "amazonaws.com" in database_url:
        connect_args["sslmode"] = "require"
    
    return create_engine(
        database_url,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=(settings.environment == "development"),
        connect_args=connect_args,
    )


engine = _build_engine(settings.sqlalchemy_database_url)


@event.listens_for(engine, "connect")
def set_timezone(dbapi_conn, connection_record) -> None:  # type: ignore[no-untyped-def]
    """Force UTC timezone for each database connection."""
    cursor = dbapi_conn.cursor()
    cursor.execute("SET TIME ZONE 'UTC'")
    cursor.close()


SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


def get_db():
    """Yield one database session per request."""
    db: Session = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def check_db_connection(database_url: str | None = None) -> bool:
    """Perform a lightweight connectivity check against a database URL."""
    target_url = database_url or settings.sqlalchemy_database_url
    target_engine = engine if target_url == settings.sqlalchemy_database_url else _build_engine(target_url)

    try:
        with target_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        logger.error("Database connectivity check failed for %s: %s", target_url, exc)
        return False
    finally:
        if target_engine is not engine:
            target_engine.dispose()


def check_supabase_connection() -> bool | None:
    """Check the standby Supabase database if configured and not active."""
    if not settings.standby_supabase_database_url:
        return None
    return check_db_connection(settings.standby_supabase_database_url)
