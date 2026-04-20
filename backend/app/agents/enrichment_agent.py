"""
app/agents/enrichment_agent.py — Enrichment Agent for storing extracted data.

Responsibilities:
  - Map Research Agent output to CRM schema
  - Create/update company and prospect records
  - Log enrichment events per field (audit trail)
  - Handle conflicts (existing data, validation errors)
  - Atomic transactions with rollback on failure
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.company import Company
from app.models.prospect import Prospect
from app.models.enrichment_event import EnrichmentEvent
from app.services.gemini_service import (
    CompanyDataExtraction,
    ProspectDataExtraction,
)

logger = logging.getLogger("agentic_crm")


class EnrichmentAgent:
    """Agent for storing enriched data to CRM schema."""

    def __init__(self):
        self.agent_name = "EnrichmentAgent"

    def enrich_from_research(
        self,
        user_id: int,
        prospect_id: int,
        company_data: Optional[CompanyDataExtraction],
        prospect_data: Optional[ProspectDataExtraction],
        db: Session,
        overwrite_existing: bool = False,
    ) -> Dict[str, Any]:
        """
        Store research-extracted data to CRM schema.

        Flow:
          1. Create or update company record
          2. Update prospect record with new data
          3. Log enrichment events for each field change
          4. Handle conflicts and validation errors

        Args:
            user_id: User owning this enrichment
            prospect_id: Prospect to enrich
            company_data: Extracted company info from Research Agent
            prospect_data: Extracted prospect info from Research Agent
            db: Database session
            overwrite_existing: If True, overwrite existing fields; else skip

        Returns:
            Dict with:
              - status: "success" | "partial" | "failed"
              - company_id: Updated/created company ID
              - prospect_id: Updated prospect ID
              - enrichment_events: Count of field changes logged
              - error: Error message if applicable
        """
        result = {
            "status": "failed",
            "company_id": None,
            "prospect_id": prospect_id,
            "enrichment_events": 0,
            "error": None,
        }

        try:
            # Get prospect
            prospect = (
                db.query(Prospect)
                .filter(
                    Prospect.prospect_id == prospect_id,
                    Prospect.user_id == user_id,
                )
                .first()
            )

            if not prospect:
                result["error"] = f"Prospect {prospect_id} not found"
                logger.error(result["error"])
                return result

            events_created = 0

            # ── Step 1: Handle company data ────────────────────────────────
            if company_data:
                company = self._enrich_company(
                    user_id=user_id,
                    prospect_id=prospect_id,
                    company_data=company_data,
                    db=db,
                    overwrite=overwrite_existing,
                )

                if company:
                    result["company_id"] = company.company_id
                    # Link prospect to company if not already linked
                    if prospect.company_id != company.company_id:
                        prospect.company_id = company.company_id
                        events_created += self._log_enrichment_event(
                            prospect_id=prospect_id,
                            field_name="company_id",
                            old_value=str(prospect.company_id) if prospect.company_id else None,
                            new_value=str(company.company_id),
                            confidence=company_data.confidence,
                            source="research:company",
                            db=db,
                        )

            # ── Step 2: Handle prospect data ───────────────────────────────
            if prospect_data:
                events = self._enrich_prospect(
                    prospect=prospect,
                    prospect_data=prospect_data,
                    db=db,
                    overwrite=overwrite_existing,
                )
                events_created += events

            # ── Step 3: Update enrichment status ───────────────────────────
            prospect.enrichment_status = "enriched"
            prospect.enrichment_confidence = max(
                company_data.confidence if company_data else 0.0,
                prospect_data.confidence if prospect_data else 0.0,
            )

            db.commit()
            result["status"] = "success"
            result["enrichment_events"] = events_created

            logger.info(
                f"[EnrichmentAgent] Enriched prospect {prospect_id}: "
                f"{events_created} events logged, company {result['company_id']}"
            )

            return result

        except IntegrityError as e:
            db.rollback()
            result["error"] = f"Database integrity error: {str(e)}"
            logger.error(f"[EnrichmentAgent] IntegrityError: {e}")
            return result
        except Exception as e:
            db.rollback()
            result["error"] = f"Enrichment failed: {str(e)}"
            logger.error(f"[EnrichmentAgent] Error: {e}", exc_info=True)
            return result

    def _enrich_company(
        self,
        user_id: int,
        prospect_id: int,
        company_data: CompanyDataExtraction,
        db: Session,
        overwrite: bool = False,
    ) -> Optional[Company]:
        """
        Create or update company record from extracted data.

        Returns: Company object or None if creation failed.
        """
        try:
            # Try to find existing company by domain
            company = None
            if company_data.website:
                company = (
                    db.query(Company)
                    .filter(Company.domain == company_data.website)
                    .first()
                )

            if company and not overwrite:
                logger.debug(f"Company {company.name} already exists, skipping update")
                return company

            if not company:
                # Create new company
                company = Company(
                    user_id=user_id,
                    name=company_data.company_name or f"Company_{prospect_id}",
                    domain=company_data.website,
                    description=company_data.description,
                    headcount=company_data.headcount,
                    headcount_range=company_data.headcount_range,
                    revenue_annual=company_data.revenue_annual,
                    funding_stage=company_data.funding_stage,
                    headquarters_city=company_data.headquarters_city,
                    headquarters_country=company_data.headquarters_country,
                    industry=company_data.industry,
                    tech_stack=company_data.tech_stack or [],
                )
                db.add(company)
                db.flush()  # Get the ID without committing
                logger.info(f"[EnrichmentAgent] Created company {company.name}")
                return company
            else:
                # Update existing company
                if company_data.headcount and (not company.headcount or overwrite):
                    company.headcount = company_data.headcount
                if company_data.headcount_range and (not company.headcount_range or overwrite):
                    company.headcount_range = company_data.headcount_range
                if company_data.revenue_annual and (not company.revenue_annual or overwrite):
                    company.revenue_annual = company_data.revenue_annual
                if company_data.funding_stage and (not company.funding_stage or overwrite):
                    company.funding_stage = company_data.funding_stage
                if company_data.headquarters_city and (not company.headquarters_city or overwrite):
                    company.headquarters_city = company_data.headquarters_city
                if company_data.headquarters_country and (not company.headquarters_country or overwrite):
                    company.headquarters_country = company_data.headquarters_country
                if company_data.industry and (not company.industry or overwrite):
                    company.industry = company_data.industry
                if company_data.tech_stack and (not company.tech_stack or overwrite):
                    company.tech_stack = company_data.tech_stack

                db.flush()
                logger.info(f"[EnrichmentAgent] Updated company {company.name}")
                return company

        except Exception as e:
            logger.error(f"[EnrichmentAgent] Error enriching company: {e}")
            return None

    def _enrich_prospect(
        self,
        prospect: Prospect,
        prospect_data: ProspectDataExtraction,
        db: Session,
        overwrite: bool = False,
    ) -> int:
        """
        Update prospect record from extracted data.

        Returns: Number of enrichment events created.
        """
        events_count = 0

        # Map prospect fields
        fields_to_update = {
            "title": prospect_data.title,
            "location": prospect_data.location,
            "linkedin_url": prospect_data.linkedin_url,
            "website_url": prospect_data.website_url,
        }

        # Email and phone are special: only fill if empty (never overwrite)
        if not prospect.email and prospect_data.email:
            fields_to_update["email"] = prospect_data.email

        if not prospect.phone and prospect_data.phone:
            fields_to_update["phone"] = prospect_data.phone

        for field_name, new_value in fields_to_update.items():
            if not new_value:
                continue

            old_value = getattr(prospect, field_name, None)

            # Skip if field already has value and not overwriting
            if old_value and not overwrite:
                continue

            if old_value != new_value:
                setattr(prospect, field_name, new_value)
                events_count += self._log_enrichment_event(
                    prospect_id=prospect.prospect_id,
                    field_name=field_name,
                    old_value=str(old_value) if old_value else None,
                    new_value=str(new_value),
                    confidence=prospect_data.confidence,
                    source="research:prospect",
                    db=db,
                )

        return events_count

    def _log_enrichment_event(
        self,
        prospect_id: int,
        field_name: str,
        old_value: Optional[str],
        new_value: str,
        confidence: float,
        source: str,
        db: Session,
    ) -> int:
        """
        Create an enrichment event audit log entry.

        Returns: 1 if created successfully, 0 otherwise.
        """
        try:
            event = EnrichmentEvent(
                prospect_id=prospect_id,
                field_name=field_name,
                old_value=old_value,
                new_value=new_value,
                agent_name=self.agent_name,
                confidence_score=confidence,
                source=source,
            )
            db.add(event)
            db.flush()
            logger.debug(
                f"[EnrichmentAgent] Logged enrichment: {field_name} → {new_value} "
                f"(confidence: {confidence}, source: {source})"
            )
            return 1
        except Exception as e:
            logger.error(f"[EnrichmentAgent] Failed to log enrichment event: {e}")
            return 0


# Module-level instance for easy import
enrichment_agent = EnrichmentAgent()
