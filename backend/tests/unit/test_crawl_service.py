import pytest

from app.services.crawl_service import CrawlService


@pytest.mark.asyncio
async def test_crawl_url_normalizes_scheme(monkeypatch):
    service = CrawlService(provider="crawl4ai")

    async def fake_crawl(url: str):
        return {
            "url": url,
            "status_code": 200,
            "title": "Example",
            "html": "<html><body>Example</body></html>",
            "text": "Example",
            "markdown": "",
            "metadata": {"provider": "crawl4ai"},
        }

    monkeypatch.setattr(service, "_crawl_with_crawl4ai", fake_crawl)

    result = await service.crawl_url("example.com")

    assert result["url"] == "https://example.com"
    assert result["status_code"] == 200


@pytest.mark.asyncio
async def test_crawl_url_falls_back_to_http_when_browser_provider_fails(monkeypatch):
    service = CrawlService(provider="crawl4ai")

    async def raise_browser_error(url: str):
        raise RuntimeError("browser boot failed")

    async def fake_http(url: str):
        return {
            "url": url,
            "status_code": 200,
            "title": "Example",
            "html": "<html><body>Fallback</body></html>",
            "text": "Fallback",
            "markdown": "",
            "metadata": {"provider": "http"},
        }

    monkeypatch.setattr(service, "_crawl_with_crawl4ai", raise_browser_error)
    monkeypatch.setattr(service, "_crawl_with_http", fake_http)

    result = await service.crawl_url("example.com")

    assert result["url"] == "https://example.com"
    assert result["metadata"]["provider"] == "http"
    assert result["metadata"]["fallback_used"] is True
    assert "browser boot failed" in result["metadata"]["fallback_reason"]


@pytest.mark.asyncio
async def test_crawl_url_rejects_empty_url():
    service = CrawlService()

    with pytest.raises(ValueError, match="URL cannot be empty"):
        await service.crawl_url("")


@pytest.mark.asyncio
async def test_extract_company_data_strips_html_noise():
    service = CrawlService()
    html = """
    <html>
      <head>
        <meta name="description" content="AI-first CRM platform">
        <style>.hidden { display: none; }</style>
      </head>
      <body>
        <script>alert("x")</script>
        <h1>Agentic CRM</h1>
        <p>Pipeline intelligence for modern sales teams.</p>
      </body>
    </html>
    """

    extracted = await service.extract_company_data(html, "example.com")

    assert extracted["domain"] == "example.com"
    assert extracted["description"] == "AI-first CRM platform"
    assert extracted["headings"] == ["Agentic CRM"]
    assert "alert(" not in extracted["text"]


@pytest.mark.asyncio
async def test_crawl_company_website_returns_failed_on_exception(monkeypatch):
    service = CrawlService()

    async def raise_timeout(url: str):  # pragma: no cover - helper
        raise TimeoutError("network timeout")

    monkeypatch.setattr(service, "crawl_url", raise_timeout)

    result = await service.crawl_company_website("example.com")

    assert result["status"] == "failed"
    assert result["domain"] == "example.com"
    assert "network timeout" in result["error"]
