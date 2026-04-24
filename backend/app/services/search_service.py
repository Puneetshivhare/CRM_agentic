"""Web search orchestration for agentic search workflows."""

from __future__ import annotations

import base64
import logging
import re
from datetime import datetime
from typing import Any
from urllib.parse import parse_qs, quote_plus, unquote, urlparse

import httpx
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.config import settings
from app.models.company import Company
from app.models.document import Document
from app.models.memory import MemoryStore
from app.services.crawl_service import crawl_service
from app.utils.logger import trace_logic

logger = logging.getLogger("agentic_crm")


class SearchService:
    """Search the web, crawl top results, and persist reusable artifacts."""

    def __init__(self, timeout_seconds: int = 20):
        self.timeout_seconds = timeout_seconds
        self.user_agent = "AgenticCRMSearchBot/1.0"
        self.brave_api_key = settings.brave_search_api_key.strip()

    async def search_and_store(
        self,
        db: Session,
        user_id: int,
        query: str,
        *,
        company_id: int | None = None,
        limit: int = 5,
    ) -> dict[str, Any]:
        """Search the web, crawl results, and persist a cache snapshot."""
        normalized_query = self._normalize_query(query)
        cache_key = self._cache_key(user_id=user_id, query=normalized_query)
        trace_logic(
            logger,
            "search.web.start",
            user_id=user_id,
            company_id=company_id,
            query=normalized_query,
            limit=limit,
            cache_key=cache_key,
        )

        search_results = await self.discover_results(normalized_query, limit=limit)
        stored_results = await self.crawl_and_store_results(
            db=db,
            user_id=user_id,
            results=search_results,
            company_id=company_id,
        )

        memory_record = self._upsert_cache(
            db=db,
            cache_key=cache_key,
            results=stored_results,
            query=normalized_query,
            company_id=company_id,
        )
        db.commit()

        trace_logic(
            logger,
            "search.web.success",
            user_id=user_id,
            company_id=company_id,
            query=normalized_query,
            results_count=len(stored_results),
            cache_key=cache_key,
        )
        return {
            "query": normalized_query,
            "company_id": company_id,
            "results": stored_results,
            "memory_key": memory_record.memory_key,
            "cached_at": memory_record.accessed_at.isoformat(),
        }

    async def discover_results(self, query: str, *, limit: int = 5) -> list[dict[str, str]]:
        """Discover candidate URLs without persisting crawled content."""
        normalized_query = self._normalize_query(query)
        return await self._search_web(normalized_query, limit=limit)

    async def crawl_and_store_results(
        self,
        *,
        db: Session,
        user_id: int,
        results: list[dict[str, str]],
        company_id: int | None = None,
    ) -> list[dict[str, Any]]:
        """Crawl and persist discovered results into documents."""
        stored_results: list[dict[str, Any]] = []
        for position, result in enumerate(results, start=1):
            crawl_result = await crawl_service.crawl_url(result["url"])
            document = self._store_document(
                db=db,
                user_id=user_id,
                company_id=company_id,
                title=result["title"],
                url=result["url"],
                snippet=result["snippet"],
                crawl_result=crawl_result,
            )
            stored_results.append(
                {
                    "rank": position,
                    "title": result["title"],
                    "url": result["url"],
                    "snippet": result["snippet"],
                    "source": result["source"],
                    "document_id": document.document_id,
                    "status_code": crawl_result.get("status_code"),
                    "provider": crawl_result.get("metadata", {}).get("provider"),
                    "text_preview": (crawl_result.get("text") or "")[:280],
                }
            )
        return stored_results

    def build_company_query(
        self,
        db: Session,
        user_id: int,
        *,
        company_id: int | None = None,
        query: str | None = None,
    ) -> tuple[str, int | None]:
        """Resolve a search query from either raw text or an owned company."""
        if query and query.strip():
            return query.strip(), company_id

        if company_id is None:
            raise ValueError("Either query or company_id is required")

        company = (
            db.query(Company)
            .filter(Company.company_id == company_id, Company.user_id == user_id)
            .first()
        )
        if not company:
            raise ValueError("Company not found")

        parts = [company.name]
        if company.domain:
            parts.append(company.domain)
        if company.industry:
            parts.append(company.industry)
        return " ".join(part for part in parts if part), company.company_id

    async def _search_web(self, query: str, *, limit: int) -> list[dict[str, str]]:
        """Discover candidate URLs from the configured provider chain."""
        logger.info("Searching web for query=%s", query)

        async with httpx.AsyncClient(
            timeout=self.timeout_seconds,
            headers={"User-Agent": self.user_agent},
            follow_redirects=True,
        ) as client:
            ddg_results = await self._search_duckduckgo(client, query, limit=limit)
            if ddg_results:
                return ddg_results

            brave_results = await self._search_brave_api(client, query, limit=limit)
            if brave_results:
                return brave_results

        browser_results = await self._search_with_bing_browser(query, limit=limit)
        if browser_results:
            trace_logic(
                logger,
                "search.provider.success",
                provider="bing_playwright",
                query=query,
                results_count=len(browser_results),
            )
            return browser_results

        domain_results = await self._discover_from_query_domains(query, limit=limit)
        if domain_results:
            trace_logic(
                logger,
                "search.provider.success",
                provider="domain_discovery",
                query=query,
                results_count=len(domain_results),
            )
            return domain_results

        raise RuntimeError("No search results returned for query")

    async def _search_duckduckgo(
        self,
        client: httpx.AsyncClient,
        query: str,
        *,
        limit: int,
    ) -> list[dict[str, str]]:
        """Run DuckDuckGo HTML search as the free primary provider."""
        response = await client.get("https://html.duckduckgo.com/html/", params={"q": query})
        response.raise_for_status()
        results = self._parse_duckduckgo_results(response.text, limit=limit)
        if results:
            trace_logic(
                logger,
                "search.provider.success",
                provider="duckduckgo",
                query=query,
                results_count=len(results),
            )
            return results
        trace_logic(
            logger,
            "search.provider.empty",
            provider="duckduckgo",
            query=query,
        )
        return []

    async def _search_brave_api(
        self,
        client: httpx.AsyncClient,
        query: str,
        *,
        limit: int,
    ) -> list[dict[str, str]]:
        """Run Brave Search API as the authenticated backup provider."""
        if not self.brave_api_key:
            trace_logic(
                logger,
                "search.provider.skipped",
                provider="brave_api",
                query=query,
                reason="missing_api_key",
            )
            return []

        response = await client.get(
            "https://api.search.brave.com/res/v1/web/search",
            params={"q": query, "count": limit},
            headers={
                "User-Agent": self.user_agent,
                "Accept": "application/json",
                "X-Subscription-Token": self.brave_api_key,
            },
        )
        response.raise_for_status()
        results = self._parse_brave_results(response.json(), limit=limit)
        if results:
            trace_logic(
                logger,
                "search.provider.success",
                provider="brave_api",
                query=query,
                results_count=len(results),
            )
            return results
        trace_logic(
            logger,
            "search.provider.empty",
            provider="brave_api",
            query=query,
        )
        return []

    async def _search_with_bing_browser(
        self,
        query: str,
        *,
        limit: int,
    ) -> list[dict[str, str]]:
        """Use a real browser session for Bing when HTML requests are challenged."""
        try:
            from playwright.async_api import async_playwright
        except ModuleNotFoundError:
            return []

        url = f"https://www.bing.com/search?q={quote_plus(query)}"
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            page = await browser.new_page()
            try:
                await page.goto(url, wait_until="load", timeout=60000)
                try:
                    await page.wait_for_selector("li.b_algo h2 a", timeout=15000)
                except Exception:
                    await page.wait_for_timeout(2000)

                items = page.locator("li.b_algo")
                count = await items.count()
                results: list[dict[str, str]] = []
                for index in range(min(count, limit)):
                    item = items.nth(index)
                    link = item.locator("h2 a").first
                    href = await link.get_attribute("href")
                    normalized_href = self._extract_bing_target_url(href or "")
                    if not normalized_href.startswith(("http://", "https://")):
                        continue

                    title = (await link.inner_text()).strip() or normalized_href
                    snippet_locator = item.locator(".b_caption p").first
                    snippet = ""
                    if await snippet_locator.count():
                        snippet = (await snippet_locator.inner_text()).strip()

                    results.append(
                        {
                            "title": title,
                            "url": normalized_href,
                            "snippet": snippet,
                            "source": urlparse(normalized_href).netloc,
                        }
                    )
                return results
            finally:
                await browser.close()

    def _parse_duckduckgo_results(self, html: str, *, limit: int) -> list[dict[str, str]]:
        """Parse DuckDuckGo HTML search response into normalized links."""
        soup = BeautifulSoup(html, "html.parser")
        parsed_results: list[dict[str, str]] = []

        if soup.select_one(".anomaly-modal__modal"):
            return []

        for link in soup.select("a.result__a"):
            raw_url = link.get("href") or ""
            normalized_url = self._extract_target_url(raw_url)
            if not normalized_url.startswith(("http://", "https://")):
                continue

            container = link.find_parent(class_="result")
            snippet_node = None
            if container:
                snippet_node = container.select_one(".result__snippet")

            parsed_results.append(
                {
                    "title": link.get_text(" ", strip=True) or normalized_url,
                    "url": normalized_url,
                    "snippet": snippet_node.get_text(" ", strip=True) if snippet_node else "",
                    "source": urlparse(normalized_url).netloc,
                }
            )
            if len(parsed_results) >= limit:
                break

        return parsed_results

    def _parse_bing_results(self, html: str, *, limit: int) -> list[dict[str, str]]:
        """Parse Bing public HTML search results."""
        soup = BeautifulSoup(html, "html.parser")
        parsed_results: list[dict[str, str]] = []

        for item in soup.select("li.b_algo"):
            link = item.select_one("h2 a")
            if not link:
                continue

            normalized_url = self._extract_bing_target_url(link.get("href") or "")
            if not normalized_url.startswith(("http://", "https://")):
                continue

            snippet_node = item.select_one(".b_caption p")
            parsed_results.append(
                {
                    "title": link.get_text(" ", strip=True) or normalized_url,
                    "url": normalized_url,
                    "snippet": snippet_node.get_text(" ", strip=True) if snippet_node else "",
                    "source": urlparse(normalized_url).netloc,
                }
            )
            if len(parsed_results) >= limit:
                break

        return parsed_results

    def _parse_brave_results(
        self,
        payload: dict[str, Any],
        *,
        limit: int,
    ) -> list[dict[str, str]]:
        """Normalize Brave Search API JSON into internal search results."""
        parsed_results: list[dict[str, str]] = []
        for item in payload.get("web", {}).get("results", []):
            url = item.get("url") or ""
            if not url.startswith(("http://", "https://")):
                continue
            parsed_results.append(
                {
                    "title": item.get("title") or url,
                    "url": url,
                    "snippet": item.get("description") or "",
                    "source": urlparse(url).netloc,
                }
            )
            if len(parsed_results) >= limit:
                break
        return parsed_results

    def _extract_target_url(self, raw_url: str) -> str:
        """Unwrap DuckDuckGo redirect links into direct URLs."""
        if not raw_url:
            return ""
        parsed = urlparse(raw_url)
        if parsed.netloc.endswith("duckduckgo.com") and parsed.path.startswith("/l/"):
            params = parse_qs(parsed.query)
            uddg = params.get("uddg", [""])[0]
            return unquote(uddg)
        return raw_url

    def _extract_bing_target_url(self, raw_url: str) -> str:
        """Unwrap Bing redirect links into direct URLs when possible."""
        if not raw_url:
            return ""

        parsed = urlparse(raw_url)
        if parsed.netloc.endswith("bing.com") and parsed.path.startswith("/ck/a"):
            params = parse_qs(parsed.query)
            encoded = params.get("u", [""])[0]
            if encoded:
                encoded = encoded[2:] if encoded.startswith("a1") else encoded
                padding = "=" * (-len(encoded) % 4)
                try:
                    decoded = base64.urlsafe_b64decode(f"{encoded}{padding}").decode("utf-8")
                    if decoded.startswith(("http://", "https://")):
                        return decoded
                except Exception:
                    return raw_url

        return raw_url

    async def _discover_from_query_domains(
        self,
        query: str,
        *,
        limit: int,
    ) -> list[dict[str, str]]:
        """Discover likely URLs directly from domains mentioned in the query."""
        domains = self._infer_domains_from_query(query)
        if not domains:
            return []

        discovered: list[dict[str, str]] = []
        seen_urls: set[str] = set()
        async with httpx.AsyncClient(
            timeout=self.timeout_seconds,
            headers={"User-Agent": self.user_agent},
            follow_redirects=True,
        ) as client:
            for domain in domains:
                urls = await self._discover_domain_urls(client, domain, limit=limit)
                for url in urls:
                    if url in seen_urls:
                        continue
                    seen_urls.add(url)
                    discovered.append(
                        {
                            "title": self._title_from_url(url),
                            "url": url,
                            "snippet": f"Discovered directly from {domain}",
                            "source": domain,
                        }
                    )
                    if len(discovered) >= limit:
                        return discovered
        return discovered

    def _infer_domains_from_query(self, query: str) -> list[str]:
        """Extract explicit domains from search syntax like site:example.com."""
        domains: list[str] = []
        for match in re.findall(r"site:([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", query):
            domains.append(match.lower())
        for match in re.findall(r"\b([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b", query):
            lowered = match.lower().strip(".")
            if lowered not in domains:
                domains.append(lowered)
        return domains

    async def _discover_domain_urls(
        self,
        client: httpx.AsyncClient,
        domain: str,
        *,
        limit: int,
    ) -> list[str]:
        """Discover crawl targets from sitemap plus common company pages."""
        candidates: list[str] = [f"https://{domain}/"]
        candidates.extend(
            f"https://{domain}{path}"
            for path in [
                "/about",
                "/about-us",
                "/company",
                "/team",
                "/leadership",
                "/management",
                "/careers",
            ]
        )

        sitemap_urls = await self._read_sitemap_urls(client, domain)
        preferred_terms = ("about", "team", "leadership", "management", "company", "people")
        for url in sitemap_urls:
            lowered = url.lower()
            if any(term in lowered for term in preferred_terms):
                candidates.append(url)
        for url in sitemap_urls:
            candidates.append(url)

        discovered: list[str] = []
        seen: set[str] = set()
        for url in candidates:
            if url in seen:
                continue
            seen.add(url)
            try:
                response = await client.head(url)
                if response.status_code >= 400:
                    response = await client.get(url)
                if response.status_code < 400:
                    discovered.append(str(response.url))
            except Exception:
                continue
            if len(discovered) >= limit:
                break
        return discovered

    async def _read_sitemap_urls(self, client: httpx.AsyncClient, domain: str) -> list[str]:
        """Read a basic XML sitemap if the target site publishes one."""
        for sitemap_path in ["/sitemap.xml", "/sitemap_index.xml"]:
            try:
                response = await client.get(f"https://{domain}{sitemap_path}")
                if response.status_code >= 400:
                    continue
                root = ET.fromstring(response.text)
                urls = [node.text.strip() for node in root.findall(".//{*}loc") if node.text]
                if urls:
                    return urls[:50]
            except Exception:
                continue
        return []

    def _title_from_url(self, url: str) -> str:
        """Create a readable fallback title from a discovered URL."""
        parsed = urlparse(url)
        path = parsed.path.strip("/")
        if not path:
            return parsed.netloc
        parts = [part.replace("-", " ").replace("_", " ") for part in path.split("/") if part]
        return " / ".join(part.title() for part in parts)

    def _store_document(
        self,
        *,
        db: Session,
        user_id: int,
        company_id: int | None,
        title: str,
        url: str,
        snippet: str,
        crawl_result: dict[str, Any],
    ) -> Document:
        """Persist a crawled search hit into the documents table."""
        host = urlparse(url).netloc or "unknown-source"
        text_body = crawl_result.get("text") or ""
        markdown = crawl_result.get("markdown") or ""
        extracted_text = "\n\n".join(part for part in [snippet, text_body, markdown] if part)

        document = Document(
            user_id=user_id,
            file_name=self._safe_file_name(title=title, host=host),
            file_path=f"/search/{host}/",
            document_type="web_search_result",
            extracted_text=extracted_text[:20000],
            associated_company_id=company_id,
        )
        db.add(document)
        db.flush()
        return document

    def _upsert_cache(
        self,
        *,
        db: Session,
        cache_key: str,
        results: list[dict[str, Any]],
        query: str,
        company_id: int | None,
    ) -> MemoryStore:
        """Store a reusable search cache snapshot for later automation."""
        memory = db.query(MemoryStore).filter(MemoryStore.memory_key == cache_key).first()
        payload = {
            "query": query,
            "company_id": company_id,
            "results": results,
            "cached_at": datetime.utcnow().isoformat(),
        }
        if memory:
            memory.memory_value = payload
            memory.accessed_at = datetime.utcnow()
            memory.ttl_seconds = 86400
            return memory

        memory = MemoryStore(
            memory_key=cache_key,
            memory_value=payload,
            ttl_seconds=86400,
        )
        db.add(memory)
        db.flush()
        return memory

    def _cache_key(self, *, user_id: int, query: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", query.lower()).strip("-")[:80] or "search"
        return f"user:{user_id}:search:{slug}"

    def _normalize_query(self, query: str) -> str:
        normalized = " ".join(query.split())
        if not normalized:
            raise ValueError("Search query cannot be empty")
        return normalized

    def _safe_file_name(self, *, title: str, host: str) -> str:
        base = re.sub(r"[^a-zA-Z0-9._-]+", "-", title.strip()).strip("-")[:80] or "search-result"
        return f"{base}-{quote_plus(host)}.txt"


search_service = SearchService()
