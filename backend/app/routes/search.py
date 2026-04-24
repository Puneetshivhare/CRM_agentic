"""Minimal web search API backed by Crawl4AI + Playwright."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Annotated, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.agent_execution import AgentExecution
from app.models.memory import MemoryStore
from app.services.search_service import search_service
from app.utils.logger import trace_logic

logger = logging.getLogger("agentic_crm")
router = APIRouter(prefix="/api/search", tags=["search"])


class SearchWebRequest(BaseModel):
    """Search request payload."""

    query: Optional[str] = Field(default=None, max_length=500)
    company_id: Optional[int] = None
    limit: int = Field(default=5, ge=1, le=10)


class SearchResultResponse(BaseModel):
    """Single crawled search result."""

    rank: int
    title: str
    url: str
    snippet: str
    source: str
    document_id: int
    status_code: Optional[int] = None
    provider: Optional[str] = None
    text_preview: str


class SearchWebResponse(BaseModel):
    """Search response payload."""

    query: str
    company_id: Optional[int] = None
    memory_key: str
    cached_at: str
    results: list[SearchResultResponse]


class BrowserSessionCreateRequest(BaseModel):
    query: Optional[str] = Field(default=None, max_length=500)
    company_id: Optional[int] = None
    limit: int = Field(default=5, ge=1, le=10)
    mode: str = Field(default="analyst_assist", max_length=50)


class BrowserAcceptPageRequest(BaseModel):
    url: str = Field(..., max_length=1000)
    title: str = Field(..., max_length=500)
    snippet: str = Field(default="", max_length=2000)
    source: str = Field(default="", max_length=255)


class BrowserSessionResponse(BaseModel):
    session_id: str
    query: str
    company_id: Optional[int] = None
    mode: str
    status: str
    execution_id: int
    candidates: list[dict]
    accepted_results: list[dict]
    created_at: str


def get_current_user_id(user: Annotated[dict, Depends(get_current_user)]) -> int:
    """Extract user id from JWT dependency."""
    return user["user_id"]


@router.post("/web", response_model=SearchWebResponse)
async def search_web(
    request: SearchWebRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> SearchWebResponse:
    """Run a web search, crawl top results, and store artifacts for reuse."""
    try:
        resolved_query, resolved_company_id = search_service.build_company_query(
            db,
            user_id=user_id,
            company_id=request.company_id,
            query=request.query,
        )
        trace_logic(
            logger,
            "search.web.request",
            user_id=user_id,
            company_id=resolved_company_id,
            query=resolved_query,
            limit=request.limit,
        )
        payload = await search_service.search_and_store(
            db,
            user_id=user_id,
            query=resolved_query,
            company_id=resolved_company_id,
            limit=request.limit,
        )
        return SearchWebResponse(**payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("Search request failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Search failed: {exc}") from exc


@router.get("/web", response_model=SearchWebResponse)
async def search_web_via_query(
    query: Optional[str] = Query(default=None, max_length=500),
    company_id: Optional[int] = Query(default=None),
    limit: int = Query(default=5, ge=1, le=10),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> SearchWebResponse:
    """Convenience GET variant for quick browser/manual testing."""
    return await search_web(
        SearchWebRequest(query=query, company_id=company_id, limit=limit),
        db=db,
        user_id=user_id,
    )


@router.post("/browser/session", response_model=BrowserSessionResponse)
async def create_browser_session(
    request: BrowserSessionCreateRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> BrowserSessionResponse:
    """Create an analyst-assist browser session with candidate pages."""
    try:
        resolved_query, resolved_company_id = search_service.build_company_query(
            db,
            user_id=user_id,
            company_id=request.company_id,
            query=request.query,
        )
        session_id = str(uuid4())
        created_at = datetime.utcnow()
        execution = AgentExecution(
            user_id=user_id,
            agent_type="AnalystAssistBrowser",
            agent_name=request.mode,
            task_id=session_id,
            company_id=resolved_company_id,
            status="running",
            input_data={"query": resolved_query, "company_id": resolved_company_id, "limit": request.limit, "mode": request.mode},
            start_time=created_at,
            decision_description="Analyst assist browser session created",
            created_at=created_at,
        )
        db.add(execution)
        db.flush()

        candidates = await search_service.discover_results(resolved_query, limit=request.limit)
        memory_key = _browser_session_key(user_id=user_id, session_id=session_id)
        payload = {
            "session_id": session_id,
            "query": resolved_query,
            "company_id": resolved_company_id,
            "mode": request.mode,
            "status": "ready",
            "execution_id": execution.execution_id,
            "candidates": candidates,
            "accepted_results": [],
            "created_at": created_at.isoformat(),
        }
        db.add(MemoryStore(memory_key=memory_key, memory_value=payload, ttl_seconds=86400))
        execution.status = "success"
        execution.end_time = datetime.utcnow()
        execution.duration_ms = int((execution.end_time - created_at).total_seconds() * 1000)
        execution.output_data = {"session_id": session_id, "candidates_count": len(candidates)}
        db.commit()
        trace_logic(logger, "search.browser.session.created", user_id=user_id, session_id=session_id, execution_id=execution.execution_id, candidates=len(candidates))
        return BrowserSessionResponse(**payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("Browser session creation failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Browser session failed: {exc}") from exc


@router.get("/browser/session/{session_id}", response_model=BrowserSessionResponse)
async def get_browser_session(
    session_id: str,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> BrowserSessionResponse:
    """Fetch the current analyst-assist session state."""
    session = _get_browser_session(db, user_id=user_id, session_id=session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Browser session not found")
    return BrowserSessionResponse(**session.memory_value)


@router.post("/browser/session/{session_id}/accept-page", response_model=SearchResultResponse)
async def accept_browser_page(
    session_id: str,
    request: BrowserAcceptPageRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> SearchResultResponse:
    """Accept a candidate page from analyst assist and persist it."""
    session = _get_browser_session(db, user_id=user_id, session_id=session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Browser session not found")

    payload = session.memory_value
    company_id = payload.get("company_id")
    execution = AgentExecution(
        user_id=user_id,
        agent_type="BackendBrowser",
        agent_name="accept-page",
        task_id=str(uuid4()),
        company_id=company_id,
        status="running",
        input_data={"session_id": session_id, "url": request.url, "title": request.title},
        start_time=datetime.utcnow(),
        decision_description="Accepted browser candidate for crawl",
    )
    db.add(execution)
    db.flush()

    stored_results = await search_service.crawl_and_store_results(
        db=db,
        user_id=user_id,
        company_id=company_id,
        results=[
            {
                "title": request.title,
                "url": request.url,
                "snippet": request.snippet,
                "source": request.source or request.url,
            }
        ],
    )
    accepted = stored_results[0]
    payload.setdefault("accepted_results", []).append(accepted)
    payload["status"] = "accepted"
    session.memory_value = payload
    session.accessed_at = datetime.utcnow()

    execution.status = "success"
    execution.end_time = datetime.utcnow()
    execution.duration_ms = int((execution.end_time - execution.start_time).total_seconds() * 1000)
    execution.output_data = {"session_id": session_id, "document_id": accepted["document_id"], "url": accepted["url"]}
    db.commit()
    trace_logic(logger, "search.browser.page.accepted", user_id=user_id, session_id=session_id, document_id=accepted["document_id"], url=accepted["url"])
    return SearchResultResponse(**accepted)


def _browser_session_key(*, user_id: int, session_id: str) -> str:
    return f"user:{user_id}:browser_session:{session_id}"


def _get_browser_session(db: Session, *, user_id: int, session_id: str) -> MemoryStore | None:
    return (
        db.query(MemoryStore)
        .filter(MemoryStore.memory_key == _browser_session_key(user_id=user_id, session_id=session_id))
        .first()
    )
