"""
app/routes/hermes.py — API routes for Hermes Agent integration.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.auth import AuthUser
from app.models.hermes_tenant import HermesTenant, HermesExecution, HermesSkill
from app.services.hermes_service import hermes_service, hermes_tenant_manager

logger = logging.getLogger("agentic_crm")

router = APIRouter(prefix="/hermes", tags=["Hermes Agent"])


# ─── Request/Response Models ───────────────────────────────────────────────────

class TenantProvisionRequest(BaseModel):
    tenant_id: str = Field(..., description="Unique tenant identifier")
    tenant_name: str = Field(..., description="Human-readable tenant name")


class TenantProvisionResponse(BaseModel):
    status: str
    tenant_id: str
    container_name: str
    api_endpoint: str
    message: str


class ResearchTaskRequest(BaseModel):
    task_type: str = Field(..., description="Type of task: web_search, prospect_research, company_enrichment")
    context: dict = Field(default_factory=dict, description="Task context")
    prospect_id: Optional[int] = Field(None, description="Optional prospect ID to link")
    company_id: Optional[int] = Field(None, description="Optional company ID to link")


class ResearchTaskResponse(BaseModel):
    status: str
    task_id: str
    data: dict = Field(default_factory=dict)
    execution_id: Optional[int] = None
    error: Optional[str] = None


class EnrichProspectRequest(BaseModel):
    prospect_id: int = Field(..., description="Prospect to enrich")
    company_domain: Optional[str] = Field(None, description="Override company domain")


class EnrichProspectResponse(BaseModel):
    status: str
    task_id: str
    data: dict = Field(default_factory=dict)
    execution_id: int
    error: Optional[str] = None


class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    max_results: int = Field(5, ge=1, le=10, description="Maximum results (1-10)")


class TenantStatusResponse(BaseModel):
    tenant_id: str
    status: str
    container_name: Optional[str]
    active_executions: int
    total_executions: int
    skills_count: int


class SkillResponse(BaseModel):
    skill_id: int
    skill_name: str
    skill_type: str
    description: str
    usage_count: int
    success_rate: str
    created_at: str


class ExecutionResponse(BaseModel):
    execution_id: int
    task_id: str
    task_type: str
    status: str
    start_time: str
    end_time: Optional[str]
    tokens_used: int
    memory_hits: int
    error_message: Optional[str]


# ─── Routes ───────────────────────────────────────────────────────────────────

@router.post(
    "/tenants/provision",
    response_model=TenantProvisionResponse,
    summary="Provision Hermes for a tenant",
    description="Creates a new Hermes container instance for a tenant with isolated skills and memory.",
)
async def provision_tenant(
    request: TenantProvisionRequest,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
) -> TenantProvisionResponse:
    """Provision Hermes container for a tenant."""
    
    # Check if tenant already exists
    existing = db.query(HermesTenant).filter(
        HermesTenant.tenant_id == request.tenant_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Tenant {request.tenant_id} already provisioned",
        )
    
    # Provision via manager
    result = await hermes_tenant_manager.provision_tenant(
        tenant_id=request.tenant_id,
        tenant_name=request.tenant_name,
    )
    
    # Create tenant record
    tenant = HermesTenant(
        tenant_id=request.tenant_id,
        tenant_name=request.tenant_name,
        container_name=result["container_name"],
        api_endpoint=result["api_endpoint"],
        status="active",
        allowed_actions=result["config"]["guardrails"]["allowed_actions"],
        blocked_actions=result["config"]["guardrails"]["blocked_actions"],
        allowed_mcp_servers=result["config"]["guardrails"]["allowed_mcp_servers"],
    )
    db.add(tenant)
    db.commit()
    
    logger.info(f"[Hermes] Provisioned tenant {request.tenant_id}")
    
    return TenantProvisionResponse(
        status="provisioned",
        tenant_id=request.tenant_id,
        container_name=result["container_name"],
        api_endpoint=result["api_endpoint"],
        message="Hermes tenant provisioned successfully",
    )


@router.get(
    "/tenants/{tenant_id}/status",
    response_model=TenantStatusResponse,
    summary="Get tenant Hermes status",
)
async def get_tenant_status(
    tenant_id: str,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
) -> TenantStatusResponse:
    """Get Hermes status for a tenant."""
    
    tenant = db.query(HermesTenant).filter(
        HermesTenant.tenant_id == tenant_id
    ).first()
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found",
        )
    
    # Count executions
    active_count = db.query(HermesExecution).filter(
        HermesExecution.tenant_id == tenant_id,
        HermesExecution.status == "running"
    ).count()
    
    total_count = db.query(HermesExecution).filter(
        HermesExecution.tenant_id == tenant_id
    ).count()
    
    skills_count = db.query(HermesSkill).filter(
        HermesSkill.tenant_id == tenant_id
    ).count()
    
    return TenantStatusResponse(
        tenant_id=tenant_id,
        status=tenant.status,
        container_name=tenant.container_name,
        active_executions=active_count,
        total_executions=total_count,
        skills_count=skills_count,
    )


@router.post(
    "/tasks/research",
    response_model=ResearchTaskResponse,
    summary="Execute research task",
    description="Execute a web research or enrichment task via Hermes.",
)
async def execute_research(
    tenant_id: str = Query(..., description="Tenant ID"),
    request: ResearchTaskRequest = None,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
) -> ResearchTaskResponse:
    """Execute a research task."""
    
    # Verify tenant exists
    tenant = db.query(HermesTenant).filter(
        HermesTenant.tenant_id == tenant_id
    ).first()
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found",
        )
    
    # Execute via service
    result = await hermes_service.execute_research_task(
        tenant_id=tenant_id,
        user_id=current_user.user_id,
        task_type=request.task_type,
        context=request.context,
        prospect_id=request.prospect_id,
        company_id=request.company_id,
    )
    
    return ResearchTaskResponse(
        status=result.get("status", "unknown"),
        task_id=result.get("task_id"),
        data=result.get("data", {}),
        execution_id=result.get("execution_id"),
        error=result.get("error"),
    )


@router.post(
    "/prospects/{prospect_id}/enrich",
    response_model=EnrichProspectResponse,
    summary="Enrich a prospect",
    description="Research and enrich a prospect using Hermes web search.",
)
async def enrich_prospect(
    prospect_id: int,
    tenant_id: str = Query(..., description="Tenant ID"),
    request: Optional[EnrichProspectRequest] = None,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
) -> EnrichProspectResponse:
    """Enrich a prospect via Hermes."""
    
    # Inject db into service
    hermes_service.db = db
    
    result = await hermes_service.enrich_prospect(
        tenant_id=tenant_id,
        user_id=current_user.user_id,
        prospect_id=prospect_id,
        company_domain=request.company_domain if request else None,
    )
    
    return EnrichProspectResponse(
        status=result.get("status", "unknown"),
        task_id=result.get("task_id", ""),
        data=result.get("data", {}),
        execution_id=result.get("execution_id", 0),
        error=result.get("error"),
    )


@router.post(
    "/search",
    response_model=ResearchTaskResponse,
    summary="Web search via Hermes",
    description="Perform web search and crawl via Hermes.",
)
async def web_search(
    tenant_id: str = Query(..., description="Tenant ID"),
    request: SearchRequest = None,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
) -> ResearchTaskResponse:
    """Search the web via Hermes."""
    
    hermes_service.db = db
    
    result = await hermes_service.search_and_crawl(
        tenant_id=tenant_id,
        user_id=current_user.user_id,
        query=request.query,
        max_results=request.max_results,
    )
    
    return ResearchTaskResponse(
        status=result.get("status", "unknown"),
        task_id=result.get("task_id", ""),
        data=result.get("data", {}),
        execution_id=result.get("execution_id"),
        error=result.get("error"),
    )


@router.get(
    "/tenants/{tenant_id}/skills",
    response_model=list[SkillResponse],
    summary="Get tenant skills",
)
async def get_tenant_skills(
    tenant_id: str,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
) -> list[SkillResponse]:
    """Get skills learned by Hermes for a tenant."""
    
    skills = db.query(HermesSkill).filter(
        HermesSkill.tenant_id == tenant_id
    ).order_by(HermesSkill.usage_count.desc()).all()
    
    return [
        SkillResponse(
            skill_id=skill.skill_id,
            skill_name=skill.skill_name,
            skill_type=skill.skill_type,
            description=skill.description or "",
            usage_count=skill.usage_count,
            success_rate=skill.success_rate,
            created_at=skill.created_at.isoformat() if skill.created_at else "",
        )
        for skill in skills
    ]


@router.get(
    "/tenants/{tenant_id}/executions",
    response_model=list[ExecutionResponse],
    summary="Get execution history",
)
async def get_executions(
    tenant_id: str,
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
) -> list[ExecutionResponse]:
    """Get execution history for a tenant."""
    
    query = db.query(HermesExecution).filter(
        HermesExecution.tenant_id == tenant_id
    )
    
    if status:
        query = query.filter(HermesExecution.status == status)
    
    executions = query.order_by(
        HermesExecution.start_time.desc()
    ).offset(offset).limit(limit).all()
    
    return [
        ExecutionResponse(
            execution_id=exec.execution_id,
            task_id=exec.hermes_task_id,
            task_type=exec.task_type,
            status=exec.status,
            start_time=exec.start_time.isoformat() if exec.start_time else "",
            end_time=exec.end_time.isoformat() if exec.end_time else None,
            tokens_used=exec.tokens_used or 0,
            memory_hits=exec.memory_hits or 0,
            error_message=exec.error_message,
        )
        for exec in executions
    ]
