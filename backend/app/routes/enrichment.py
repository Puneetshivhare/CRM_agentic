"""
app/routes/enrichment.py — REST API endpoints for enrichment workflows.

Endpoints:
  POST   /api/enrichment/trigger        — Trigger enrichment for prospect
  GET    /api/enrichment/{event_id}     — Check execution status
  GET    /api/enrichment/status/{prospect_id} — Latest enrichment status
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.database import get_db
from app.agents.research_agent import research_agent
from app.agents.enrichment_agent import enrichment_agent
from app.models.agent_execution import AgentExecution
from app.models.prospect import Prospect
from app.models.enrichment_event import EnrichmentEvent

logger = logging.getLogger("agentic_crm")
router = APIRouter(prefix="/api/enrichment", tags=["enrichment"])


# ── Pydantic Schemas ──────────────────────────────────────────────────


class EnrichmentTriggerRequest(BaseModel):
    """Request to trigger enrichment for a prospect."""

    prospect_id: int = Field(..., description="Prospect to enrich")


class EnrichmentTriggerResponse(BaseModel):
    """Response after triggering enrichment."""

    execution_id: int = Field(..., description="Agent execution ID")
    prospect_id: int = Field(..., description="Prospect being enriched")
    status: str = Field(..., description="pending | running | success | failed")
    message: str = Field(..., description="Status message")

    class Config:
        from_attributes = True


class ExecutionStatusResponse(BaseModel):
    """Status of an agent execution."""

    execution_id: int
    prospect_id: Optional[int]
    agent_type: str
    status: str
    start_time: str
    end_time: Optional[str]
    duration_ms: Optional[int]
    tokens_used: Optional[int]
    error_message: Optional[str]
    confidence_score: Optional[float]

    class Config:
        from_attributes = True


class ProspectEnrichmentStatusResponse(BaseModel):
    """Latest enrichment status for a prospect."""

    prospect_id: int
    enrichment_status: str
    enrichment_confidence: float
    last_execution_id: Optional[int]
    last_execution_status: Optional[str]
    last_execution_time: Optional[str]
    recent_events: int = Field(..., description="Count of recent enrichment events")

    class Config:
        from_attributes = True


# ── Helper Functions ──────────────────────────────────────────────────


def get_current_user_id(db: Session = Depends(get_db)) -> int:
    """Extract user_id. For now, default to user_id=1 (TODO: JWT validation)."""
    return 1


# ── Endpoints ─────────────────────────────────────────────────────────


@router.post("/trigger", response_model=EnrichmentTriggerResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_enrichment(
    request: EnrichmentTriggerRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> EnrichmentTriggerResponse:
    """
    Trigger enrichment workflow for a prospect.

    Orchestrates:
      1. Research Agent (crawl + extraction)
      2. Enrichment Agent (storage + logging)

    Returns: execution_id for polling status.
    """
    try:
        # Verify prospect exists and belongs to user
        prospect = (
            db.query(Prospect)
            .filter(
                Prospect.prospect_id == request.prospect_id,
                Prospect.user_id == user_id,
            )
            .first()
        )

        if not prospect:
            raise HTTPException(
                status_code=404,
                detail=f"Prospect {request.prospect_id} not found",
            )

        # Mark prospect as enriching
        prospect.enrichment_status = "enriching"
        db.commit()

        logger.info(f"[EnrichmentAPI] Triggering enrichment for prospect {request.prospect_id}")

        # ── Execute Research Agent ────────────────────────────────────────
        research_result = await research_agent.enrich_prospect_with_research(
            prospect_id=request.prospect_id,
            user_id=user_id,
            db=db,
        )

        execution_id = research_result.get("execution_id")

        if research_result["status"] != "success":
            # If research failed, mark prospect as failed
            prospect.enrichment_status = "failed"
            db.commit()

            logger.warning(
                f"[EnrichmentAPI] Research failed for prospect {request.prospect_id}: "
                f"{research_result.get('error')}"
            )

            return EnrichmentTriggerResponse(
                execution_id=execution_id or 0,
                prospect_id=request.prospect_id,
                status="failed",
                message=f"Research failed: {research_result.get('error')}",
            )

        # ── Execute Enrichment Agent ──────────────────────────────────────
        enrichment_result = enrichment_agent.enrich_from_research(
            user_id=user_id,
            prospect_id=request.prospect_id,
            company_data=_extract_company_data(research_result),
            prospect_data=_extract_prospect_data(research_result),
            db=db,
            overwrite_existing=False,
        )

        if enrichment_result["status"] != "success":
            prospect.enrichment_status = "failed"
            db.commit()

            logger.warning(
                f"[EnrichmentAPI] Enrichment failed for prospect {request.prospect_id}: "
                f"{enrichment_result.get('error')}"
            )

            return EnrichmentTriggerResponse(
                execution_id=execution_id or 0,
                prospect_id=request.prospect_id,
                status="failed",
                message=f"Enrichment failed: {enrichment_result.get('error')}",
            )

        # ── Success ───────────────────────────────────────────────────────
        prospect.enrichment_status = "enriched"
        db.commit()

        logger.info(
            f"[EnrichmentAPI] Enrichment completed for prospect {request.prospect_id}, "
            f"execution {execution_id}, events: {enrichment_result.get('enrichment_events', 0)}"
        )

        return EnrichmentTriggerResponse(
            execution_id=execution_id or 0,
            prospect_id=request.prospect_id,
            status="success",
            message=f"Enrichment completed. {enrichment_result.get('enrichment_events', 0)} fields updated.",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[EnrichmentAPI] Error triggering enrichment: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger enrichment: {str(e)}",
        )


@router.get("/{execution_id}", response_model=ExecutionStatusResponse)
async def get_execution_status(
    execution_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> ExecutionStatusResponse:
    """
    Get status of an agent execution.

    Returns: execution details including status, duration, tokens, confidence.
    """
    try:
        execution = (
            db.query(AgentExecution)
            .filter(
                AgentExecution.execution_id == execution_id,
                AgentExecution.user_id == user_id,
            )
            .first()
        )

        if not execution:
            raise HTTPException(
                status_code=404,
                detail=f"Execution {execution_id} not found",
            )

        return ExecutionStatusResponse(
            execution_id=execution.execution_id,
            prospect_id=execution.prospect_id,
            agent_type=execution.agent_type,
            status=execution.status,
            start_time=execution.start_time.isoformat() if execution.start_time else None,
            end_time=execution.end_time.isoformat() if execution.end_time else None,
            duration_ms=execution.duration_ms,
            tokens_used=execution.tokens_used,
            error_message=execution.error_message,
            confidence_score=execution.confidence_score,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[EnrichmentAPI] Error fetching execution status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch execution status: {str(e)}",
        )


@router.get("/status/{prospect_id}", response_model=ProspectEnrichmentStatusResponse)
async def get_prospect_enrichment_status(
    prospect_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> ProspectEnrichmentStatusResponse:
    """
    Get latest enrichment status for a prospect.

    Returns: enrichment status, confidence, last execution details, recent events.
    """
    try:
        prospect = (
            db.query(Prospect)
            .filter(
                Prospect.prospect_id == prospect_id,
                Prospect.user_id == user_id,
            )
            .first()
        )

        if not prospect:
            raise HTTPException(
                status_code=404,
                detail=f"Prospect {prospect_id} not found",
            )

        # Get latest execution
        latest_execution = (
            db.query(AgentExecution)
            .filter(AgentExecution.prospect_id == prospect_id)
            .order_by(AgentExecution.created_at.desc())
            .first()
        )

        # Count recent enrichment events (last 30 days)
        recent_events = (
            db.query(EnrichmentEvent)
            .filter(EnrichmentEvent.prospect_id == prospect_id)
            .count()
        )

        return ProspectEnrichmentStatusResponse(
            prospect_id=prospect_id,
            enrichment_status=prospect.enrichment_status,
            enrichment_confidence=prospect.enrichment_confidence,
            last_execution_id=latest_execution.execution_id if latest_execution else None,
            last_execution_status=latest_execution.status if latest_execution else None,
            last_execution_time=latest_execution.created_at.isoformat()
            if latest_execution
            else None,
            recent_events=recent_events,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[EnrichmentAPI] Error fetching prospect status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch prospect status: {str(e)}",
        )


# ── Helper Functions ──────────────────────────────────────────────────


def _extract_company_data(research_result: dict):
    """Extract CompanyDataExtraction from research result if it exists."""
    company_dict = research_result.get("company_data")
    if not company_dict:
        return None

    from app.services.gemini_service import CompanyDataExtraction

    try:
        return CompanyDataExtraction(**company_dict)
    except Exception as e:
        logger.warning(f"Failed to deserialize company data: {e}")
        return None


def _extract_prospect_data(research_result: dict):
    """Extract ProspectDataExtraction from research result if it exists."""
    prospect_dict = research_result.get("prospect_data")
    if not prospect_dict:
        return None

    from app.services.gemini_service import ProspectDataExtraction

    try:
        return ProspectDataExtraction(**prospect_dict)
    except Exception as e:
        logger.warning(f"Failed to deserialize prospect data: {e}")
        return None
