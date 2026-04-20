"""
app/models/rule.py — SQLAlchemy model for dim_rules.

Stores automation rules: trigger conditions and associated actions.
Rules are evaluated by the orchestrator for every enrichment event.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from app.database import Base


class Rule(Base):
    """dim_rules — user-defined automation rules."""

    __tablename__ = "dim_rules"

    # ── Primary key ────────────────────────────────────────────────────────
    rule_id: int = Column(Integer, primary_key=True, autoincrement=True)

    # ── Ownership ─────────────────────────────────────────────────────────
    user_id: int = Column(Integer, nullable=False, index=True)

    # ── Identity ──────────────────────────────────────────────────────────
    rule_name: str = Column(String(255), nullable=False)
    rule_type: str = Column(
        String(50),
        nullable=False,
        comment="trigger | data | workflow",
    )

    # ── Rule definition ───────────────────────────────────────────────────
    rule_definition: dict = Column(
        JSONB,
        nullable=False,
        comment='{"type": "trigger", "condition": "...", "action": {...}}',
    )
    description: Optional[str] = Column(Text, nullable=True)

    # ── Activation ────────────────────────────────────────────────────────
    is_active: bool = Column(Boolean, default=True, nullable=False)
    priority: int = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Higher value = executed first",
    )

    # ── Execution metrics ─────────────────────────────────────────────────
    execution_count: int = Column(Integer, default=0, nullable=False)
    match_count: int = Column(Integer, default=0, nullable=False)

    # ── Timestamps ────────────────────────────────────────────────────────
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: datetime = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    __table_args__ = (
        Index("idx_rules_user", "user_id"),
        Index("idx_rules_type", "rule_type"),
        Index("idx_rules_active_priority", "is_active", "priority"),
    )

    def __repr__(self) -> str:
        return f"<Rule id={self.rule_id} name={self.rule_name!r} active={self.is_active}>"
