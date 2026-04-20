import pytest

from app.services.crawl_service import CrawlService


@pytest.mark.asyncio
async def test_crawl_url_normalizes_scheme():
    service = CrawlService()

    result = await service.crawl_url("example.com")

    assert result["url"] == "https://example.com"
    assert result["status_code"] == 200


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
