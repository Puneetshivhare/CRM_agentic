"""
app/models/skill.py — SQLAlchemy model for dim_skills.

Agents can be programmed with user-defined skills: reusable research or outreach
strategies stored as JSON definitions. Execution metrics drive the Codex system.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from app.database import Base


class Skill(Base):
    """dim_skills — user-defined agent skills."""

    __tablename__ = "dim_skills"

    # ── Primary key ────────────────────────────────────────────────────────
    skill_id: int = Column(Integer, primary_key=True, autoincrement=True)

    # ── Ownership ─────────────────────────────────────────────────────────
    user_id: int = Column(Integer, nullable=False, index=True)

    # ── Identity ──────────────────────────────────────────────────────────
    skill_name: str = Column(String(255), nullable=False)
    skill_type: str = Column(
        String(50),
        nullable=False,
        index=True,
        comment="research | outreach | monitoring | custom",
    )

    # ── Skill definition (flexible JSON — see LLD section 1.4) ────────────
    skill_definition: dict = Column(
        JSONB,
        nullable=False,
        comment='{"criteria": {...}, "depth": "deep", "action": {...}}',
    )

    description: Optional[str] = Column(Text, nullable=True)
    version: int = Column(Integer, default=1, nullable=False)
    is_active: bool = Column(Boolean, default=True, nullable=False)

    # ── Execution metrics (used by Codex) ─────────────────────────────────
    execution_count: int = Column(Integer, default=0, nullable=False)
    success_count: int = Column(Integer, default=0, nullable=False)
    avg_execution_time_ms: Optional[float] = Column(Float, nullable=True)

    # ── Timestamps ────────────────────────────────────────────────────────
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: datetime = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    __table_args__ = (
        Index("idx_skills_user", "user_id"),
        Index("idx_skills_type", "skill_type"),
        Index("idx_skills_active", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<Skill id={self.skill_id} name={self.skill_name!r} type={self.skill_type!r}>"
