"""
app/models/prospect.py — SQLAlchemy model for dim_prospects (dimension table).

Tracks individual sales prospects. Linked to dim_companies via company_id.
enrichment_status drives the agent workflow state machine:
  pending → enriching → enriched | failed
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import relationship
from app.database import Base


class Prospect(Base):
    """dim_prospects — prospect dimension (Snowflake schema)."""

    __tablename__ = "dim_prospects"

    # ── Primary key ────────────────────────────────────────────────────────
    prospect_id: int = Column(Integer, primary_key=True, autoincrement=True)

    # ── Ownership (application-enforced FK to auth_users) ─────────────────
    user_id: int = Column(Integer, nullable=False, index=True)

    # ── Identity ──────────────────────────────────────────────────────────
    email: Optional[str] = Column(String(255), nullable=True, index=True)
    first_name: Optional[str] = Column(String(100), nullable=True)
    last_name: Optional[str] = Column(String(100), nullable=True)
    title: Optional[str] = Column(String(255), nullable=True, comment="Job title")
    phone: Optional[str] = Column(String(20), nullable=True)
    location: Optional[str] = Column(String(255), nullable=True)

    # ── Social / web links ────────────────────────────────────────────────
    linkedin_url: Optional[str] = Column(String(500), nullable=True)
    website_url: Optional[str] = Column(String(500), nullable=True)

    # ── Company FK ───────────────────────────────────────────────────────
    company_id: Optional[int] = Column(
        Integer,
        ForeignKey("dim_companies.company_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ── Enrichment state machine ──────────────────────────────────────────
    enrichment_status: str = Column(
        String(50),
        default="pending",
        nullable=False,
        index=True,
        comment="pending | enriching | enriched | failed",
    )
    enrichment_confidence: float = Column(
        Float,
        default=0.0,
        nullable=False,
        comment="0.0–1.0 completeness score",
    )

    # ── Engagement metrics ────────────────────────────────────────────────
    last_contacted_at: Optional[datetime] = Column(DateTime, nullable=True)
    email_opens: int = Column(Integer, default=0, nullable=False)
    email_clicks: int = Column(Integer, default=0, nullable=False)

    # ── Timestamps ────────────────────────────────────────────────────────
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: datetime = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # ── Relationships ─────────────────────────────────────────────────────
    company = relationship("Company", back_populates="prospects", lazy="select")
    interactions = relationship("Interaction", back_populates="prospect", lazy="select")
    enrichment_events = relationship(
        "EnrichmentEvent", back_populates="prospect", lazy="select"
    )
    agent_executions = relationship(
        "AgentExecution",
        foreign_keys="AgentExecution.prospect_id",
        back_populates="prospect",
        lazy="select",
    )

    # ── Table constraints & indexes ────────────────────────────────────────
    __table_args__ = (
        CheckConstraint(
            "enrichment_confidence >= 0 AND enrichment_confidence <= 1",
            name="ck_prospect_confidence",
        ),
        Index("idx_prospects_user", "user_id"),
        Index("idx_prospects_company", "company_id"),
        Index("idx_prospects_email", "email"),
        Index(
            "idx_prospects_enrichment",
            "enrichment_status",
            "enrichment_confidence",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Prospect id={self.prospect_id} "
            f"name={self.first_name!r} {self.last_name!r} "
            f"status={self.enrichment_status!r}>"
        )
