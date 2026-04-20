"""
migrations/env.py — Alembic runtime environment.

Key behaviours:
  - DATABASE_URL is read from the environment (picks up Docker env vars automatically)
  - All models are imported so Alembic can auto-detect schema diffs
  - Supports both offline (SQL script) and online (live DB) migration modes
"""

import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# ── Import models so Alembic can detect all table definitions ─────────────────
from app.database import Base
import app.models  # noqa: F401  (registers all models onto Base.metadata)

# ── Alembic config ────────────────────────────────────────────────────────────
config = context.config
fileConfig(config.config_file_name)

# Override sqlalchemy.url with the real DATABASE_URL from environment
database_url = os.environ.get("DATABASE_URL")
if not database_url:
    raise RuntimeError(
        "DATABASE_URL environment variable is not set. "
        "Run migrations inside the backend container where Docker injects env vars."
    )
# Escape '%' for configparser interpolation
config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Emit SQL migration script without connecting to the DB.
    Useful for generating review scripts.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Connect to the DB and apply migrations directly.
    This is the standard flow used in `alembic upgrade head`.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
