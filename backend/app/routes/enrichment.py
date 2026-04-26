"""Minimal enrichment endpoints for the current frontend contract."""

import logging
from datetime import datetime
from typing import Annotated, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.agent_execution import AgentExecution
from app.models.company import Company
from app.models.enrichment_event import EnrichmentEvent
from app.models.prospect import Prospect
from app.services.search_service import search_service
from app.utils.logger import trace_logic

logger = logging.getLogger("agentic_crm")
router = APIRouter(prefix="/api/enrichment", tags=["enrichment"])


class EnrichmentTriggerRequest(BaseModel):
    prospect_id: int = Field(..., description="Prospect to enrich")


class EnrichmentTriggerResponse(BaseModel):
    execution_id: int
    prospect_id: int
    status: str
    message: str


class SearchEnrichmentTriggerRequest(BaseModel):
    prospect_id: int = Field(..., description="Prospect to enrich via search")
    limit: int = Field(default=3, ge=1, le=5)


class ProspectEnrichmentStatusResponse(BaseModel):
    prospect_id: int
    enrichment_status: str
    enrichment_confidence: float
    last_execution_id: Optional[int]
    last_execution_status: Optional[str]
    last_execution_time: Optional[datetime]
    recent_events: int


class ExecutionListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    execution_id: int
    agent_type: str
    status: str
    prospect_id: Optional[int] = None
    company_id: Optional[int] = None
    duration_ms: Optional[int] = None
    tokens_used: Optional[int] = None
    confidence_score: Optional[float] = None
    decision_description: Optional[str] = None
    created_at: datetime
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class PaginatedExecutionsResponse(BaseModel):
    total: int
    page: int
    per_page: int
    items: list[ExecutionListResponse]


def get_current_user_id(user: Annotated[dict, Depends(get_current_user)]) -> int:
    return user["user_id"]


@router.post("/trigger", response_model=EnrichmentTriggerResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_enrichment(
    request: EnrichmentTriggerRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> EnrichmentTriggerResponse:
    trace_logic(logger, "enrichment.trigger.request", user_id=user_id, prospect_id=request.prospect_id)
    prospect = (
        db.query(Prospect)
        .filter(
            Prospect.prospect_id == request.prospect_id,
            Prospect.user_id == user_id,
        )
        .first()
    )
    if not prospect:
        raise HTTPException(status_code=404, detail=f"Prospect {request.prospect_id} not found")

    start_time = datetime.utcnow()
    execution = AgentExecution(
        user_id=user_id,
        agent_type="EnrichmentAgent",
        agent_name="frontend-trigger",
        task_id=str(uuid4()),
        prospect_id=prospect.prospect_id,
        status="running",
        input_data={"source": "frontend", "prospect_id": prospect.prospect_id},
        start_time=start_time,
        decision_description="Manual enrichment triggered from the dashboard",
        created_at=start_time,
    )
    db.add(execution)
    db.flush()

    previous_status = prospect.enrichment_status
    previous_confidence = prospect.enrichment_confidence

    prospect.enrichment_status = "enriched"
    prospect.enrichment_confidence = max(prospect.enrichment_confidence or 0.0, 0.6)

    db.add(
        EnrichmentEvent(
            prospect_id=prospect.prospect_id,
            field_name="enrichment_status",
            old_value=previous_status,
            new_value=prospect.enrichment_status,
            agent_name="EnrichmentAgent",
            confidence_score=prospect.enrichment_confidence,
            source="manual_trigger",
        )
    )

    if prospect.enrichment_confidence != previous_confidence:
        db.add(
            EnrichmentEvent(
                prospect_id=prospect.prospect_id,
                field_name="enrichment_confidence",
                old_value=str(previous_confidence),
                new_value=str(prospect.enrichment_confidence),
                agent_name="EnrichmentAgent",
                confidence_score=prospect.enrichment_confidence,
                source="manual_trigger",
            )
        )

    end_time = datetime.utcnow()
    execution.status = "success"
    execution.end_time = end_time
    execution.duration_ms = int((end_time - start_time).total_seconds() * 1000)
    execution.confidence_score = prospect.enrichment_confidence
    execution.output_data = {
        "prospect_id": prospect.prospect_id,
        "enrichment_status": prospect.enrichment_status,
        "enrichment_confidence": prospect.enrichment_confidence,
    }

    db.commit()
    db.refresh(execution)

    logger.info("Enrichment completed for prospect %s", prospect.prospect_id)
    trace_logic(
        logger,
        "enrichment.trigger.success",
        user_id=user_id,
        prospect_id=prospect.prospect_id,
        execution_id=execution.execution_id,
        confidence=prospect.enrichment_confidence,
    )
    return EnrichmentTriggerResponse(
        execution_id=execution.execution_id,
        prospect_id=prospect.prospect_id,
        status="success",
        message="Enrichment completed successfully.",
    )


@router.get("/executions", response_model=PaginatedExecutionsResponse)
async def list_agent_executions(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    agent_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> PaginatedExecutionsResponse:
    trace_logic(logger, "enrichment.executions.request", user_id=user_id, page=page, per_page=per_page, agent_type=agent_type, status=status)
    query = db.query(AgentExecution).filter(AgentExecution.user_id == user_id)
    if agent_type:
        query = query.filter(AgentExecution.agent_type == agent_type)
    if status:
        query = query.filter(AgentExecution.status == status)

    total = query.count()
    executions = (
        query.order_by(desc(AgentExecution.created_at))
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return PaginatedExecutionsResponse(
        total=total,
        page=page,
        per_page=per_page,
        items=[ExecutionListResponse.model_validate(execution) for execution in executions],
    )


@router.get("/status/{prospect_id}", response_model=ProspectEnrichmentStatusResponse)
async def get_prospect_enrichment_status(
    prospect_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> ProspectEnrichmentStatusResponse:
    prospect = (
        db.query(Prospect)
        .filter(
            Prospect.prospect_id == prospect_id,
            Prospect.user_id == user_id,
        )
        .first()
    )
    if not prospect:
        raise HTTPException(status_code=404, detail=f"Prospect {prospect_id} not found")

    latest_execution = (
        db.query(AgentExecution)
        .filter(AgentExecution.prospect_id == prospect_id)
        .order_by(desc(AgentExecution.created_at))
        .first()
    )
    recent_events = db.query(EnrichmentEvent).filter(EnrichmentEvent.prospect_id == prospect_id).count()

    return ProspectEnrichmentStatusResponse(
        prospect_id=prospect_id,
        enrichment_status=prospect.enrichment_status,
        enrichment_confidence=prospect.enrichment_confidence,
        last_execution_id=latest_execution.execution_id if latest_execution else None,
        last_execution_status=latest_execution.status if latest_execution else None,
        last_execution_time=latest_execution.created_at if latest_execution else None,
        recent_events=recent_events,
    )


@router.post("/search-trigger", response_model=EnrichmentTriggerResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_search_enrichment(
    request: SearchEnrichmentTriggerRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> EnrichmentTriggerResponse:
    """Run search discovery + crawl and use the result set in enrichment."""
    prospect = (
        db.query(Prospect)
        .filter(Prospect.prospect_id == request.prospect_id, Prospect.user_id == user_id)
        .first()
    )
    if not prospect:
        raise HTTPException(status_code=404, detail=f"Prospect {request.prospect_id} not found")

    company = None
    if prospect.company_id:
        company = (
            db.query(Company)
            .filter(Company.company_id == prospect.company_id, Company.user_id == user_id)
            .first()
        )

    name_parts = [part for part in [prospect.first_name, prospect.last_name] if part]
    base_query_parts = [" ".join(name_parts).strip() or prospect.email or "prospect"]
    if prospect.title:
        base_query_parts.append(prospect.title)
    if company:
        base_query_parts.append(company.name)

    base_query = " ".join(part for part in base_query_parts if part).strip()
    query_candidates: list[str] = []
    if company and company.domain:
        query_candidates.append(f"{base_query} site:{company.domain}".strip())
    query_candidates.append(base_query)
    if prospect.email:
        query_candidates.append(f"{prospect.email} {prospect.title or ''}".strip())

    deduped_queries: list[str] = []
    for candidate in query_candidates:
        normalized = " ".join(candidate.split()).strip()
        if normalized and normalized not in deduped_queries:
            deduped_queries.append(normalized)

    chosen_query = deduped_queries[0]

    start_time = datetime.utcnow()
    execution = AgentExecution(
        user_id=user_id,
        agent_type="SearchEnrichmentAgent",
        agent_name="search-trigger",
        task_id=str(uuid4()),
        prospect_id=prospect.prospect_id,
        company_id=prospect.company_id,
        status="running",
        input_data={"prospect_id": prospect.prospect_id, "query_candidates": deduped_queries, "limit": request.limit},
        start_time=start_time,
        decision_description="Search-driven enrichment triggered",
        created_at=start_time,
    )
    db.add(execution)
    db.flush()

    previous_status = prospect.enrichment_status
    previous_confidence = prospect.enrichment_confidence
    previous_website = prospect.website_url

    payload = None
    last_search_error: Exception | None = None
    for candidate_query in deduped_queries:
        chosen_query = candidate_query
        try:
            payload = await search_service.search_and_store(
                db,
                user_id=user_id,
                query=candidate_query,
                company_id=prospect.company_id,
                limit=request.limit,
            )
            break
        except Exception as exc:
            last_search_error = exc
            trace_logic(
                logger,
                "enrichment.search_trigger.retry",
                user_id=user_id,
                prospect_id=prospect.prospect_id,
                failed_query=candidate_query,
                error=str(exc),
            )

    if payload is None:
        execution.status = "failed"
        execution.end_time = datetime.utcnow()
        execution.duration_ms = int((execution.end_time - start_time).total_seconds() * 1000)
        execution.error_message = str(last_search_error or "Search enrichment failed")
        execution.output_data = {"query_candidates": deduped_queries}
        db.commit()
        raise HTTPException(status_code=502, detail="Search enrichment failed to find usable results")

    results = payload["results"]
    confidence = min(0.9, max(prospect.enrichment_confidence or 0.0, 0.35 + (0.15 * len(results))))

    prospect.enrichment_status = "enriched"
    prospect.enrichment_confidence = confidence
    if not prospect.website_url and results:
        prospect.website_url = results[0]["url"]

    db.add(
        EnrichmentEvent(
            prospect_id=prospect.prospect_id,
            field_name="enrichment_status",
            old_value=previous_status,
            new_value=prospect.enrichment_status,
            agent_name="SearchEnrichmentAgent",
            confidence_score=confidence,
            source="search_pipeline",
        )
    )
    if previous_confidence != confidence:
        db.add(
            EnrichmentEvent(
                prospect_id=prospect.prospect_id,
                field_name="enrichment_confidence",
                old_value=str(previous_confidence),
                new_value=str(confidence),
                agent_name="SearchEnrichmentAgent",
                confidence_score=confidence,
                source="search_pipeline",
            )
        )
    if previous_website != prospect.website_url and prospect.website_url:
        db.add(
            EnrichmentEvent(
                prospect_id=prospect.prospect_id,
                field_name="website_url",
                old_value=previous_website,
                new_value=prospect.website_url,
                agent_name="SearchEnrichmentAgent",
                confidence_score=confidence,
                source="search_pipeline",
            )
        )

    execution.status = "success"
    execution.end_time = datetime.utcnow()
    execution.duration_ms = int((execution.end_time - start_time).total_seconds() * 1000)
    execution.confidence_score = confidence
    execution.output_data = {
        "query": chosen_query,
        "query_candidates": deduped_queries,
        "memory_key": payload["memory_key"],
        "results_count": len(results),
        "document_ids": [result["document_id"] for result in results],
        "website_url": prospect.website_url,
    }
    db.commit()
    db.refresh(execution)

    trace_logic(
        logger,
        "enrichment.search_trigger.success",
        user_id=user_id,
        prospect_id=prospect.prospect_id,
        execution_id=execution.execution_id,
        results_count=len(results),
        memory_key=payload["memory_key"],
    )
    return EnrichmentTriggerResponse(
        execution_id=execution.execution_id,
        prospect_id=prospect.prospect_id,
        status="success",
        message="Search-driven enrichment completed successfully.",
    )
