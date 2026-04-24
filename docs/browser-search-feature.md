# Browser Search Feature

## Goal

Add two browser-driven capabilities on top of the current backend search stack:

1. `Analyst Assist`
2. `Backend Browser`

## Search Stack

The current intended discovery order is:

1. DuckDuckGo HTML
2. Brave Search API
3. Browser-based public search fallback
4. Domain discovery fallback
5. Crawl4AI + Playwright crawl and extraction

## Analyst Assist

### Purpose

Use a real visible browser session for guided research when the user wants to:

- inspect search results manually
- validate agent choices
- continue through blocked pages
- select specific result pages to crawl

### UX Shape

- user starts a research session
- browser opens with the search task context
- search query is executed automatically
- user can click, approve, or reject result pages
- approved pages are saved into the same backend storage as automated search

## Backend Browser

### Purpose

Use a browser-only fallback inside the backend when the discovery chain fails but the task remains valuable enough to continue automatically.

### Guardrails

- not the default search path
- strict timeout budget
- full trace logging
- screenshots or HTML snapshots on failure
- shared persistence with normal search

## Shared Storage

Both browser features should write into:

- `dim_documents`
- `memory_store`
- `fact_agent_executions`

## Suggested Future API Surface

- `POST /api/search/browser/session`
- `POST /api/search/browser/session/{id}/start`
- `POST /api/search/browser/session/{id}/accept-page`
- `POST /api/search/browser/session/{id}/crawl-selection`
- `GET /api/search/browser/session/{id}`

## Implementation Order

1. Add session tracking model and execution logs
2. Add analyst-assist session endpoint
3. Add backend-browser fallback service
4. Connect browser outputs to enrichment and automation

## Notes

- Analyst Assist is best for human-in-the-loop research.
- Backend Browser should remain a narrow fallback.
- Downstream automation should not care whether a page came from DDG, Brave, or browser mode.
