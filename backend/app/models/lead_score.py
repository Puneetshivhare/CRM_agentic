"""
app/models/lead_score.py — Lead scoring for sales prioritization.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Boolean, Index
from app.database import Base


class LeadScore(Base):
    """Lead score calculated from company firmographics and prospect signals."""

    __tablename__ = "fact_lead_scores"

    score_id = Column(Integer, primary_key=True, autoincrement=True)
    prospect_id = Column(Integer, ForeignKey("dim_prospects.prospect_id"), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("dim_companies.company_id"), nullable=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)

    # Score components
    fit_score = Column(Float, nullable=False, default=0.0)  # Company fit (0-100): industry, size, stage
    engagement_score = Column(Float, nullable=False, default=0.0)  # Behavioral (0-100): opens, clicks, replies
    propensity_score = Column(Float, nullable=False, default=0.0)  # Conversion likelihood (0-100)

    # Composite score
    total_score = Column(Float, nullable=False, default=0.0)  # Weighted average (0-100)
    grade = Column(String(1), nullable=False, default="F")  # A, B, C, D, F

    # Scoring details
    score_breakdown = Column(JSON, nullable=True)  # { "industry": 85, "size": 70, "stage": 80, "emails_opened": 2, "links_clicked": 1 }
    signals = Column(JSON, nullable=True)  # Array of [{signal_type, value, weight}]

    is_hot_lead = Column(Boolean, nullable=False, default=False)  # Score >= 80
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes for fast queries
    __table_args__ = (
        Index("idx_lead_score_user_prospect", "user_id", "prospect_id"),
        Index("idx_lead_score_total", "total_score"),
        Index("idx_lead_score_grade", "grade"),
    )
