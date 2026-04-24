from app.services.search_service import SearchService


def test_parse_duckduckgo_results_unwraps_redirects():
    service = SearchService()
    html = """
    <html>
      <body>
        <div class="result">
          <a class="result__a" href="https://duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com%2Fteam">Example Team</a>
          <a class="result__snippet">Leadership and company information.</a>
        </div>
      </body>
    </html>
    """

    results = service._parse_duckduckgo_results(html, limit=5)

    assert len(results) == 1
    assert results[0]["url"] == "https://example.com/team"
    assert results[0]["title"] == "Example Team"
    assert results[0]["snippet"] == "Leadership and company information."
    assert results[0]["source"] == "example.com"


def test_cache_key_is_stable_and_namespaced():
    service = SearchService()

    cache_key = service._cache_key(user_id=7, query="ACME Inc leadership")

    assert cache_key == "user:7:search:acme-inc-leadership"


def test_parse_bing_results_extracts_title_url_and_snippet():
    service = SearchService()
    html = """
    <html>
      <body>
        <li class="b_algo">
          <h2><a href="https://vercel.com/about">Vercel About</a></h2>
          <div class="b_caption"><p>Leadership, company story, and platform overview.</p></div>
        </li>
      </body>
    </html>
    """

    results = service._parse_bing_results(html, limit=5)

    assert len(results) == 1
    assert results[0]["url"] == "https://vercel.com/about"
    assert results[0]["title"] == "Vercel About"
    assert results[0]["snippet"] == "Leadership, company story, and platform overview."


def test_extract_bing_target_url_decodes_redirect_target():
    service = SearchService()
    raw_url = (
        "https://www.bing.com/ck/a?!&&p=abc123"
        "&u=a1aHR0cHM6Ly92ZXJjZWwuY29tL2Fib3V0"
        "&ntb=1"
    )

    normalized_url = service._extract_bing_target_url(raw_url)

    assert normalized_url == "https://vercel.com/about"


def test_parse_brave_results_extracts_title_url_and_snippet():
    service = SearchService()
    payload = {
        "web": {
            "results": [
                {
                    "title": "Vercel About",
                    "url": "https://vercel.com/about",
                    "description": "Leadership, mission, and company overview.",
                }
            ]
        }
    }

    results = service._parse_brave_results(payload, limit=5)

    assert len(results) == 1
    assert results[0]["url"] == "https://vercel.com/about"
    assert results[0]["title"] == "Vercel About"
    assert results[0]["snippet"] == "Leadership, mission, and company overview."
