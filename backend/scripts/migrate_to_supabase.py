"""Migrate public app tables from local Postgres to Supabase Postgres."""

from __future__ import annotations

import logging
import os
from typing import Iterable

from sqlalchemy import MetaData, Table, create_engine, delete, select, text

from app.database import Base
from app.utils.logger import configure_logging, trace_logic

import app.models  # noqa: F401

logger = logging.getLogger("agentic_crm")

TABLE_ORDER = [
    "auth_users",
    "dim_companies",
    "dim_prospects",
    "dim_documents",
    "dim_skills",
    "dim_rules",
    "fact_interactions",
    "fact_enrichment_events",
    "fact_agent_executions",
    "fact_lead_scores",
    "fact_rule_executions",
    "memory_store",
    "memory_vector",
    "dim_campaigns",
]


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def reset_identity_sequence(conn, table_name: str, primary_key_columns: Iterable[str]) -> None:
    for column_name in primary_key_columns:
        conn.execute(
            text(
                """
                SELECT setval(
                    pg_get_serial_sequence(:table_name, :column_name),
                    COALESCE((SELECT MAX(""" + column_name + """) FROM """ + table_name + """), 1),
                    (SELECT MAX(""" + column_name + """) IS NOT NULL FROM """ + table_name + """)
                )
                """
            ),
            {"table_name": table_name, "column_name": column_name},
        )


def main() -> None:
    configure_logging()

    source_url = require_env("LOCAL_DATABASE_URL")
    target_url = require_env("SUPABASE_DATABASE_URL")

    source_engine = create_engine(source_url, pool_pre_ping=True)
    target_engine = create_engine(target_url, pool_pre_ping=True)

    trace_logic(logger, "migration.start", source="local", target="supabase")

    try:
        Base.metadata.create_all(bind=target_engine)

        source_meta = MetaData()
        target_meta = MetaData()
        source_meta.reflect(bind=source_engine, only=TABLE_ORDER)
        target_meta.reflect(bind=target_engine, only=TABLE_ORDER)

        with target_engine.begin() as target_conn:
            for table_name in reversed(TABLE_ORDER):
                target_conn.execute(delete(target_meta.tables[table_name]))
                trace_logic(logger, "migration.clear_table", table=table_name)

            for table_name in TABLE_ORDER:
                source_table: Table = source_meta.tables[table_name]
                target_table: Table = target_meta.tables[table_name]
                with source_engine.connect() as source_conn:
                    rows = [dict(row) for row in source_conn.execute(select(source_table)).mappings()]

                if rows:
                    target_conn.execute(target_table.insert(), rows)

                trace_logic(logger, "migration.copy_table", table=table_name, rows=len(rows))

                pk_columns = [
                    column.name
                    for column in target_table.primary_key.columns
                    if str(column.type).lower() in {"integer", "bigint"}
                ]
                if pk_columns:
                    reset_identity_sequence(target_conn, table_name, pk_columns)

        trace_logic(logger, "migration.complete", tables=len(TABLE_ORDER))
    finally:
        source_engine.dispose()
        target_engine.dispose()


if __name__ == "__main__":
    main()
