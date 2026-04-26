"""
hermes_app/config.py — Configuration for Hermes SaaS.
"""

import os
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Hermes SaaS settings."""
    
    # Core
    mode: str = Field(default="saas", description="Hermes mode: saas, single")
    tenant_isolation: str = Field(default="strict", description="Tenant isolation level")
    
    # Paths
    data_dir: str = Field(default="/app/data")
    skills_dir: str = Field(default="/app/skills")
    tenants_dir: str = Field(default="/app/tenants")
    
    # Database (shared with CRM)
    database_url: str = Field(default="")
    
    # Redis
    redis_url: str = Field(default="redis://redis:6379/1")
    
    # API Keys
    brave_search_api_key: str = Field(default="")
    gemini_api_key: str = Field(default="")
    
    # CRM Integration
    crm_backend_url: str = Field(default="http://backend:8000/api")
    crm_api_key: str = Field(default="")
    
    # Graphify
    graphify_enabled: bool = Field(default=True)
    graphify_url: str = Field(default="")
    
    # Security
    api_key: str = Field(default="")
    cors_origins: str = Field(default="http://localhost:3005,http://localhost:8005")
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore",
    }


settings = Settings()
