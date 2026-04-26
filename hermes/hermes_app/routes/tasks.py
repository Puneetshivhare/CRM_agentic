"""
hermes_app/routes/tasks.py — Task execution routes.
"""

import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from hermes_app.config import settings
from hermes_app.guardrails import GuardrailsManager
from hermes_app.services.research_service import ResearchService

logger = logging.getLogger("hermes")

router = APIRouter(prefix="/tasks", tags=["Tasks"])


class TaskRequest(BaseModel):
    """Task execution request."""
    task_id: Optional[str] = Field(default=None)
    tenant_id: str = Field(..., description="Tenant identifier")
    task_type: str = Field(..., description="Type of task")
    context: dict = Field(default_factory=dict)
    guardrails: dict = Field(default_factory=dict)
    mcp_context: dict = Field(default_factory=dict)


class TaskResponse(BaseModel):
    """Task execution response."""
    status: str
    task_id: str
    data: dict = Field(default_factory=dict)
    tokens_used: int = 0
    memory_hits: int = 0
    error: Optional[str] = None


def get_guardrails(request: Request) -> GuardrailsManager:
    """Dependency to get guardrails from app state."""
    return request.app.state.guardrails


@router.post(
    "/",
    response_model=TaskResponse,
    summary="Execute task",
    description="Execute a research or enrichment task with guardrails enforced.",
)
async def execute_task(
    request: TaskRequest,
    guardrails: GuardrailsManager = Depends(get_guardrails),
) -> TaskResponse:
    """Execute a task with guardrail validation."""
    
    # Generate task ID if not provided
    task_id = request.task_id or str(uuid.uuid4())
    
    logger.info(
        f"[Hermes] Task {task_id}: {request.task_type} for tenant {request.tenant_id}"
    )
    
    # ─── Guardrail Validation ────────────────────────────────────────────────
    
    # 1. Check action is allowed
    if not guardrails.is_action_allowed(request.task_type):
        logger.warning(f"[Guardrails] Blocked task type: {request.task_type}")
        return TaskResponse(
            status="blocked",
            task_id=task_id,
            error=f"Task type '{request.task_type}' is not allowed",
        )
    
    # 2. Validate search queries if present
    if "search_query" in request.context:
        is_valid, error_msg = guardrails.validate_search_query(
            request.context["search_query"]
        )
        if not is_valid:
            logger.warning(f"[Guardrails] Blocked search query: {error_msg}")
            return TaskResponse(
                status="blocked",
                task_id=task_id,
                error=error_msg,
            )
    
    # 3. Validate domains if present
    if "company_domain" in request.context:
        domain = request.context["company_domain"]
        if not guardrails.is_domain_allowed(domain):
            return TaskResponse(
                status="blocked",
                task_id=task_id,
                error=f"Domain '{domain}' is not allowed",
            )
    
    # ─── Task Execution ─────────────────────────────────────────────────────
    
    try:
        research_service = ResearchService(
            tenant_id=request.tenant_id,
            guardrails=guardrails,
        )
        
        if request.task_type == "web_search":
            result = await research_service.web_search(
                query=request.context.get("search_query", ""),
                max_results=request.context.get("max_results", 5),
            )
            
        elif request.task_type == "web_crawl":
            result = await research_service.web_crawl(
                url=request.context.get("url"),
                depth=request.context.get("depth", 1),
            )
            
        elif request.task_type == "prospect_research":
            result = await research_service.research_prospect(
                prospect_name=request.context.get("prospect_name"),
                company_domain=request.context.get("company_domain"),
                enrichment_goal=request.context.get("enrichment_goal", ""),
            )
            
        elif request.task_type == "company_enrichment":
            result = await research_service.enrich_company(
                domain=request.context.get("company_domain"),
                company_name=request.context.get("company_name"),
            )
            
        else:
            return TaskResponse(
                status="error",
                task_id=task_id,
                error=f"Unknown task type: {request.task_type}",
            )
        
        return TaskResponse(
            status="completed",
            task_id=task_id,
            data=result.get("data", {}),
            tokens_used=result.get("tokens_used", 0),
            memory_hits=result.get("memory_hits", 0),
        )
        
    except Exception as e:
        logger.error(f"[Hermes] Task {task_id} failed: {e}")
        return TaskResponse(
            status="failed",
            task_id=task_id,
            error=str(e),
        )


@router.get(
    "/{task_id}/status",
    summary="Get task status",
)
async def get_task_status(task_id: str) -> dict:
    """Get status of a running or completed task."""
    # In production, query from database/Redis
    return {
        "task_id": task_id,
        "status": "unknown",  # Would query actual status
        "timestamp": datetime.utcnow().isoformat(),
    }
