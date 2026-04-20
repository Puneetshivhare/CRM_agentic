"""
app/routes/companies.py — REST API endpoints for company management.

Endpoints:
  GET    /api/companies              — List companies (search, pagination)
  GET    /api/companies/{id}         — Get single company with prospects
  POST   /api/companies              — Create company
  PUT    /api/companies/{id}         — Update company
  DELETE /api/companies/{id}         — Delete company
  POST   /api/companies/{id}/monitor — Toggle monitoring on/off
  GET    /api/companies/{id}/signals — Get latest MonitoringAgent output
"""

import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, desc, or_
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.auth import get_current_user
from app.database import get_db
from app.models.company import Company
from app.models.prospect import Prospect
from app.models.agent_execution import AgentExecution

logger = logging.getLogger("agentic_crm")
router = APIRouter(prefix="/api/companies", tags=["companies"])


# ── Pydantic Schemas ──────────────────────────────────────────────────

class CompanyBase(BaseModel):
    name: str = Field(..., max_length=500)
    domain: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    headcount: Optional[int] = None
    headcount_range: Optional[str] = Field(None, max_length=50)
    revenue_annual: Optional[float] = None
    funding_stage: Optional[str] = Field(None, max_length=100)
    headquarters_city: Optional[str] = Field(None, max_length=255)
    headquarters_country: Optional[str] = Field(None, max_length=255)
    industry: Optional[str] = Field(None, max_length=255)
    tech_stack: Optional[list[str]] = None
    monitoring_enabled: bool = False


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    description: Optional[str] = None
    headcount: Optional[int] = None
    headcount_range: Optional[str] = None
    revenue_annual: Optional[float] = None
    funding_stage: Optional[str] = None
    headquarters_city: Optional[str] = None
    headquarters_country: Optional[str] = None
    industry: Optional[str] = None
    tech_stack: Optional[list[str]] = None
    monitoring_enabled: Optional[bool] = None


class CompanyResponse(CompanyBase):
    company_id: int
    user_id: int
    last_monitoring_run_at: Optional[str] = None
    created_at: str
    updated_at: str
    prospects_count: int = 0

    class Config:
        from_attributes = True


class PaginatedCompaniesResponse(BaseModel):
    total: int
    page: int
    per_page: int
    items: list[CompanyResponse]


class MonitorSignal(BaseModel):
    agent_type: str
    status: str
    execution_id: int
    duration_ms: Optional[int] = None
    decision_description: Optional[str] = None
    confidence_score: Optional[float] = None
    created_at: str

    class Config:
        from_attributes = True


# ── Helper Functions ──────────────────────────────────────────────────

def get_current_user_id(user: Annotated[dict, Depends(get_current_user)]) -> int:
    """Extract user_id from validated JWT token."""
    return user["user_id"]


# ── Endpoints ─────────────────────────────────────────────────────────

@router.get("", response_model=PaginatedCompaniesResponse)
async def list_companies(
    search: Optional[str] = Query(None, description="Search by name or domain"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> PaginatedCompaniesResponse:
    """List companies for the current user."""
    query = db.query(Company).filter(Company.user_id == user_id)

    if search:
        query = query.filter(
            or_(
                Company.name.ilike(f"%{search}%"),
                Company.domain.ilike(f"%{search}%"),
            )
        )

    total = query.count()
    companies = (
        query.order_by(desc(Company.created_at))
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    items = []
    for company in companies:
        prospects_count = (
            db.query(Prospect)
            .filter(Prospect.company_id == company.company_id)
            .count()
        )
        response = CompanyResponse.from_orm(company)
        response.prospects_count = prospects_count
        items.append(response)

    return PaginatedCompaniesResponse(
        total=total,
        page=page,
        per_page=per_page,
        items=items,
    )


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> CompanyResponse:
    """Get a single company with its prospects."""
    company = (
        db.query(Company)
        .filter(and_(Company.company_id == company_id, Company.user_id == user_id))
        .first()
    )

    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    prospects_count = (
        db.query(Prospect)
        .filter(Prospect.company_id == company.company_id)
        .count()
    )

    response = CompanyResponse.from_orm(company)
    response.prospects_count = prospects_count
    return response


@router.post("", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def create_company(
    request: CompanyCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> CompanyResponse:
    """Create a new company."""
    # Check if domain already exists for this user
    if request.domain:
        existing = (
            db.query(Company)
            .filter(
                and_(
                    Company.domain == request.domain,
                    Company.user_id == user_id,
                )
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Company with this domain already exists",
            )

    company = Company(
        user_id=user_id,
        name=request.name,
        domain=request.domain,
        description=request.description,
        headcount=request.headcount,
        headcount_range=request.headcount_range,
        revenue_annual=request.revenue_annual,
        funding_stage=request.funding_stage,
        headquarters_city=request.headquarters_city,
        headquarters_country=request.headquarters_country,
        industry=request.industry,
        tech_stack=request.tech_stack or [],
        monitoring_enabled=request.monitoring_enabled,
    )

    db.add(company)
    db.commit()
    db.refresh(company)

    logger.info(f"Created company {company.company_id} for user {user_id}")
    return CompanyResponse.from_orm(company)


@router.put("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: int,
    request: CompanyUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> CompanyResponse:
    """Update a company."""
    company = (
        db.query(Company)
        .filter(and_(Company.company_id == company_id, Company.user_id == user_id))
        .first()
    )

    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    # Update fields
    for field, value in request.dict(exclude_unset=True).items():
        setattr(company, field, value)

    db.commit()
    db.refresh(company)

    logger.info(f"Updated company {company_id} for user {user_id}")
    return CompanyResponse.from_orm(company)


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(
    company_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> None:
    """Delete a company and its associated prospects."""
    company = (
        db.query(Company)
        .filter(and_(Company.company_id == company_id, Company.user_id == user_id))
        .first()
    )

    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    db.delete(company)
    db.commit()

    logger.info(f"Deleted company {company_id} for user {user_id}")


@router.post("/{company_id}/monitor", response_model={"status": str, "monitoring_enabled": bool})
async def toggle_monitoring(
    company_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> dict:
    """Toggle monitoring on/off for a company."""
    company = (
        db.query(Company)
        .filter(and_(Company.company_id == company_id, Company.user_id == user_id))
        .first()
    )

    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    company.monitoring_enabled = not company.monitoring_enabled
    db.commit()

    logger.info(
        f"Toggled monitoring to {company.monitoring_enabled} for company {company_id}"
    )

    return {
        "status": "success",
        "monitoring_enabled": company.monitoring_enabled,
    }


@router.get("/{company_id}/signals", response_model=list[MonitorSignal])
async def get_company_signals(
    company_id: int,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> list[MonitorSignal]:
    """Get latest MonitoringAgent executions for a company."""
    # Verify company ownership
    company = (
        db.query(Company)
        .filter(and_(Company.company_id == company_id, Company.user_id == user_id))
        .first()
    )

    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    # Get latest agent executions
    executions = (
        db.query(AgentExecution)
        .filter(
            and_(
                AgentExecution.company_id == company_id,
                AgentExecution.agent_type == "MonitoringAgent",
            )
        )
        .order_by(desc(AgentExecution.created_at))
        .limit(limit)
        .all()
    )

    return [MonitorSignal.from_orm(e) for e in executions]
