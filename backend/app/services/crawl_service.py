"""
app/services/crawl_service.py - Web crawling service using Crawl4AI + Playwright.

Responsibilities:
  - Crawl company websites with a browser-backed provider
  - Return normalized HTML, text, markdown, and metadata
  - Fall back to basic HTTP fetching when browser crawling is unavailable
  - Keep the public API stable for ResearchAgent and MonitoringAgent
"""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Any, Optional

import httpx
from bs4 import BeautifulSoup
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import settings

logger = logging.getLogger("agentic_crm")


class CrawlService:
    """Service for browser-backed crawling and content extraction."""

    def __init__(
        self,
        timeout_seconds: int = 30,
        max_retries: int = 3,
        provider: Optional[str] = None,
    ):
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.provider = (provider or settings.crawl_provider).strip().lower()
        self.browser_type = settings.crawl_browser_type
        self.headless = settings.crawl_headless
        self.text_mode = settings.crawl_text_mode
        self.light_mode = settings.crawl_light_mode
        self.http_fallback_enabled = settings.crawl_http_fallback_enabled
        self.respect_robots_txt = settings.crawl_respect_robots_txt
        self.verbose = settings.crawl_verbose
        self.user_agent = settings.crawl_user_agent.strip() or None
        self.word_count_threshold = settings.crawl_word_count_threshold
        self.wait_for = settings.crawl_wait_for.strip() or None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    async def crawl_url(self, url: str) -> dict[str, Any]:
        """
        Crawl a URL and extract normalized content.

        Returns:
            Dict with url, status_code, title, html, text, markdown, and metadata.
        """
        normalized_url = self._normalize_url(url)
        last_error: Exception | None = None

        if self.provider == "crawl4ai":
            try:
                return await self._crawl_with_crawl4ai(normalized_url)
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "crawl4ai crawl failed for %s: %s",
                    normalized_url,
                    exc,
                )
                if not self.http_fallback_enabled:
                    raise

        try:
            fallback_result = await self._crawl_with_http(normalized_url)
            fallback_result.setdefault("metadata", {})
            fallback_result["metadata"]["fallback_used"] = last_error is not None
            fallback_result["metadata"]["fallback_reason"] = (
                str(last_error) if last_error else None
            )
            return fallback_result
        except Exception as exc:
            logger.error("Fallback crawl failed for %s: %s", normalized_url, exc)
            raise exc from last_error

    async def _crawl_with_crawl4ai(self, url: str) -> dict[str, Any]:
        """Use Crawl4AI with Playwright-backed Chromium crawling."""
        try:
            from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig
        except ModuleNotFoundError as exc:  # pragma: no cover - dependency/runtime issue
            raise RuntimeError(
                "crawl4ai is not installed in the backend runtime"
            ) from exc

        browser_config = BrowserConfig(
            browser_type=self.browser_type,
            headless=self.headless,
            verbose=self.verbose,
            user_agent=self.user_agent,
            text_mode=self.text_mode,
            light_mode=self.light_mode,
        )
        run_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            word_count_threshold=self.word_count_threshold,
            wait_for=self.wait_for,
            check_robots_txt=self.respect_robots_txt,
            verbose=self.verbose,
        )

        logger.info(
            "Crawling %s via crawl4ai (browser=%s, headless=%s)",
            url,
            self.browser_type,
            self.headless,
        )

        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=url, config=run_config)

        success = bool(getattr(result, "success", False))
        if not success:
            error_message = getattr(result, "error_message", "Unknown crawl4ai error")
            raise RuntimeError(error_message)

        html = self._as_text(getattr(result, "html", "")) or self._as_text(
            getattr(result, "cleaned_html", "")
        )
        cleaned_html = self._as_text(getattr(result, "cleaned_html", "")) or html
        markdown = self._coerce_markdown(getattr(result, "markdown", ""))
        text = self._extract_text_from_sources(cleaned_html, html, markdown)

        raw_metadata = getattr(result, "metadata", None)
        metadata = raw_metadata if isinstance(raw_metadata, dict) else {}
        title = metadata.get("title") or self._extract_title(html)
        status_code = metadata.get("status_code") or 200

        return {
            "url": self._as_text(getattr(result, "url", "")) or url,
            "status_code": status_code,
            "title": title,
            "html": html,
            "text": text[:5000],
            "markdown": markdown,
            "metadata": {
                **metadata,
                "provider": "crawl4ai",
                "browser_type": self.browser_type,
                "headless": self.headless,
            },
        }

    async def _crawl_with_http(self, url: str) -> dict[str, Any]:
        """Fallback crawler using httpx when browser crawling is unavailable."""
        logger.info("Crawling %s via http fallback", url)

        headers = {"User-Agent": self.user_agent} if self.user_agent else None
        async with httpx.AsyncClient(timeout=self.timeout_seconds, headers=headers) as client:
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()

        html = response.text
        soup = BeautifulSoup(html, "html.parser")
        title = soup.title.string.strip() if soup.title and soup.title.string else "No title"
        text = self._extract_text_from_html(html)

        return {
            "url": str(response.url),
            "status_code": response.status_code,
            "title": title,
            "html": html,
            "text": text[:5000],
            "markdown": "",
            "metadata": {
                "provider": "http",
                "language": response.headers.get("content-language", "unknown"),
                "charset": response.encoding or "utf-8",
            },
        }

    async def extract_company_data(self, html: str, domain: str) -> dict[str, Any]:
        """Pre-process crawled HTML before structured extraction."""
        try:
            text = self._extract_text_from_html(html)
            description_match = re.search(
                r'<meta\s+name="description"\s+content="([^"]*)"',
                html,
                re.IGNORECASE,
            )
            description = description_match.group(1) if description_match else ""
            h1_matches = re.findall(r"<h1[^>]*>([^<]+)</h1>", html, re.IGNORECASE)
            headings = [heading.strip() for heading in h1_matches[:3] if heading.strip()]

            return {
                "domain": domain,
                "text": text[:5000],
                "description": description,
                "headings": headings,
                "char_count": len(text),
            }
        except Exception as exc:
            logger.error("Error extracting company data: %s", exc)
            return {
                "domain": domain,
                "text": "",
                "description": "",
                "headings": [],
                "char_count": 0,
                "error": str(exc),
            }

    async def crawl_company_website(self, domain: str) -> dict[str, Any]:
        """High-level company crawl for ResearchAgent and MonitoringAgent."""
        url = self._normalize_url(domain)
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
                "metadata": crawl_result.get("metadata", {}),
            }
        except Exception as exc:
            logger.error("Failed to crawl %s: %s", domain, exc)
            return {
                "status": "failed",
                "domain": domain,
                "error": str(exc),
            }

    async def crawl_prospect_profile(
        self,
        prospect_name: str,
        company_domain: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Placeholder for future search-driven prospect profile discovery.

        The search layer will call this once query orchestration is added.
        """
        return {
            "status": "pending",
            "prospect_name": prospect_name,
            "company": company_domain,
            "profiles_found": [],
        }

    def _normalize_url(self, url: str) -> str:
        if not url:
            raise ValueError("URL cannot be empty")
        if not url.startswith(("http://", "https://")):
            return f"https://{url}"
        return url

    def _extract_title(self, html: str) -> str:
        if not html:
            return "No title"
        soup = BeautifulSoup(html, "html.parser")
        if soup.title and soup.title.string:
            return soup.title.string.strip()
        return "No title"

    def _extract_text_from_sources(self, cleaned_html: str, html: str, markdown: str) -> str:
        if cleaned_html:
            return self._extract_text_from_html(cleaned_html)
        if html:
            return self._extract_text_from_html(html)
        return re.sub(r"\s+", " ", markdown or "").strip()

    def _extract_text_from_html(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        return re.sub(r"\s+", " ", text)

    def _coerce_markdown(self, value: Any) -> str:
        if isinstance(value, str):
            return value
        if hasattr(value, "raw_markdown"):
            raw_markdown = getattr(value, "raw_markdown")
            if isinstance(raw_markdown, str):
                return raw_markdown
        return self._as_text(value)

    def _as_text(self, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        return str(value)


crawl_service = CrawlService()
