# Tech Stack Summary - Agentic CRM

**Project:** SalesAI Pro (Agentic CRM)  
**Status:** MVP Ready for Development  
**Date:** April 2026

---

## 1. Technology Stack Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FRONTEND LAYER                               │
├─────────────────────────────────────────────────────────────────────┤
│ React 18 + Next.js 14    │ TypeScript      │ Tailwind CSS           │
│ State: React Hooks       │ API: Axios      │ UI: Shadcn/Radix       │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                          HTTP/WebSocket (REST API)
                                    │
┌─────────────────────────────────────────────────────────────────────┐
│                        BACKEND LAYER                                │
├─────────────────────────────────────────────────────────────────────┤
│ FastAPI 0.100+          │ Python 3.11+    │ Uvicorn (ASGI server)  │
│ ORM: SQLAlchemy 2.0     │ Validation: Pydantic v2                   │
│ Async/Await support     │ Type hints      │ Auto API docs (Swagger)│
└─────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
         ┌──────────▼──┐  ┌────────▼──────┐  ┌──────▼──────┐
         │  Job Queue   │  │  Memory       │  │  Services   │
         │  (Celery)    │  │  (Redis +     │  │  (Agents)   │
         │              │  │   Postgres)   │  │             │
         │              │  │               │  │             │
         │ Async tasks  │  │ Cache layer   │  │ - Crawl     │
         │ Background   │  │ Distributed   │  │ - Gemini    │
         │ workers      │  │ memory        │  │ - RAG       │
         │              │  │               │  │ - Skills    │
         │              │  │               │  │ - Rules     │
         └──────────────┘  └───────────────┘  └─────────────┘
                                    │
          ┌─────────────────────────┼──────────────────────────┐
          │                         │                          │
    ┌─────▼──────┐        ┌─────────▼────────┐        ┌────────▼─────┐
    │  Postgres  │        │  Supabase Auth   │        │  Vector DB   │
    │  (Data +   │        │  (JWT tokens)    │        │  (Postgres   │
    │   Memory)  │        │  (Isolated)      │        │   pgvector)  │
    │            │        │                  │        │              │
    │ - Prospects│        │ - User auth      │        │ - Embeddings │
    │ - Companies│        │ - Login/Signup   │        │ - Similarity │
    │ - Interact.│        │ - Token validation       │   search     │
    │ - Events   │        │                  │        │              │
    │ - Memory   │        │                  │        │              │
    └────────────┘        └──────────────────┘        └──────────────┘
          │
    Data: Snowflake
    Schema (Star)
          │
    ┌─────────────────────────────────────────────┐
    │ External APIs (Non-blocking)               │
    ├─────────────────────────────────────────────┤
    │ Gemini 2.5 Flash  │ Crawl4AI (web scraping)│
    │ (LLM)             │ LightPanda (rendering) │
    │ Gemini Embeddings │ (JS-heavy sites)       │
    │ (768-dim vectors) │                        │
    └─────────────────────────────────────────────┘
```

---

## 2. Detailed Tech Stack By Layer

### 2.1 Frontend Stack

| Technology | Version | Purpose | Why? |
|---|---|---|---|
| **React** | 18+ | UI library | Modern hooks, concurrent rendering |
| **Next.js** | 14+ | Framework | Server-side rendering, API routes, file-based routing |
| **TypeScript** | 5+ | Language | Type safety, better DX, fewer runtime errors |
| **Tailwind CSS** | 3.4+ | Styling | Utility-first, fast development, responsive |
| **Shadcn/Radix** | Latest | UI Components | Accessible, unstyled, customizable |
| **Axios** | 1.6+ | HTTP Client | Simpler than Fetch, request/response interceptors |
| **React Query** | 5+ | Data Fetching | Caching, background sync, stale-while-revalidate |
| **Zustand** | 4+ | State Management | Lightweight alternative to Redux |
| **date-fns** | 3+ | Date Utilities | Immutable, composable, tree-shakable |
| **Lodash** | 4+ | Utilities | Debounce, throttle, deep merge, etc. |
| **Vitest** | Latest | Unit Testing | Fast, ESM-native, low config |
| **Playwright** | Latest | E2E Testing | Real browser automation, cross-browser |

**Frontend folder structure:**
```
frontend/
├── app/
│   ├── (main)/
│   │   └── page.tsx           # Dashboard
│   ├── prospects/
│   │   ├── page.tsx           # List + table
│   │   ├── [id]/page.tsx      # Detail view
│   │   └── enrich/page.tsx    # Bulk enrich
│   ├── companies/
│   ├── monitoring/
│   ├── skills/
│   ├── rules/
│   ├── codex/
│   │   ├── page.tsx           # Main dashboard
│   │   ├── decision-logs/
│   │   ├── metrics/
│   │   └── prompt-logs/
│   ├── api/                   # API route handlers (proxy to backend)
│   ├── components/            # Reusable components
│   │   ├── ProspectTable.tsx
│   │   ├── EnrichmentStatus.tsx
│   │   ├── CodexDashboard.tsx
│   │   └── ...
│   ├── hooks/                 # Custom React hooks
│   ├── lib/                   # Utilities
│   └── layout.tsx             # Root layout
├── public/                    # Static assets
├── package.json
└── next.config.js
```

---

### 2.2 Backend Stack

| Technology | Version | Purpose | Why? |
|---|---|---|---|
| **Python** | 3.11+ | Language | Mature, great for ML/AI, extensive libraries |
| **FastAPI** | 0.100+ | Web Framework | Async-first, fast, auto-documentation, validation |
| **Uvicorn** | 0.23+ | ASGI Server | Fast, lightweight, full async support |
| **SQLAlchemy** | 2.0+ | ORM | Type hints, async support, powerful queries |
| **Alembic** | 1.12+ | DB Migrations | Version control for schema changes |
| **Pydantic** | 2+ | Data Validation | JSON schema, automatic validation, serialization |
| **python-jose** | 3.3+ | JWT Tokens | Token creation/validation, multiple algorithms |
| **Celery** | 5.3+ | Task Queue | Async job execution, scheduled tasks |
| **Redis** | 5+ (Python lib) | Cache & Broker | Fast cache, Celery broker, pub/sub |
| **Requests** | 2.31+ | HTTP Client | Crawl4AI, external API calls |
| **aiohttp** | 3.8+ | Async HTTP | Non-blocking HTTP for high concurrency |
| **tenacity** | 8.2+ | Retry Library | Exponential backoff, conditional retries |
| **python-dotenv** | 1.0+ | Config | Load .env variables |
| **pytest** | 7.4+ | Testing | Fixtures, async support, powerful assertions |
| **pytest-asyncio** | Latest | Async Testing | Run async tests with pytest |
| **python-multipart** | 0.0.6+ | File Upload | Parse multipart form data |
| **python-json-logger** | Latest | JSON Logging | Structured logging for monitoring |
| **prometheus-client** | Latest | Metrics | Expose Prometheus metrics |

**Backend folder structure:**
```
backend/
├── app/
│   ├── main.py               # FastAPI app init, middleware
│   ├── config.py             # Settings/env vars
│   ├── database.py           # DB connection, session
│   ├── auth.py               # JWT validation
│   │
│   ├── agents/               # Agent implementations (core)
│   │   ├── base_agent.py
│   │   ├── research_agent.py
│   │   ├── enrichment_agent.py
│   │   ├── monitoring_agent.py
│   │   ├── outreach_agent.py
│   │   ├── analytics_agent.py
│   │   └── orchestrator.py
│   │
│   ├── memory/               # Distributed memory system
│   │   ├── memory_store.py
│   │   ├── hierarchical_memory.py
│   │   ├── vector_memory.py
│   │   └── memory_interface.py
│   │
│   ├── models/               # Pydantic + SQLAlchemy models
│   │   ├── prospect.py
│   │   ├── company.py
│   │   ├── interaction.py
│   │   ├── enrichment_event.py
│   │   ├── agent_execution.py
│   │   ├── document.py
│   │   ├── skill.py
│   │   └── rule.py
│   │
│   ├── routes/               # API endpoints
│   │   ├── prospects.py
│   │   ├── companies.py
│   │   ├── enrichment.py
│   │   ├── monitoring.py
│   │   ├── skills.py
│   │   ├── rules.py
│   │   ├── documents.py
│   │   ├── codex.py
│   │   └── agents.py
│   │
│   ├── services/             # Business logic
│   │   ├── crawl_service.py        # Crawl4AI wrapper
│   │   ├── gemini_service.py       # Gemini API
│   │   ├── rag_service.py          # RAG embeddings
│   │   ├── skill_executor.py       # Run user skills
│   │   ├── rule_evaluator.py       # Evaluate rules
│   │   ├── job_queue.py            # Celery tasks
│   │   ├── cache_service.py        # Multi-layer caching
│   │   └── quota_manager.py        # Token quotas
│   │
│   ├── codex/                # Observability system
│   │   ├── decision_logger.py
│   │   ├── test_generator.py
│   │   ├── prompt_optimizer.py
│   │   ├── metrics_tracker.py
│   │   └── dashboard_data.py
│   │
│   ├── middleware/           # HTTP middleware
│   │   ├── auth.py
│   │   ├── rate_limit.py
│   │   └── error_handler.py
│   │
│   └── utils/
│       ├── logger.py
│       ├── validators.py
│       ├── constants.py
│       └── helpers.py
│
├── migrations/               # Alembic DB migrations
├── tests/
│   ├── test_agents.py
│   ├── test_memory.py
│   ├── test_api.py
│   └── ...
├── requirements.txt          # Python dependencies
├── Dockerfile
└── .dockerignore
```

---

### 2.3 Database Stack

| Technology | Purpose | Details |
|---|---|---|
| **PostgreSQL 15** | Primary OLTP DB | Structured data, fast queries, indexes |
| **pgvector** | Vector search | Semantic similarity, embeddings (768-dim) |
| **Supabase** | Auth layer | JWT tokens, user management, isolated |
| **Alembic** | Schema versioning | Track schema changes, rollback capability |

**Schema Design: Snowflake Schema**
- Dimensions: prospects, companies, documents, skills, rules
- Facts: interactions, enrichment_events, agent_executions
- Memory: memory_store (KV), memory_vector (embeddings)

---

### 2.4 External Services

| Service | Purpose | Integration | Cost |
|---|---|---|---|
| **Gemini 2.5 Flash** | LLM for enrichment | REST API, tokens tracked | ~$0.5/1M tokens (input) |
| **Gemini Embeddings** | Vector generation | Batch embeddings, cached | ~$0.02/1K embeddings |
| **Crawl4AI** | Web scraping | Python library, async | Free (self-hosted) |
| **LightPanda** | JS rendering | Python library wrapper | Free (self-hosted) |

---

## 3. Why These Choices?

### 3.1 Frontend: React + Next.js + TypeScript

**Rationale:**
- React: Most popular, large ecosystem, many components
- Next.js: Server-side rendering (SEO), API routes, file routing (no config)
- TypeScript: Catch bugs at dev time, better IDE support
- Tailwind: No CSS file management, utility-first = fast development

**Alternative Considered:**
- Vue.js: Smaller community, fewer components
- Svelte: Too niche, harder to hire developers
- Plain JavaScript: No type safety, poor DX

---

### 3.2 Backend: FastAPI + Python

**Rationale:**
- FastAPI: Fastest Python framework, async-native, auto docs, data validation
- Python: Best for ML/AI, Gemini SDKs, extensive libraries
- SQLAlchemy: Most mature ORM, type hints, async support
- Celery: Industry standard for async jobs (used at Spotify, Pinterest, etc.)

**Alternative Considered:**
- Node.js: Would duplicate frontend stack, less ideal for ML
- Go: No native Gemini SDK, harder for quick iteration
- Django: Too heavy, not async-first

---

### 3.3 Database: PostgreSQL + pgvector

**Rationale:**
- PostgreSQL: Open source, reliable, pgvector extension for vectors
- pgvector: No separate vector DB needed (MVP), all in one
- Supabase Auth: Simple OAuth, JWT, isolated from data
- Alembic: Version-controlled migrations, safety

**Alternative Considered:**
- MongoDB: No structured schema needed, but Gemini data is relational
- Pinecone: Expensive for MVP, add later if 100K+ documents
- Aurora: Cloud-only, harder to self-host

---

### 3.4 External APIs: Gemini 2.5 Flash

**Rationale:**
- Gemini 2.5 Flash: Cheapest frontier model, fast, good instruction-following
- No fine-tuning needed (yet): Generic extraction works well
- Gemini Embeddings: Same provider, native API support

**Alternative Considered:**
- GPT-4: 10x more expensive, not needed for structured extraction
- Claude: Good but slower/more expensive than Gemini for this use case
- Llama: Self-hosted, but inference is slower (Docker constraint)

---

### 3.5 Crawling: Crawl4AI + LightPanda

**Rationale:**
- Crawl4AI: Open source, Python-first, works in Docker
- LightPanda: Renders JavaScript (modern websites need it)
- No Selenium/Puppeteer overhead: Pure Python, lighter

**Alternative Considered:**
- Selenium: Heavy, slower, Java/Chrome dependency
- PlaywrightPython: Better, but Crawl4AI is simpler
- Scrapy: Overkill for this use case, complex

---

## 4. Dependency Management

### 4.1 Python Requirements (backend/requirements.txt)

```
# Core Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-dotenv==1.0.0

# Database & ORM
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
alembic==1.12.1
pydantic==2.4.2
pydantic-settings==2.0.3

# Authentication
python-jose[cryptography]==3.3.0
PyJWT==2.8.1

# Async & Jobs
celery==5.3.4
redis==5.0.1
aiohttp==3.9.1

# HTTP & APIs
requests==2.31.0
tenacity==8.2.3

# Web Scraping
beautifulsoup4==4.12.2
lxml==4.9.3

# Data Validation
email-validator==2.1.0

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.2

# Monitoring & Logging
python-json-logger==2.0.7
prometheus-client==0.19.0

# Utils
python-multipart==0.0.6
slowapi==0.1.9  # Rate limiting
```

### 4.2 Frontend Dependencies (frontend/package.json)

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "next": "^14.0.0",
    "@types/react": "^18.2.0",
    "typescript": "^5.3.0",
    "tailwindcss": "^3.4.0",
    "@radix-ui/react-*": "latest",
    "shadcn-ui": "latest",
    "axios": "^1.6.0",
    "@tanstack/react-query": "^5.0.0",
    "zustand": "^4.4.0",
    "date-fns": "^2.30.0",
    "lodash": "^4.17.21"
  },
  "devDependencies": {
    "vitest": "^latest",
    "@testing-library/react": "^latest",
    "playwright": "^latest",
    "tailwindcss": "^3.4.0",
    "postcss": "^latest",
    "autoprefixer": "^latest"
  }
}
```

---

## 5. Infrastructure & Deployment

### 5.1 Local Development (Docker Compose)

```yaml
services:
  postgres:15        # Database + memory + vectors
  redis:7-alpine     # Cache + Celery broker
  backend:FastAPI    # Python app
  frontend:Next.js   # React app
```

**Requirements:**
- Docker Desktop (includes Docker Compose)
- WSL 2 on Windows (provided by Docker Desktop)
- 4GB RAM minimum, 8GB recommended

### 5.2 Production Deployment (Future - v1.1)

```
Option A: Cloud (Recommended for v1.1+)
├─ Frontend: Vercel (Next.js optimized)
├─ Backend: Cloud Run / Lambda (serverless)
├─ Database: Cloud SQL (managed Postgres)
├─ Cache: Redis Cloud / ElastiCache
└─ Monitoring: DataDog / New Relic

Option B: Self-hosted (Kubernetes)
├─ EKS / GKE (agent pods)
├─ RDS (database)
├─ ElastiCache (Redis)
└─ CloudFront (CDN)
```

---

## 6. Development Workflow

### 6.1 Local Setup (Day 1)

```bash
# Clone repo
git clone <repo>
cd agentic-crm

# Create .env from template
cp .env.example .env
# Edit .env with your API keys

# Start Docker services
docker-compose up -d

# Wait for Postgres to be ready
docker-compose logs -f postgres | grep "database system is ready"

# Run migrations
docker-compose exec backend alembic upgrade head

# Seed test data (optional)
docker-compose exec backend python scripts/seed_db.py

# Access app
# Frontend: http://localhost:3000
# Backend API docs: http://localhost:8000/docs
# Postgres: localhost:5432 (psql -U crm_user -h localhost agentic_crm)
```

### 6.2 Development Commands

```bash
# Backend
docker-compose exec backend uvicorn app.main:app --reload
docker-compose exec backend pytest tests/

# Frontend
docker-compose exec frontend npm run dev
docker-compose exec frontend npm run test

# Database
docker-compose exec postgres psql -U crm_user agentic_crm
docker-compose exec backend alembic revision --autogenerate -m "Add field"

# Celery worker (for async jobs)
docker-compose exec backend celery -A app.services.job_queue worker -l info

# Redis CLI (for debugging cache)
docker-compose exec redis redis-cli
```

---

## 7. Cost Breakdown (Monthly)

### MVP Phase (April-May 2026)

| Component | Cost | Notes |
|---|---|---|
| Gemini API | $200-500 | ~2M tokens for exploration/testing |
| Postgres (Supabase) | $25-100 | Free tier, then $15/month |
| Docker (local) | $0 | Runs on your machine |
| Storage (local) | $0 | Uses your disk |
| **Total** | **~$300-600/month** | Very affordable MVP |

### v1.1 Phase (Cloud-ready)

| Component | Cost | Notes |
|---|---|---|
| Gemini API | $2,000-5,000 | More enrichment volume |
| Cloud SQL (Postgres) | $100-500 | Managed DB, backup, SSL |
| Cloud Run (Backend) | $50-200 | Pay per request |
| Vercel (Frontend) | $20-50 | Next.js optimized |
| Redis Cloud | $200 | Caching layer |
| Storage | $100 | Documents, PDFs |
| **Total** | **~$3,000-7,000/month** | ~$20/user for 150 users |

---

## 8. Version Compatibility Matrix

| Component | Min Version | Recommended | Max Version |
|---|---|---|---|
| Python | 3.10 | 3.11 | 3.13 |
| PostgreSQL | 13 | 15 | Latest |
| Node.js | 18 LTS | 20 LTS | 21 |
| Docker | 20.10 | 24+ | Latest |
| FastAPI | 0.100 | 0.104 | Latest |
| React | 18.0 | 18.2 | 19 |

---

## 9. Tech Stack Comparison (Alternatives)

| Aspect | Our Choice | Alternative 1 | Alternative 2 | Why Ours |
|---|---|---|---|---|
| Backend | FastAPI | Django | Express.js | Async, fast, auto-docs |
| Frontend | React+TS | Vue+TS | Svelte | Largest ecosystem, easier hire |
| Database | Postgres | MongoDB | MySQL | Relational, pgvector, mature |
| Crawling | Crawl4AI | Selenium | Scrapy | Python, lightweight, Docker |
| LLM | Gemini Flash | GPT-4 | Claude | Cheapest, fast, good for tasks |
| Cache | Redis | Memcached | DynamoDB | Flexible, pub/sub, TTL |
| Job Queue | Celery | Bull.js | AWS SQS | Mature, Python-native, scheduled |

---

## 10. Tech Stack Risk Assessment

### 10.1 Low Risk

✅ **PostgreSQL:** Proven in production, stable, large community  
✅ **FastAPI:** Growing ecosystem, backed by Starlette, well-maintained  
✅ **React:** Industry standard, largest job market  
✅ **Docker:** De facto standard for containerization  

### 10.2 Medium Risk

⚠️ **Gemini 2.5 Flash:** Newer model, API may change (unlikely but possible)  
⚠️ **Crawl4AI:** Younger library, less battle-tested (fallback to LightPanda if fails)  
⚠️ **pgvector:** Specific to Postgres, vendor lock-in (acceptable for MVP)  

### 10.3 Mitigation Strategies

1. **Gemini:** Implement abstraction layer (LLM service) so switching is easy
2. **Crawl4AI:** Graceful degradation to cache/synthetic data if fails
3. **pgvector:** Later migrate to Pinecone if scaling to millions of documents
4. **Celery:** No vendor lock-in (can switch to Bull.js if needed)

---

## 11. Learning Resources

### Backend (FastAPI)
- https://fastapi.tiangolo.com/ (official docs)
- https://sqlalchemy.org/ (SQLAlchemy docs)
- https://docs.celeryproject.io/ (Celery docs)

### Frontend (React + Next.js)
- https://nextjs.org/docs (Next.js docs)
- https://react.dev (React docs)
- https://tailwindcss.com/docs (Tailwind docs)

### Database (PostgreSQL)
- https://www.postgresql.org/docs/ (Postgres docs)
- https://github.com/pgvector/pgvector (pgvector)

### External APIs
- https://ai.google.dev/ (Gemini API)
- https://crawl4ai.github.io/ (Crawl4AI)

---

**Document Version:** 1.0  
**Status:** Ready for Development  
**Last Updated:** April 2026  
**Next Step:** Start backend setup with Docker