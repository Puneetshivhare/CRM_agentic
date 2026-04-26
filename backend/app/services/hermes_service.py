"""
app/services/hermes_service.py — Hermes Agent SaaS Integration Service.

Responsibilities:
  - Manage per-tenant Hermes containers
  - Enforce guardrails and scope restrictions
  - Route CRM tasks to Hermes via REST API
  - Handle tenant isolation for skills and memory
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Optional

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.agent_execution import AgentExecution
from app.models.hermes_tenant import HermesTenant, HermesExecution

logger = logging.getLogger("agentic_crm")


class HermesGuardrails:
    """Guardrails configuration for restricted operations."""
    
    ALLOWED_ACTIONS = {
        "web_search",
        "web_crawl",
        "prospect_research",
        "company_enrichment",
        "document_summarization",
        "crm_query",
        "mcp_invoke",
    }
    
    BLOCKED_ACTIONS = {
        "bash_execution",
        "python_execution",
        "file_system_write",
        "system_commands",
        "network_scanning",
        "code_interpreter",
        "terminal_access",
        "ssh_connect",
    }
    
    ALLOWED_MCP_SERVERS = {
        "crm_backend",
        "graphify",
        "web_search",
    }
    
    BLOCKED_MCP_SERVERS = {
        "filesystem",
        "terminal",
        "bash",
        "python",
        "system",
    }


class HermesTenantManager:
    """Manages per-tenant Hermes containers and configuration."""
    
    def __init__(self):
        self.base_url = getattr(settings, 'hermes_base_url', 'http://hermes:8000')
        self.docker_network = getattr(settings, 'docker_network', 'agentic-crm_default')
        
    async def provision_tenant(self, tenant_id: str, tenant_name: str) -> dict:
        """
        Provision a new Hermes container for a tenant.
        
        Args:
            tenant_id: Unique tenant identifier
            tenant_name: Human-readable tenant name
            
        Returns:
            Dict with container info and API endpoint
        """
        container_name = f"hermes-tenant-{tenant_id}"
        
        config = {
            "tenant_id": tenant_id,
            "tenant_name": tenant_name,
            "container_name": container_name,
            "api_port": self._get_tenant_port(tenant_id),
            "guardrails": {
                "allowed_actions": list(HermesGuardrails.ALLOWED_ACTIONS),
                "blocked_actions": list(HermesGuardrails.BLOCKED_ACTIONS),
                "allowed_mcp_servers": list(HermesGuardrails.ALLOWED_MCP_SERVERS),
                "blocked_mcp_servers": list(HermesGuardrails.BLOCKED_MCP_SERVERS),
            },
            "isolated_skills": True,
            "isolated_memory": True,
            "mcp_endpoints": {
                "crm_backend": f"http://backend:8000/api/mcp",
                "graphify": getattr(settings, 'graphify_url', ''),
            }
        }
        
        logger.info(f"[Hermes] Provisioning tenant {tenant_id}: {tenant_name}")
        
        # In production, this would call Docker API to spin up container
        # For now, return config for shared container setup
        return {
            "status": "provisioned",
            "tenant_id": tenant_id,
            "container_name": container_name,
            "api_endpoint": f"{self.base_url}/tenant/{tenant_id}",
            "config": config,
        }
    
    def _get_tenant_port(self, tenant_id: str) -> int:
        """Generate a consistent port number for tenant container."""
        # Hash tenant_id to get port in range 9000-9999
        import hashlib
        hash_val = int(hashlib.md5(tenant_id.encode()).hexdigest(), 16)
        return 9000 + (hash_val % 1000)


class HermesService:
    """Service for interacting with Hermes Agent via REST API."""
    
    def __init__(self, db: Session = None):
        self.db = db
        self.base_url = getattr(settings, 'hermes_base_url', 'http://hermes:8000')
        self.timeout = 120.0  # 2 minutes for research tasks
        self.guardrails = HermesGuardrails()
        
    async def execute_research_task(
        self,
        tenant_id: str,
        user_id: int,
        task_type: str,
        context: dict,
        prospect_id: Optional[int] = None,
        company_id: Optional[int] = None,
    ) -> dict:
        """
        Execute a research task via Hermes Agent.
        
        Args:
            tenant_id: Tenant identifier for isolation
            user_id: User who owns this task
            task_type: Type of task (web_search, enrichment, etc.)
            context: Task context (prospect data, company info, etc.)
            prospect_id: Optional prospect ID to link
            company_id: Optional company ID to link
            
        Returns:
            Dict with results and execution metadata
        """
        task_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        # Validate task against guardrails
        if not self._validate_task(task_type, context):
            return {
                "status": "blocked",
                "error": f"Task '{task_type}' blocked by guardrails",
                "task_id": task_id,
            }
        
        # Log execution start
        execution = HermesExecution(
            tenant_id=tenant_id,
            user_id=user_id,
            hermes_task_id=task_id,
            task_type=task_type,
            status="running",
            input_data=context,
            start_time=start_time,
            prospect_id=prospect_id,
            company_id=company_id,
        )
        self.db.add(execution)
        self.db.commit()
        
        try:
            # Build Hermes API request
            payload = {
                "task_id": task_id,
                "tenant_id": tenant_id,
                "task_type": task_type,
                "context": context,
                "guardrails": {
                    "allowed_actions": list(self.guardrails.ALLOWED_ACTIONS),
                    "blocked_actions": list(self.guardrails.BLOCKED_ACTIONS),
                },
                "mcp_context": {
                    "user_id": user_id,
                    "prospect_id": prospect_id,
                    "company_id": company_id,
                }
            }
            
            # Call Hermes REST API
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/tasks",
                    json=payload,
                    headers={
                        "X-Tenant-ID": tenant_id,
                        "X-API-Key": getattr(settings, 'hermes_api_key', ''),
                    }
                )
                response.raise_for_status()
                result = response.json()
            
            # Update execution record
            execution.status = result.get("status", "completed")
            execution.output_data = result.get("data", {})
            execution.end_time = datetime.utcnow()
            execution.tokens_used = result.get("tokens_used", 0)
            execution.memory_hits = result.get("memory_hits", 0)
            self.db.commit()
            
            logger.info(
                f"[Hermes] Task {task_id} completed: {execution.status}"
            )
            
            return {
                "status": execution.status,
                "task_id": task_id,
                "data": result.get("data", {}),
                "execution_id": execution.execution_id,
            }
            
        except httpx.TimeoutException:
            execution.status = "timeout"
            execution.end_time = datetime.utcnow()
            execution.error_message = "Hermes task timed out"
            self.db.commit()
            
            logger.error(f"[Hermes] Task {task_id} timed out")
            return {
                "status": "timeout",
                "error": "Task execution exceeded timeout",
                "task_id": task_id,
            }
            
        except Exception as e:
            execution.status = "failed"
            execution.end_time = datetime.utcnow()
            execution.error_message = str(e)
            self.db.commit()
            
            logger.error(f"[Hermes] Task {task_id} failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "task_id": task_id,
            }
    
    async def enrich_prospect(
        self,
        tenant_id: str,
        user_id: int,
        prospect_id: int,
        company_domain: Optional[str] = None,
    ) -> dict:
        """
        Enrich a prospect using Hermes web research.
        
        Args:
            tenant_id: Tenant identifier
            user_id: User who owns the prospect
            prospect_id: Prospect to enrich
            company_domain: Optional company domain to research
            
        Returns:
            Enrichment results
        """
        # Get prospect data from CRM
        from app.models.prospect import Prospect
        
        prospect = (
            self.db.query(Prospect)
            .filter(Prospect.prospect_id == prospect_id)
            .first()
        )
        
        if not prospect:
            return {"status": "failed", "error": "Prospect not found"}
        
        context = {
            "prospect_name": f"{prospect.first_name or ''} {prospect.last_name or ''}".strip(),
            "prospect_email": prospect.email,
            "prospect_title": prospect.title,
            "company_domain": company_domain or prospect.company.domain if prospect.company else None,
            "enrichment_goal": "Find company information, role details, and recent activity",
        }
        
        return await self.execute_research_task(
            tenant_id=tenant_id,
            user_id=user_id,
            task_type="prospect_research",
            context=context,
            prospect_id=prospect_id,
            company_id=prospect.company_id,
        )
    
    async def search_and_crawl(
        self,
        tenant_id: str,
        user_id: int,
        query: str,
        max_results: int = 5,
    ) -> dict:
        """
        Perform web search and crawl via Hermes.
        
        Args:
            tenant_id: Tenant identifier
            user_id: User who owns the search
            query: Search query
            max_results: Maximum results to return
            
        Returns:
            Search results with crawled content
        """
        context = {
            "search_query": query,
            "max_results": max_results,
            "crawl_depth": "shallow",  # Guardrails: no deep crawling
            "extract_structured": True,
        }
        
        return await self.execute_research_task(
            tenant_id=tenant_id,
            user_id=user_id,
            task_type="web_search",
            context=context,
        )
    
    def _validate_task(self, task_type: str, context: dict) -> bool:
        """Validate task against guardrails."""
        # Check if task type is allowed
        if task_type not in self.guardrails.ALLOWED_ACTIONS:
            logger.warning(f"[Hermes] Task type '{task_type}' blocked by guardrails")
            return False
        
        # Check for blocked keywords in context
        context_str = json.dumps(context).lower()
        for blocked in self.guardrails.BLOCKED_ACTIONS:
            if blocked.lower() in context_str:
                logger.warning(f"[Hermes] Blocked keyword '{blocked}' found in context")
                return False
        
        return True
    
    async def get_tenant_status(self, tenant_id: str) -> dict:
        """Get Hermes status for a tenant."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/tenant/{tenant_id}/status",
                    headers={"X-Tenant-ID": tenant_id},
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"[Hermes] Failed to get tenant status: {e}")
            return {"status": "unavailable", "error": str(e)}
    
    async def get_tenant_skills(self, tenant_id: str) -> list:
        """Get learned skills for a tenant."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/tenant/{tenant_id}/skills",
                    headers={"X-Tenant-ID": tenant_id},
                )
                response.raise_for_status()
                return response.json().get("skills", [])
        except Exception as e:
            logger.error(f"[Hermes] Failed to get tenant skills: {e}")
            return []


# Module-level instance
hermes_service = HermesService()
hermes_tenant_manager = HermesTenantManager()
