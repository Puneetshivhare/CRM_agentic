# Production Readiness Test Plan

## Scope

This plan covers the current CRM system across:

- API functional behavior
- Authentication and authorization security
- File ingestion robustness (CSV/PDF)
- Agent workflow resilience
- Performance, reliability, and operational readiness

## Automated Test Suite (Implemented)

Run from `backend/`:

```bash
pytest
```

Current automated coverage includes:

- Auth cryptography and JWT validation
- Auth API (`signup`, `login`, `me`) integration flows
- Health/system endpoints (`/`, `/health`)
- File service parsing/limits/type validation
- Crawl service normalization and extraction behavior
- Security expectation tests (with `xfail` markers for known current gaps)

## Production Gate Criteria

Use these as release criteria:

1. No failing tests in `unit` or `integration`.
2. Security `xfail` tests are either resolved (moved to passing tests) or explicitly accepted with risk sign-off.
3. P95 API latency under target for critical endpoints (`/api/auth/*`, `/api/prospects`, `/api/documents/upload`).
4. Error budget accepted: 5xx rate < 1% over representative load window.
5. Structured logs and health checks validated in deployment environment.

## Functional Test Cases

| ID | Area | Scenario | Expected Result | Status |
|---|---|---|---|---|
| F-01 | Auth | Signup with valid email/password | `201`, token returned, user created | Automated |
| F-02 | Auth | Signup with duplicate email | `409` conflict | Automated |
| F-03 | Auth | Login with wrong credentials | `401` generic error | Automated |
| F-04 | Auth | `/api/auth/me` with valid JWT | `200` and user payload | Automated |
| F-05 | System | `/health` with DB unavailable | `503 degraded` | Automated |
| F-06 | System | `/health` with DB available | `200 ok` | Automated |
| F-07 | File | CSV ingestion with valid rows | Parsed rows and columns | Automated |
| F-08 | File | Empty CSV body | Rejected with clear error | Automated |
| F-09 | File | Oversized upload | Rejected by size guardrail | Automated |

## Security Test Cases

| ID | Area | Scenario | Expected Result | Status |
|---|---|---|---|---|
| S-01 | JWT | Tampered token | `401` unauthorized | Automated |
| S-02 | JWT | Missing required claims | `401` unauthorized | Automated |
| S-03 | AuthN | `/api/prospects` without JWT | `401` | Automated (`xfail`) |
| S-04 | AuthN | `/api/documents` without JWT | `401` | Automated (`xfail`) |
| S-05 | AuthN | `/api/enrichment/trigger` without JWT | `401` | Automated (`xfail`) |
| S-06 | Frontend token storage | JWT not persisted in `localStorage` | True | Automated (`xfail`) |
| S-07 | Abuse protection | Repeated auth attempts are rate-limited | `429` after threshold | Manual/Pending |
| S-08 | CORS policy | Only approved origins allowed | Disallowed origin blocked | Manual/Pending |
| S-09 | Dependency risk | `pip-audit` high/critical findings | 0 unresolved criticals | Manual/Pending |

## Reliability and Resilience Test Cases

| ID | Area | Scenario | Expected Result | Status |
|---|---|---|---|---|
| R-01 | Startup | App boots with invalid DB URL | Service stays alive, health degraded | Automated (partial via health logic) |
| R-02 | Crawl | URL without scheme | Normalized and processed | Automated |
| R-03 | Crawl | Empty URL input | Validation failure, no crash | Automated |
| R-04 | File service | Non-UTF8 CSV payload | Falls back safely or rejects with reason | Automated |
| R-05 | Agent workflows | Downstream service failure | Error captured, execution marked failed, no crash | Manual/Pending |

## Performance and Load Test Cases (Recommended)

| ID | Endpoint/Flow | Load Profile | Target |
|---|---|---|---|
| P-01 | `POST /api/auth/login` | 50 RPS for 5 min | P95 < 300ms, error rate < 1% |
| P-02 | `GET /api/prospects` | 100 concurrent users | P95 < 500ms |
| P-03 | `POST /api/documents/upload` (CSV) | 20 concurrent uploads | No worker crash, bounded memory |
| P-04 | Full enrichment trigger | 10 concurrent jobs | Graceful degradation, stable queue behavior |

Suggested tool: `k6` or Locust in staging with production-like infrastructure.

## Observability and Ops Test Cases

| ID | Area | Check | Status |
|---|---|---|---|
| O-01 | Logging | JSON logs include request correlation fields | Manual/Pending |
| O-02 | Health probes | Liveness/readiness behave correctly in orchestrator | Manual/Pending |
| O-03 | Alerts | 5xx spike and latency alerting configured | Manual/Pending |
| O-04 | Backups | DB restore drill validated | Manual/Pending |

## Current Risk Summary

These are the main blockers before true production launch:

1. Non-auth routes still do not enforce JWT-based authorization.
2. Frontend stores JWT in `localStorage` instead of HttpOnly secure cookies.
3. Rate limiting and abuse tests are not yet fully implemented and validated.
4. Load/performance tests have not been run in staging yet.

## Next Actions

1. Implement shared JWT dependency across `prospects`, `documents`, and `enrichment` routes.
2. Migrate frontend auth token storage to HttpOnly cookie strategy.
3. Add rate-limiter middleware tests for auth and expensive endpoints.
4. Run staging load tests and set hard release thresholds.
