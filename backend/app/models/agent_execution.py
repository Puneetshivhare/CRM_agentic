"""
app/models/agent_execution.py — SQLAlchemy model for fact_agent_executions.

The Codex system's core table: logs every agent run with full input/output,
performance metrics, and Gemini token/cost tracking.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.database import Base


class AgentExecution(Base):
    """fact_agent_executions — Codex observability log for all agent runs."""

    __tablename__ = "fact_agent_executions"

    # ── Primary key ────────────────────────────────────────────────────────
    execution_id: int = Column(Integer, primary_key=True, autoincrement=True)

    # ── Ownership ─────────────────────────────────────────────────────────
    user_id: int = Column(Integer, nullable=False, index=True)

    # ── Agent identity ────────────────────────────────────────────────────
    agent_type: str = Column(
        String(100),
        nullable=False,
        index=True,
        comment="ResearchAgent | EnrichmentAgent | MonitoringAgent | ...",
    )
    agent_name: Optional[str] = Column(
        String(100),
        nullable=True,
        comment="Worker name if running in parallel, e.g. 'ResearchAgent_worker_1'",
    )
    task_id: str = Column(String(255), nullable=False, comment="Unique task UUID")

    # ── Task context FKs (nullable — not every run targets a prospect/company) ──
    prospect_id: Optional[int] = Column(
        Integer,
        ForeignKey("dim_prospects.prospect_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    company_id: Optional[int] = Column(
        Integer,
        ForeignKey("dim_companies.company_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ── Execution lifecycle ───────────────────────────────────────────────
    status: str = Column(
        String(50),
        nullable=False,
        index=True,
        comment="pending | running | success | failed",
    )
    input_data: Optional[dict] = Column(JSONB, nullable=True)
    output_data: Optional[dict] = Column(JSONB, nullable=True)
    error_message: Optional[str] = Column(Text, nullable=True)

    # ── Performance metrics ───────────────────────────────────────────────
    start_time: datetime = Column(DateTime, nullable=False)
    end_time: Optional[datetime] = Column(DateTime, nullable=True)
    duration_ms: Optional[int] = Column(Integer, nullable=True)

    # ── Cost tracking (Gemini) ────────────────────────────────────────────
    tokens_used: Optional[int] = Column(Integer, nullable=True, index=True)
    api_cost_cents: Optional[Decimal] = Column(Numeric(10, 2), nullable=True)

    # ── Decision metadata (for Codex analysis) ────────────────────────────
    decision_description: Optional[str] = Column(Text, nullable=True)
    confidence_score: Optional[float] = Column(Float, nullable=True)
    memory_hits: int = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Count of cache hits during this execution",
    )

    # ── Timestamp ─────────────────────────────────────────────────────────
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)

    # ── Relationships ─────────────────────────────────────────────────────
    prospect = relationship(
        "Prospect",
        foreign_keys=[prospect_id],
        back_populates="agent_executions",
        lazy="select",
    )

    __table_args__ = (
        Index("idx_agent_executions_user", "user_id"),
        Index("idx_agent_executions_agent", "agent_type"),
        Index("idx_agent_executions_status", "status"),
        Index("idx_agent_executions_date", "created_at"),
        Index("idx_agent_executions_tokens", "tokens_used"),
    )

    def __repr__(self) -> str:
        return (
            f"<AgentExecution id={self.execution_id} "
            f"agent={self.agent_type!r} status={self.status!r}>"
        )
