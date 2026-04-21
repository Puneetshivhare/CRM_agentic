"""
app/models/campaign.py — Email campaign and sequence management.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, ForeignKey, JSON, Text
from app.database import Base


class Campaign(Base):
    """Multi-touch email campaign."""

    __tablename__ = "dim_campaigns"

    campaign_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Campaign config
    sequence_steps = Column(JSON, nullable=False)  # List of {day: int, subject: str, body: str}
    target_criteria = Column(JSON, nullable=True)  # Filters for prospects to enroll
    is_active = Column(Boolean, nullable=False, default=True, index=True)

    # Stats
    enrolled_count = Column(Integer, nullable=False, default=0)
    opened_count = Column(Integer, nullable=False, default=0)
    clicked_count = Column(Integer, nullable=False, default=0)
    replied_count = Column(Integer, nullable=False, default=0)
    conversion_rate = Column(Float, nullable=False, default=0.0)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
