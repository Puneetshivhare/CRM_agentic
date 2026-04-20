"""
app/models/interaction.py — SQLAlchemy model for fact_interactions.

Immutable event log of all interactions with a prospect.
Rows are INSERT-only to preserve audit trail integrity.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from app.database import Base


class Interaction(Base):
    """fact_interactions — immutable interaction event log."""

    __tablename__ = "fact_interactions"

    # ── Primary key ────────────────────────────────────────────────────────
    interaction_id: int = Column(Integer, primary_key=True, autoincrement=True)

    # ── Prospect reference ────────────────────────────────────────────────
    prospect_id: int = Column(
        Integer,
        ForeignKey("dim_prospects.prospect_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Interaction data ──────────────────────────────────────────────────
    interaction_type: str = Column(
        String(50),
        nullable=False,
        index=True,
        comment="email | call | meeting | linkedin_message",
    )
    subject: Optional[str] = Column(String(500), nullable=True)
    body: Optional[str] = Column(Text, nullable=True)

    # ── Metadata ──────────────────────────────────────────────────────────
    initiated_by: Optional[str] = Column(
        String(50),
        nullable=True,
        comment="user | prospect",
    )
    interaction_date: datetime = Column(DateTime, nullable=False)
    duration_seconds: Optional[int] = Column(
        Integer,
        nullable=True,
        comment="For call/meeting duration",
    )

    # ── Engagement ────────────────────────────────────────────────────────
    email_opened: Optional[bool] = Column(Boolean, nullable=True)
    email_clicked: Optional[bool] = Column(Boolean, nullable=True)

    # ── Metadata ──────────────────────────────────────────────────────────
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)

    # ── Relationships ─────────────────────────────────────────────────────
    prospect = relationship("Prospect", back_populates="interactions", lazy="select")

    __table_args__ = (
        Index("idx_interactions_prospect", "prospect_id"),
        Index("idx_interactions_date", "interaction_date"),
        Index("idx_interactions_type", "interaction_type"),
    )

    def __repr__(self) -> str:
        return (
            f"<Interaction id={self.interaction_id} "
            f"type={self.interaction_type!r} prospect={self.prospect_id}>"
        )
