"""
app/agents/monitoring_agent.py — Monitoring Agent for change detection.

Responsibilities:
  - Crawl monitored company websites daily
  - Detect changes (funding, hiring, announcements)
  - Create alerts and log monitoring runs
  - Compare to previous crawl results for deltas
  - Store results in agent_executions with change metadata
"""

import logging
import time
from datetime import datetime
from typing import Optional, Dict, List, Any

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.agent_execution import AgentExecution
from app.models.company import Company
from app.models.enrichment_event import EnrichmentEvent
from app.services.crawl_service import crawl_service
from app.services.gemini_service import gemini_service

logger = logging.getLogger("agentic_crm")


class MonitoringAgent:
    """Agent for detecting changes in monitored companies."""

    def __init__(self):
        self.agent_type = "MonitoringAgent"
        self.change_keywords = {
            "funding": [
                "seed",
                "series a",
                "series b",
                "series c",
                "funding",
                "raised",
                "investment",
                "venture capital",
            ],
            "hiring": [
                "hiring",
                "jobs",
                "careers",
                "join our team",
                "we are hiring",
                "positions open",
            ],
            "product": [
                "new product",
                "launch",
                "announce",
                "released",
                "feature",
                "beta",
            ],
            "partnership": [
                "partnership",
                "partner",
                "collaborate",
                "acquisition",
                "acquired by",
            ],
        }

    async def monitor_company(
        self,
        user_id: int,
        company_id: int,
        company_domain: str,
        db: Session,
    ) -> Dict[str, Any]:
        """
        Monitor a single company for changes.

        Flow:
          1. Crawl company website
          2. Extract data via Gemini
          3. Compare to previous crawl (if exists)
          4. Detect changes using keyword detection
          5. Log execution with change details

        Args:
            user_id: User owning this monitoring task
            company_id: Company to monitor
            company_domain: Company domain
            db: Database session

        Returns:
            Dict with:
              - status: "success" | "no_changes" | "failed"
              - changes_detected: List of change categories
              - execution_id: Logged execution ID
              - details: Change details
              - error: Error message if applicable
        """
        start_time = datetime.utcnow()
        start_ms = time.time()

        result = {
            "status": "failed",
            "changes_detected": [],
            "execution_id": None,
            "details": {},
            "error": None,
        }

        try:
            # Create execution log entry
            execution = AgentExecution(
                user_id=user_id,
                agent_type=self.agent_type,
                task_id=f"monitor_{company_id}_{int(time.time())}",
                company_id=company_id,
                status="running",
                input_data={
                    "company_id": company_id,
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
                f"[MonitoringAgent] Starting monitoring for {company_domain} "
                f"(company_id: {company_id})"
            )

            # ── Step 1: Crawl company website ──────────────────────────────
            crawl_result = await crawl_service.crawl_company_website(company_domain)

            if crawl_result["status"] != "success":
                result["error"] = f"Crawl failed: {crawl_result.get('error')}"
                logger.warning(f"[MonitoringAgent] {result['error']}")
                result["status"] = "failed"
            else:
                current_text = crawl_result.get("text", "")

                # ── Step 2: Extract data via Gemini ────────────────────────
                company_data = await gemini_service.extract_company_data(
                    html_text=current_text, domain=company_domain
                )

                # ── Step 3: Get previous crawl for comparison ──────────────
                previous_crawl = await self._get_previous_crawl(
                    company_id, db
                )

                # ── Step 4: Detect changes ────────────────────────────────
                changes = self._detect_changes(
                    current_text=current_text,
                    previous_text=previous_crawl.get("text", "") if previous_crawl else "",
                    company_data=company_data,
                )

                if changes:
                    result["status"] = "success"
                    result["changes_detected"] = list(changes.keys())
                    result["details"] = changes

                    logger.info(
                        f"[MonitoringAgent] Changes detected for {company_domain}: "
                        f"{', '.join(changes.keys())}"
                    )
                else:
                    result["status"] = "no_changes"
                    logger.debug(f"[MonitoringAgent] No changes for {company_domain}")

            # ── Step 5: Log execution ──────────────────────────────────────
            end_time = datetime.utcnow()
            duration_ms = int((time.time() - start_ms) * 1000)

            execution.status = result["status"]
            execution.end_time = end_time
            execution.duration_ms = duration_ms
            execution.tokens_used = gemini_service.get_token_count()
            execution.output_data = {
                "changes_detected": result["changes_detected"],
                "change_details": result["details"],
            }
            execution.confidence_score = (
                float(len(result["changes_detected"]) > 0) if result["status"] != "failed" else 0.0
            )
            execution.decision_description = (
                f"Detected: {', '.join(result['changes_detected'])}"
                if result["changes_detected"]
                else "No changes detected"
            )

            db.commit()

            logger.info(
                f"[MonitoringAgent] Monitoring complete for {company_domain}. "
                f"Status: {result['status']}, Duration: {duration_ms}ms"
            )

            return result

        except Exception as e:
            logger.error(
                f"[MonitoringAgent] Error monitoring {company_domain}: {e}",
                exc_info=True,
            )
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

    async def monitor_all_enabled(self, user_id: int, db: Session) -> Dict[str, Any]:
        """
        Monitor all companies with monitoring_enabled=true.

        Returns summary of all monitoring runs.
        """
        companies = (
            db.query(Company)
            .filter(
                Company.user_id == user_id,
                Company.monitoring_enabled == True,
            )
            .all()
        )

        logger.info(
            f"[MonitoringAgent] Starting batch monitoring for {len(companies)} companies"
        )

        results = {
            "total": len(companies),
            "successful": 0,
            "no_changes": 0,
            "failed": 0,
            "changes_detected": [],
        }

        for company in companies:
            if not company.domain:
                logger.warning(f"Skipping company {company.name} (no domain)")
                continue

            result = await self.monitor_company(
                user_id=user_id,
                company_id=company.company_id,
                company_domain=company.domain,
                db=db,
            )

            if result["status"] == "success":
                results["successful"] += 1
                results["changes_detected"].append(
                    {
                        "company": company.name,
                        "changes": result["changes_detected"],
                    }
                )
            elif result["status"] == "no_changes":
                results["no_changes"] += 1
            else:
                results["failed"] += 1

        logger.info(
            f"[MonitoringAgent] Batch complete. "
            f"Successful: {results['successful']}, "
            f"No changes: {results['no_changes']}, "
            f"Failed: {results['failed']}"
        )

        return results

    def _detect_changes(
        self,
        current_text: str,
        previous_text: str,
        company_data: Optional[Any] = None,
    ) -> Dict[str, List[str]]:
        """
        Detect changes between current and previous crawl.

        Args:
            current_text: Current website text
            previous_text: Previous website text (for comparison)
            company_data: Extracted company data from Gemini

        Returns:
            Dict of change_category -> [detected_items]
        """
        changes = {}

        # Convert to lowercase for comparison
        current_lower = current_text.lower()
        previous_lower = previous_text.lower()

        # Search for keywords in current text that weren't in previous
        for category, keywords in self.change_keywords.items():
            found_in_current = [kw for kw in keywords if kw in current_lower]
            found_in_previous = [kw for kw in keywords if kw in previous_lower]

            # Changes = found in current but not in previous
            new_keywords = set(found_in_current) - set(found_in_previous)

            if new_keywords:
                changes[category] = list(new_keywords)

        # Additional detection: check if new text appeared (>500 char segments)
        if previous_text and len(current_text) > len(previous_text) + 500:
            changes["content_growth"] = [
                f"Content grew from {len(previous_text)} to {len(current_text)} chars"
            ]

        return changes

    async def _get_previous_crawl(
        self, company_id: int, db: Session
    ) -> Optional[Dict[str, Any]]:
        """
        Get the most recent previous monitoring run for this company.

        Returns: Previous crawl result or None.
        """
        try:
            previous_execution = (
                db.query(AgentExecution)
                .filter(
                    AgentExecution.company_id == company_id,
                    AgentExecution.agent_type == self.agent_type,
                    AgentExecution.status == "success",
                )
                .order_by(desc(AgentExecution.created_at))
                .first()
            )

            if not previous_execution or not previous_execution.output_data:
                return None

            # Ideally, we'd store the text in documents table
            # For MVP, we return the metadata
            return previous_execution.output_data

        except Exception as e:
            logger.warning(f"Failed to get previous crawl: {e}")
            return None


# Module-level instance for easy import
monitoring_agent = MonitoringAgent()
