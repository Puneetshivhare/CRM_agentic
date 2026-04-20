"""
app/agents/research_agent.py — Research Agent for prospect enrichment.

Responsibilities:
  - Orchestrate web crawling + structured extraction
  - Log execution metrics (tokens, latency, success)
  - Store raw HTML in documents table for RAG
  - Handle errors with graceful fallbacks
  - Target: <30 seconds per prospect (MVP)
"""

import json
import logging
import time
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy.orm import Session

from app.database import get_db
from app.models.document import Document
from app.models.agent_execution import AgentExecution
from app.models.company import Company
from app.models.prospect import Prospect
from app.services.crawl_service import crawl_service
from app.services.gemini_service import gemini_service

logger = logging.getLogger("agentic_crm")


class ResearchAgent:
    """Agent for researching and enriching prospect/company data."""

    def __init__(self, db: Session = None):
        """
        Initialize Research Agent.

        Args:
            db: Database session (injected; can be passed or None for testing)
        """
        self.db = db
        self.agent_type = "ResearchAgent"

    async def research_prospect(
        self,
        user_id: int,
        prospect_name: str,
        company_domain: Optional[str] = None,
        prospect_id: Optional[int] = None,
        company_id: Optional[int] = None,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """
        Research and enrich a prospect with company data.

        Flow:
          1. Crawl company website (if domain provided)
          2. Extract structured company data via Gemini
          3. Store raw HTML in documents table (for RAG)
          4. Log execution metrics to agent_executions

        Args:
            user_id: User who owns this research task
            prospect_name: Full name of prospect
            company_domain: Company domain (e.g., "acme.com")
            prospect_id: Optional prospect DB ID to link execution
            company_id: Optional company DB ID to link execution
            db: Database session (optional override)

        Returns:
            Dict with:
              - status: "success" | "partial" | "failed"
              - execution_id: Logged execution ID
              - company_data: Extracted company info (from Gemini)
              - document_id: Raw HTML stored in documents
              - error: Error message if status != "success"
        """
        db = db or self.db
        task_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        start_ms = time.time()

        execution = None
        result = {
            "status": "failed",
            "execution_id": None,
            "company_data": None,
            "document_id": None,
            "error": None,
        }

        try:
            # Create execution log entry
            execution = AgentExecution(
                user_id=user_id,
                agent_type=self.agent_type,
                task_id=task_id,
                prospect_id=prospect_id,
                company_id=company_id,
                status="running",
                input_data={
                    "prospect_name": prospect_name,
                    "company_domain": company_domain,
                },
                start_time=start_time,
                memory_hits=0,
            )
            db.add(execution)
            db.commit()
            db.refresh(execution)
            result["execution_id"] = execution.execution_id

            logger.info(
                f"[ResearchAgent {task_id}] Starting research for {prospect_name}@{company_domain}"
            )

            # ── Step 1: Crawl company website ──────────────────────────────
            company_data = None
            document_id = None
            crawl_result = None

            if company_domain:
                try:
                    logger.debug(f"[{task_id}] Crawling {company_domain}")
                    crawl_result = await crawl_service.crawl_company_website(
                        company_domain
                    )

                    if crawl_result["status"] == "success":
                        # ── Step 2: Extract data via Gemini ──────────────────
                        logger.debug(f"[{task_id}] Extracting company data via Gemini")
                        company_data = await gemini_service.extract_company_data(
                            html_text=crawl_result["text"], domain=company_domain
                        )

                        # ── Step 3: Store raw HTML in documents table ────────
                        document = Document(
                            user_id=user_id,
                            file_name=f"crawl_{company_domain}_{task_id[:8]}.html",
                            file_path=f"/raw_crawls/{company_domain}/",
                            document_type="company_website",
                            extracted_text=crawl_result["text"],
                            associated_company_id=company_id,
                        )
                        db.add(document)
                        db.commit()
                        db.refresh(document)
                        document_id = document.document_id

                        logger.info(
                            f"[{task_id}] Stored raw HTML in document {document_id}"
                        )

                        result["company_data"] = company_data.model_dump()
                        result["document_id"] = document_id
                        result["status"] = "success"

                    else:
                        result["error"] = f"Crawl failed: {crawl_result.get('error', 'Unknown error')}"
                        logger.warning(f"[{task_id}] Crawl failed: {result['error']}")
                        result["status"] = "partial"

                except Exception as e:
                    result["error"] = f"Crawl/extraction error: {str(e)}"
                    logger.error(f"[{task_id}] Error during crawl: {e}", exc_info=True)
                    result["status"] = "partial"
            else:
                result["error"] = "No company domain provided"
                result["status"] = "partial"

            # ── Step 4: Log execution metrics ──────────────────────────────
            end_time = datetime.utcnow()
            duration_ms = int((time.time() - start_ms) * 1000)
            tokens_used = gemini_service.get_token_count()

            execution.status = result["status"]
            execution.end_time = end_time
            execution.duration_ms = duration_ms
            execution.tokens_used = tokens_used
            execution.output_data = {
                "company_data_extracted": result["company_data"] is not None,
                "document_stored": result["document_id"] is not None,
                "crawl_status": crawl_result.get("status") if crawl_result else "skipped",
            }
            execution.confidence_score = (
                company_data.confidence if company_data else 0.0
            )
            execution.decision_description = result.get("error", "Research completed successfully")

            db.commit()

            logger.info(
                f"[{task_id}] Research complete. Status: {result['status']}, "
                f"Duration: {duration_ms}ms, Tokens: {tokens_used}"
            )

            return result

        except Exception as e:
            logger.error(f"[{task_id}] Unhandled error in research_prospect: {e}", exc_info=True)
            result["error"] = str(e)
            result["status"] = "failed"

            # Update execution with failure
            if execution:
                execution.status = "failed"
                execution.error_message = str(e)
                execution.end_time = datetime.utcnow()
                execution.duration_ms = int((time.time() - start_ms) * 1000)
                try:
                    db.commit()
                except:
                    pass

            return result

    async def enrich_prospect_with_research(
        self,
        prospect_id: int,
        user_id: int,
        db: Session,
    ) -> Dict[str, Any]:
        """
        High-level method to enrich a prospect from the database.

        Looks up prospect, extracts company domain, then runs research.

        Args:
            prospect_id: Prospect to enrich
            user_id: User owning the prospect
            db: Database session

        Returns:
            Result dict from research_prospect()
        """
        prospect = (
            db.query(Prospect)
            .filter(
                Prospect.prospect_id == prospect_id,
                Prospect.user_id == user_id,
            )
            .first()
        )

        if not prospect:
            logger.error(f"Prospect {prospect_id} not found for user {user_id}")
            return {
                "status": "failed",
                "error": "Prospect not found",
            }

        # Extract company domain from prospect's company or construct from name
        company_domain = None
        company_id = prospect.company_id

        if prospect.company_id:
            company = db.query(Company).filter(
                Company.company_id == prospect.company_id
            ).first()
            if company:
                company_domain = company.domain

        prospect_name = f"{prospect.first_name or ''} {prospect.last_name or ''}".strip()

        return await self.research_prospect(
            user_id=user_id,
            prospect_name=prospect_name,
            company_domain=company_domain,
            prospect_id=prospect_id,
            company_id=company_id,
            db=db,
        )


# Module-level instance for easy import
research_agent = ResearchAgent()
