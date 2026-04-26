"""
app/models/hermes_tenant.py — Hermes tenant models for SaaS multi-tenancy.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class HermesTenant(Base):
    """Configuration for Hermes per-tenant setup."""
    
    __tablename__ = "hermes_tenants"
    
    tenant_id = Column(String(64), primary_key=True)
    tenant_name = Column(String(255), nullable=False)
    
    # Container info
    container_name = Column(String(255))
    api_endpoint = Column(String(500))
    
    # Guardrails config
    allowed_actions = Column(JSON, default=list)
    blocked_actions = Column(JSON, default=list)
    allowed_mcp_servers = Column(JSON, default=list)
    
    # Status
    status = Column(String(50), default="provisioning")  # provisioning, active, suspended
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    executions = relationship("HermesExecution", back_populates="tenant")
    skills = relationship("HermesSkill", back_populates="tenant")


class HermesExecution(Base):
    """Execution log for Hermes tasks."""
    
    __tablename__ = "hermes_executions"
    
    execution_id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(64), ForeignKey("hermes_tenants.tenant_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("auth_users.user_id"), nullable=False)
    
    # Hermes task tracking
    hermes_task_id = Column(String(64), nullable=False, index=True)
    task_type = Column(String(100), nullable=False)
    
    # Status
    status = Column(String(50), default="running")  # running, completed, failed, timeout, blocked
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    
    # Data
    input_data = Column(JSON)
    output_data = Column(JSON)
    
    # Metrics
    tokens_used = Column(Integer, default=0)
    memory_hits = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    
    # CRM linkage - using integer fields without relationships to avoid circular imports
    prospect_id = Column(Integer, nullable=True)
    company_id = Column(Integer, nullable=True)
    
    # Relationships - only to tenant to avoid complex FK issues
    tenant = relationship("HermesTenant", back_populates="executions")


class HermesSkill(Base):
    """Skills learned by Hermes per tenant."""
    
    __tablename__ = "hermes_skills"
    
    skill_id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(64), ForeignKey("hermes_tenants.tenant_id"), nullable=False)
    
    skill_name = Column(String(255), nullable=False)
    skill_type = Column(String(100), nullable=False)
    
    # Skill content (follows agentskills.io standard)
    skill_definition = Column(JSON)
    description = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    usage_count = Column(Integer, default=0)
    success_rate = Column(String(10), default="0%")
    
    # Relationships
    tenant = relationship("HermesTenant", back_populates="skills")
