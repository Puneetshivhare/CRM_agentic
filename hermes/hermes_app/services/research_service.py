"""
hermes_app/services/research_service.py — Research service with guardrails.
"""

import logging
from typing import Optional

import httpx

from hermes_app.config import settings
from hermes_app.guardrails import GuardrailsManager

logger = logging.getLogger("hermes")


class ResearchService:
    """Research service with guardrail enforcement."""
    
    def __init__(self, tenant_id: str, guardrails: GuardrailsManager):
        self.tenant_id = tenant_id
        self.guardrails = guardrails
        self.brave_api_key = settings.brave_search_api_key
        self.gemini_api_key = settings.gemini_api_key
        
    async def web_search(self, query: str, max_results: int = 5) -> dict:
        """Perform web search via Brave API."""
        
        # Enforce max results limit
        limits = self.guardrails.get_rate_limits()
        max_results = min(max_results, limits.get("max_results", 10))
        
        if not self.brave_api_key:
            logger.warning("Brave API key not configured")
            return {"data": {"results": [], "error": "Search not configured"}}
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    "https://api.search.brave.com/res/v1/web/search",
                    headers={
                        "X-Subscription-Token": self.brave_api_key,
                        "Accept": "application/json",
                    },
                    params={
                        "q": query,
                        "count": max_results,
                        "offset": 0,
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                return {
                    "data": {
                        "results": data.get("web", {}).get("results", []),
                        "query": query,
                    },
                    "tokens_used": 0,
                    "memory_hits": 0,
                }
                
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return {"data": {"results": [], "error": str(e)}}
    
    async def web_crawl(self, url: str, depth: int = 1) -> dict:
        """Crawl a web page with restrictions."""
        
        crawl_limits = self.guardrails.get_crawl_limits()
        max_depth = crawl_limits.get("max_depth", 1)
        max_duration = crawl_limits.get("max_duration_seconds", 60)
        
        # Enforce depth limit
        depth = min(depth, max_depth)
        
        logger.info(f"[Research] Crawling {url} (depth={depth}, tenant={self.tenant_id})")
        
        # In production, integrate with crawl4ai
        # For now, return simulated data
        return {
            "data": {
                "url": url,
                "title": "Simulated page title",
                "content": "Simulated crawled content...",
                "depth": depth,
            },
            "tokens_used": 0,
            "memory_hits": 0,
        }
    
    async def research_prospect(
        self,
        prospect_name: str,
        company_domain: Optional[str],
        enrichment_goal: str = "",
    ) -> dict:
        """Research a prospect."""
        
        logger.info(f"[Research] Researching prospect: {prospect_name}")
        
        # 1. Search for prospect
        search_query = f"{prospect_name} {company_domain or ''}"
        search_result = await self.web_search(search_query, max_results=5)
        
        # 2. If company domain provided, crawl it
        company_data = {}
        if company_domain:
            crawl_result = await self.web_crawl(f"https://{company_domain}", depth=1)
            company_data = crawl_result.get("data", {})
        
        return {
            "data": {
                "prospect_name": prospect_name,
                "company_domain": company_domain,
                "search_results": search_result.get("data", {}).get("results", []),
                "company_data": company_data,
            },
            "tokens_used": 0,
            "memory_hits": 0,
        }
    
    async def enrich_company(self, domain: Optional[str], company_name: str) -> dict:
        """Enrich company data."""
        
        logger.info(f"[Research] Enriching company: {company_name}")
        
        search_query = f"{company_name} company overview"
        if domain:
            search_query += f" site:{domain}"
        
        search_result = await self.web_search(search_query, max_results=5)
        
        return {
            "data": {
                "company_name": company_name,
                "domain": domain,
                "search_results": search_result.get("data", {}).get("results", []),
            },
            "tokens_used": 0,
            "memory_hits": 0,
        }
