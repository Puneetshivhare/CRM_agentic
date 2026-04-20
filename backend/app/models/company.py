"""
app/models/company.py — SQLAlchemy model for dim_companies (dimension table).

Stores company profile data. Acts as the central dimension that prospects link to.
tech_stack is stored as JSONB for schema flexibility.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.database import Base


class Company(Base):
    """dim_companies — company dimension (Snowflake schema)."""

    __tablename__ = "dim_companies"

    # ── Primary key ────────────────────────────────────────────────────────
    company_id: int = Column(Integer, primary_key=True, autoincrement=True)

    # ── Ownership (application-enforced FK to auth_users) ─────────────────
    user_id: int = Column(Integer, nullable=False, index=True)

    # ── Company identity ──────────────────────────────────────────────────
    name: str = Column(String(255), unique=True, nullable=False)
    domain: Optional[str] = Column(String(255), nullable=True, index=True)
    description: Optional[str] = Column(Text, nullable=True)

    # ── Company metrics ───────────────────────────────────────────────────
    headcount: Optional[int] = Column(Integer, nullable=True)
    headcount_range: Optional[str] = Column(
        String(20),
        nullable=True,
        comment="e.g. '50-100' when exact headcount is unknown",
    )
    revenue_annual: Optional[int] = Column(
        BigInteger,
        nullable=True,
        comment="Annual revenue in USD",
    )

    # ── Funding info ──────────────────────────────────────────────────────
    funding_stage: Optional[str] = Column(
        String(50),
        nullable=True,
        index=True,
        comment="seed | series_a | series_b | ipo | etc.",
    )
    latest_funding_date: Optional[datetime] = Column(Date, nullable=True)

    # ── Geography ─────────────────────────────────────────────────────────
    headquarters_city: Optional[str] = Column(String(100), nullable=True)
    headquarters_country: Optional[str] = Column(String(100), nullable=True)

    # ── Classification ────────────────────────────────────────────────────
    industry: Optional[str] = Column(String(100), nullable=True)

    # ── Tech stack (flexible JSON array) ─────────────────────────────────
    tech_stack: list = Column(
        JSONB,
        default=list,
        nullable=False,
        server_default='[]',
        comment='e.g. ["React", "Python", "AWS"]',
    )

    # ── Monitoring ────────────────────────────────────────────────────────
    last_monitoring_run_at: Optional[datetime] = Column(DateTime, nullable=True)
    monitoring_enabled: bool = Column(Boolean, default=False, nullable=False)

    # ── Timestamps ────────────────────────────────────────────────────────
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: datetime = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # ── Relationships ─────────────────────────────────────────────────────
    prospects = relationship("Prospect", back_populates="company", lazy="select")
    documents = relationship("Document", back_populates="company", lazy="select")

    # ── Table constraints ─────────────────────────────────────────────────
    __table_args__ = (
        CheckConstraint("headcount > 0 OR headcount IS NULL", name="ck_company_headcount"),
        Index("idx_companies_user", "user_id"),
        Index("idx_companies_domain", "domain"),
        Index("idx_companies_funding", "funding_stage"),
        Index(
            "idx_companies_monitoring",
            "monitoring_enabled",
            "last_monitoring_run_at",
        ),
    )

    def __repr__(self) -> str:
        return f"<Company id={self.company_id} name={self.name!r}>"
