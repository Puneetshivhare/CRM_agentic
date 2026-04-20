"""
app/services/crawl_service.py — Web scraping service using Crawl4AI + LightPanda.

Responsibilities:
  - Crawl company websites and extract structured data
  - Handle JavaScript-heavy sites via LightPanda
  - Retry with exponential backoff (tenacity)
  - Return raw HTML + extracted text for Gemini processing
"""

import logging
import re
from typing import Optional

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

logger = logging.getLogger("agentic_crm")


class CrawlService:
    """Service for web scraping and content extraction."""

    def __init__(self, timeout_seconds: int = 30, max_retries: int = 3):
        """
        Initialize the crawl service.

        Args:
            timeout_seconds: Max time to wait for a page to load
            max_retries: Max number of retries on failure
        """
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    async def crawl_url(self, url: str) -> dict:
        """
        Crawl a URL and extract content.

        Uses Crawl4AI for modern JS-based sites via LightPanda.
        Returns raw HTML + extracted text.

        Args:
            url: The URL to crawl

        Returns:
            Dict with url, title, text, html, and metadata

        Raises:
            Exception: On timeout, network error, or invalid URL
        """
        if not url:
            raise ValueError("URL cannot be empty")

        # Normalize URL
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"

        try:
            logger.info(f"Crawling {url}")

            # TODO: Implement actual Crawl4AI call here
            # from crawl4ai import AsyncWebCrawler
            # crawler = AsyncWebCrawler()
            # result = await crawler.arun(
            #     url=url,
            #     timeout=self.timeout_seconds,
            #     use_light_panda=True,  # For JS rendering
            # )

            # Stub response for now (to be replaced with real Crawl4AI)
            result = {
                "url": url,
                "status_code": 200,
                "title": f"Page from {url}",
                "html": "<html><body>Stub content</body></html>",
                "text": "Stub text content from the page",
                "metadata": {
                    "language": "en",
                    "charset": "utf-8",
                },
            }

            logger.info(f"Successfully crawled {url} ({len(result['text'])} chars)")
            return result

        except asyncio.TimeoutError:
            logger.error(f"Timeout crawling {url} after {self.timeout_seconds}s")
            raise
        except Exception as e:
            logger.error(f"Error crawling {url}: {e}")
            raise

    async def extract_company_data(self, html: str, domain: str) -> dict:
        """
        Extract company data from raw HTML.

        Pre-processes HTML before sending to Gemini.
        Removes boilerplate, nav, footer, scripts.

        Args:
            html: Raw HTML content
            domain: Domain for context (e.g., "acme.com")

        Returns:
            Dict with cleaned text, found links, meta tags, etc.
        """
        try:
            # Remove script and style tags
            text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)
            text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)

            # Remove HTML tags
            text = re.sub(r"<[^>]+>", " ", text)

            # Clean whitespace
            text = re.sub(r"\s+", " ", text).strip()

            # Extract meta tags (og:description, meta description)
            description_match = re.search(
                r'<meta\s+name="description"\s+content="([^"]*)"',
                html,
                re.IGNORECASE,
            )
            description = description_match.group(1) if description_match else ""

            # Extract headings (H1, H2)
            h1_matches = re.findall(r"<h1[^>]*>([^<]+)</h1>", html, re.IGNORECASE)
            headings = h1_matches[:3]  # Top 3 H1s

            return {
                "domain": domain,
                "text": text[:5000],  # First 5K chars
                "description": description,
                "headings": headings,
                "char_count": len(text),
            }

        except Exception as e:
            logger.error(f"Error extracting company data: {e}")
            return {
                "domain": domain,
                "text": "",
                "description": "",
                "headings": [],
                "char_count": 0,
                "error": str(e),
            }

    async def crawl_company_website(self, domain: str) -> dict:
        """
        High-level: Crawl a company domain and extract key data.

        Args:
            domain: Company domain (e.g., "acme.com")

        Returns:
            Dict with extracted company info for Gemini
        """
        url = f"https://{domain}" if not domain.startswith("http") else domain
        try:
            crawl_result = await self.crawl_url(url)
            extracted = await self.extract_company_data(crawl_result["html"], domain)
            return {
                "status": "success",
                "domain": domain,
                "url": crawl_result["url"],
                "title": crawl_result.get("title", ""),
                "text": extracted["text"],
                "description": extracted.get("description", ""),
                "headings": extracted.get("headings", []),
                "html_length": len(crawl_result.get("html", "")),
            }
        except Exception as e:
            logger.error(f"Failed to crawl {domain}: {e}")
            return {
                "status": "failed",
                "domain": domain,
                "error": str(e),
            }

    async def crawl_prospect_profile(
        self, prospect_name: str, company_domain: Optional[str] = None
    ) -> dict:
        """
        Crawl for prospect profile info (LinkedIn, personal site, etc).

        Args:
            prospect_name: Full name of prospect
            company_domain: Optional company domain for context

        Returns:
            Dict with found profile URLs and snippets
        """
        # TODO: Implement LinkedIn/web search for prospect profiles
        # For now, return stub
        return {
            "status": "pending",
            "prospect_name": prospect_name,
            "company": company_domain,
            "profiles_found": [],
        }


# Module-level instance for easy import
crawl_service = CrawlService()


# TODO: Remove this import when Crawl4AI integration is done
import asyncio
