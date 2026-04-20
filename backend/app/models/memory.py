"""
app/models/memory.py — SQLAlchemy models for memory_store (KV) and memory_vector.

MemoryStore: flat key-value cache with optional TTL (backed by Postgres).
MemoryVector: pgvector-backed semantic memory for similarity search.

Note: pgvector VECTOR type requires the pgvector extension (installed via Docker init script).
We use Text as a fallback for the embedding column until pgvector is confirmed available;
the Alembic env.py will handle the correct SQL DDL via a hand-written migration.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from app.database import Base


class MemoryStore(Base):
    """
    memory_store — flat key-value persistent memory for agents.

    Keys follow a structured namespace:
      prospect:{id}                 → Full prospect context
      company:{id}                  → Company context / cached research
      company:{id}:monitoring_state → Previous monitoring snapshot
      user:{id}:preferences         → User preferences
      cache:research:{domain}       → Short-lived crawl cache
    """

    __tablename__ = "memory_store"

    # ── Primary key ────────────────────────────────────────────────────────
    memory_key: str = Column(String(500), primary_key=True)

    # ── Value ─────────────────────────────────────────────────────────────
    memory_value: dict = Column(JSONB, nullable=False)

    # ── TTL (optional — NULL means persistent) ────────────────────────────
    ttl_seconds: Optional[int] = Column(
        Integer,
        nullable=True,
        comment="Time-to-live in seconds. NULL = no expiry.",
    )

    # ── Timestamps ────────────────────────────────────────────────────────
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
    accessed_at: datetime = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "ttl_seconds IS NULL OR ttl_seconds > 0",
            name="ck_memory_ttl_positive",
        ),
        Index("idx_memory_accessed", "accessed_at"),
    )

    def __repr__(self) -> str:
        return f"<MemoryStore key={self.memory_key!r}>"


class MemoryVector(Base):
    """
    memory_vector — pgvector-backed semantic memory.

    Each row stores a 768-dimensional Gemini embedding alongside the
    original text and entity metadata for filtered similarity search.

    The `embedding` column is declared as Text here to avoid SQLAlchemy
    import errors if pgvector is not yet installed. The actual migration
    will use `ALTER TABLE ... ALTER COLUMN embedding TYPE vector(768)`.
    """

    __tablename__ = "memory_vector"

    # ── Primary key ────────────────────────────────────────────────────────
    vector_id: int = Column(Integer, primary_key=True, autoincrement=True)

    # ── Embedding reference key ───────────────────────────────────────────
    embedding_key: Optional[str] = Column(
        String(500),
        nullable=True,
        comment="e.g. 'prospect:123:research'",
    )

    # ── Embedding (stored as Text; migration converts to vector(768)) ──────
    embedding: Optional[str] = Column(
        Text,
        nullable=True,
        comment="768-dim Gemini embedding (Text placeholder; migration sets VECTOR type)",
    )
    embedding_text: Optional[str] = Column(
        Text,
        nullable=True,
        comment="Original text that was embedded",
    )

    # ── Entity metadata for filtering ─────────────────────────────────────
    entity_type: Optional[str] = Column(
        String(50),
        nullable=True,
        comment="prospect | company | skill_result",
    )
    entity_id: Optional[int] = Column(Integer, nullable=True)
    user_id: int = Column(Integer, nullable=False, index=True)

    # ── Timestamp ─────────────────────────────────────────────────────────
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_memory_vector_user", "user_id"),
        Index("idx_memory_vector_key", "embedding_key"),
    )

    def __repr__(self) -> str:
        return (
            f"<MemoryVector id={self.vector_id} "
            f"type={self.entity_type!r} entity={self.entity_id}>"
        )
