"""
app/services/gemini_service.py — Gemini 2.5 Flash LLM service for structured extraction.

Responsibilities:
  - Extract structured company/prospect data from raw HTML
  - Track token usage for quota management
  - Cache prompt results for cost efficiency
  - Handle retries and rate limiting
"""

import json
import logging
from typing import Any, Optional

from pydantic import BaseModel, Field
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

logger = logging.getLogger("agentic_crm")


# ── Output Schemas (Pydantic) ──────────────────────────────────────────

class CompanyDataExtraction(BaseModel):
    """Extracted company data structure."""
    company_name: Optional[str] = Field(None, description="Official company name")
    website: Optional[str] = Field(None, description="Website URL")
    headcount: Optional[int] = Field(None, description="Employee count estimate")
    headcount_range: Optional[str] = Field(None, description="e.g., '50-100' if unknown")
    revenue_annual: Optional[int] = Field(None, description="Annual revenue in USD")
    funding_stage: Optional[str] = Field(None, description="seed|series_a|series_b|ipo|etc")
    latest_funding_date: Optional[str] = Field(None, description="YYYY-MM-DD format")
    headquarters_city: Optional[str] = None
    headquarters_country: Optional[str] = None
    industry: Optional[str] = Field(None, description="e.g., SaaS, FinTech, Healthcare")
    tech_stack: Optional[list[str]] = Field(None, description="Technologies used")
    description: Optional[str] = Field(None, description="Company description")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Confidence score")


class ProspectDataExtraction(BaseModel):
    """Extracted prospect/person data structure."""
    full_name: Optional[str] = None
    title: Optional[str] = Field(None, description="Job title")
    department: Optional[str] = Field(None, description="e.g., Sales, Engineering")
    seniority: Optional[str] = Field(None, description="entry|mid|senior|executive")
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    website_url: Optional[str] = None
    confidence: float = Field(0.0, ge=0.0, le=1.0)


class GeminiService:
    """Service for calling Gemini 2.5 Flash API."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini service.

        Args:
            api_key: Gemini API key (reads from env if not provided)
        """
        import os
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not set — LLM calls will fail")
            self.model = None
        else:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel("gemini-2.5-flash")
                logger.info("Gemini client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini: {e}")
                self.model = None

        self.token_count = 0
        self.cache = {}

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    async def extract_company_data(
        self, html_text: str, domain: str
    ) -> CompanyDataExtraction:
        """
        Extract structured company data from raw HTML.

        Sends to Gemini with structured output schema.

        Args:
            html_text: Cleaned HTML/text content
            domain: Company domain for context

        Returns:
            CompanyDataExtraction with extracted fields
        """
        if not html_text:
            return CompanyDataExtraction(confidence=0.0)

        # Check cache first
        cache_key = f"company:{domain}"
        if cache_key in self.cache:
            logger.debug(f"Cache hit for {domain}")
            return self.cache[cache_key]

        try:
            prompt = f"""
Extract structured company information from the following website content.
Be conservative with estimates. Only include data you're confident about.
If a field is not mentioned or unclear, leave it null.

Domain: {domain}

Content:
{html_text[:3000]}

Return JSON matching this schema:
{{
  "company_name": string,
  "website": string,
  "headcount": number,
  "headcount_range": string,
  "revenue_annual": number,
  "funding_stage": string,
  "latest_funding_date": "YYYY-MM-DD",
  "headquarters_city": string,
  "headquarters_country": string,
  "industry": string,
  "tech_stack": [strings],
  "description": string,
  "confidence": 0.0-1.0
}}

Only return valid JSON, no markdown.
"""

            if not self.model:
                logger.warning("Gemini model not available, returning stub")
                result_json = {
                    "company_name": f"Company from {domain}",
                    "website": domain,
                    "headcount": None,
                    "headcount_range": None,
                    "revenue_annual": None,
                    "funding_stage": None,
                    "latest_funding_date": None,
                    "headquarters_city": None,
                    "headquarters_country": None,
                    "industry": None,
                    "tech_stack": [],
                    "description": "Stub extraction (Gemini unavailable)",
                    "confidence": 0.1,
                }
            else:
                try:
                    response = self.model.generate_content(
                        prompt,
                        generation_config={
                            "response_mime_type": "application/json",
                        }
                    )
                    result_json = json.loads(response.text)
                except Exception as e:
                    logger.error(f"Gemini API call failed: {e}, using stub")
                    result_json = {
                        "company_name": f"Company from {domain}",
                        "website": domain,
                        "headcount": None,
                        "headcount_range": None,
                        "revenue_annual": None,
                        "funding_stage": None,
                        "latest_funding_date": None,
                        "headquarters_city": None,
                        "headquarters_country": None,
                        "industry": None,
                        "tech_stack": [],
                        "description": f"Extraction failed: {str(e)}",
                        "confidence": 0.0,
                    }

            extraction = CompanyDataExtraction(**result_json)
            self.cache[cache_key] = extraction
            self.token_count += 100  # Stub token count

            logger.info(f"Extracted company data for {domain} (confidence: {extraction.confidence})")
            return extraction

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response: {e}")
            return CompanyDataExtraction(confidence=0.0)
        except Exception as e:
            logger.error(f"Error extracting company data: {e}")
            raise

    async def extract_prospect_data(
        self, profile_text: str, prospect_name: str
    ) -> ProspectDataExtraction:
        """
        Extract prospect/person data from LinkedIn or web profile.

        Args:
            profile_text: Profile content
            prospect_name: Name for context

        Returns:
            ProspectDataExtraction
        """
        if not profile_text:
            return ProspectDataExtraction(confidence=0.0)

        cache_key = f"prospect:{prospect_name}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            prompt = f"""
Extract professional information about: {prospect_name}

Profile content:
{profile_text[:2000]}

Extract and return as JSON:
{{
  "full_name": string,
  "title": string,
  "department": string,
  "seniority": string (entry|mid|senior|executive),
  "email": string,
  "phone": string,
  "location": string,
  "linkedin_url": string,
  "website_url": string,
  "confidence": 0.0-1.0
}}

Only return valid JSON.
"""

            if not self.model:
                logger.warning("Gemini model not available for prospect extraction")
                result_json = {
                    "full_name": prospect_name,
                    "title": None,
                    "department": None,
                    "seniority": None,
                    "email": None,
                    "phone": None,
                    "location": None,
                    "linkedin_url": None,
                    "website_url": None,
                    "confidence": 0.1,
                }
            else:
                try:
                    response = self.model.generate_content(prompt)
                    result_json = json.loads(response.text)
                except Exception as e:
                    logger.error(f"Prospect extraction failed: {e}")
                    result_json = {
                        "full_name": prospect_name,
                        "title": None,
                        "department": None,
                        "seniority": None,
                        "email": None,
                        "phone": None,
                        "location": None,
                        "linkedin_url": None,
                        "website_url": None,
                        "confidence": 0.0,
                    }

            extraction = ProspectDataExtraction(**result_json)
            self.cache[cache_key] = extraction
            self.token_count += 80

            return extraction

        except Exception as e:
            logger.error(f"Error extracting prospect data: {e}")
            raise

    async def detect_keywords(
        self, text: str, keywords: list[str]
    ) -> dict[str, bool]:
        """
        Detect presence of keywords in text (for monitoring alerts).

        Args:
            text: Text to search
            keywords: Keywords to detect (e.g., ["Series B", "funding", "hired"])

        Returns:
            Dict of keyword -> found boolean
        """
        if not text:
            return {kw: False for kw in keywords}

        try:
            prompt = f"""
Search for these keywords in the text. Be case-insensitive.
Return a JSON object with true/false for each keyword.

Keywords: {', '.join(keywords)}

Text:
{text[:2000]}

Return JSON:
{{{", ".join(f'"{kw}": false' for kw in keywords)}}}

Only return valid JSON.
"""

            # TODO: Call actual Gemini API
            result = {kw: False for kw in keywords}

            return result

        except Exception as e:
            logger.error(f"Error detecting keywords: {e}")
            return {kw: False for kw in keywords}

    def get_token_count(self) -> int:
        """Return total tokens used in this session."""
        return self.token_count

    def clear_cache(self) -> None:
        """Clear prompt cache."""
        self.cache.clear()
        logger.info("Cleared Gemini service cache")


# Module-level instance
gemini_service = GeminiService()
