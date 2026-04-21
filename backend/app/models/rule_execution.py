"""
app/models/rule_execution.py — Track automation rule executions.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, JSON, Text
from app.database import Base


class RuleExecution(Base):
    """Log of when rules are triggered and what they do."""

    __tablename__ = "fact_rule_executions"

    execution_id = Column(Integer, primary_key=True, autoincrement=True)
    rule_id = Column(Integer, ForeignKey("dim_rules.rule_id"), nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)

    # Context
    prospect_id = Column(Integer, nullable=True, index=True)
    company_id = Column(Integer, nullable=True, index=True)
    trigger_event = Column(String(100), nullable=False)  # enrichment_complete, email_opened, etc.

    # Execution
    triggered = Column(Boolean, nullable=False, default=False)
    action_taken = Column(String(255), nullable=True)
    result = Column(String(50), nullable=False, default="pending")  # pending|success|failed

    # Details
    trigger_data = Column(JSON, nullable=True)
    action_result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
