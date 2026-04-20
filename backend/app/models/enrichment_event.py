"""
app/models/enrichment_event.py — SQLAlchemy model for fact_enrichment_events.

Immutable audit trail of every field change made by any agent.
Enables full enrichment history and confidence tracking per field.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship
from app.database import Base


class EnrichmentEvent(Base):
    """fact_enrichment_events — immutable per-field enrichment audit log."""

    __tablename__ = "fact_enrichment_events"

    # ── Primary key ────────────────────────────────────────────────────────
    event_id: int = Column(Integer, primary_key=True, autoincrement=True)

    # ── Prospect reference ────────────────────────────────────────────────
    prospect_id: int = Column(
        Integer,
        ForeignKey("dim_prospects.prospect_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Change data capture ───────────────────────────────────────────────
    field_name: str = Column(
        String(255),
        nullable=False,
        comment="e.g. 'company_name', 'headcount', 'funding_stage'",
    )
    old_value: Optional[str] = Column(Text, nullable=True, comment="NULL if new field")
    new_value: str = Column(Text, nullable=False)

    # ── Agent provenance ──────────────────────────────────────────────────
    agent_name: str = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Which agent made this change",
    )
    confidence_score: Optional[float] = Column(
        Float,
        nullable=True,
        comment="0.0–1.0 confidence in the new value",
    )
    source: Optional[str] = Column(
        String(255),
        nullable=True,
        comment="e.g. 'crawl:linkedin', 'gemini:extraction'",
    )

    # ── Timestamp ─────────────────────────────────────────────────────────
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)

    # ── Relationships ─────────────────────────────────────────────────────
    prospect = relationship(
        "Prospect", back_populates="enrichment_events", lazy="select"
    )

    __table_args__ = (
        Index("idx_enrichment_prospect", "prospect_id"),
        Index("idx_enrichment_agent", "agent_name"),
        Index("idx_enrichment_date", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<EnrichmentEvent id={self.event_id} "
            f"field={self.field_name!r} agent={self.agent_name!r}>"
        )
