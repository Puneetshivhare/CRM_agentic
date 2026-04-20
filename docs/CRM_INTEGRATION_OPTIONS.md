# CRM Integration Options

This document outlines the current CRM system and future integration possibilities.

---

## Current System: Custom Agentic CRM

**Status**: ✅ MVP Complete (All 8 tasks implemented)

### Architecture
- **Database**: Supabase PostgreSQL (Snowflake schema with dimensions + facts)
- **Models**: Custom SQLAlchemy ORM models
- **Agents**: Autonomous AI agents for research, enrichment, monitoring
- **API**: FastAPI REST endpoints for prospects, documents, enrichment

### Key Features
- Prospect management (CRUD, bulk import)
- Web research + data extraction (via Gemini 2.5 Flash)
- Automatic enrichment (fills prospect/company fields)
- File upload (PDF/CSV processing)
- Change monitoring (detects funding, hiring, announcements)
- Vector storage (Chroma) for future RAG

### Database Schema

**Dimension Tables** (slowly changing)
- `dim_prospects` — Individual sales prospects
- `dim_companies` — Company profiles
- `dim_documents` — Uploaded files (PDFs, CSVs) for RAG

**Fact Tables** (immutable audit logs)
- `fact_agent_executions` — Every agent run (Research, Enrichment, Monitoring)
- `fact_enrichment_events` — Field-level change history (per-field confidence + source)
- `fact_interactions` — Email opens, clicks, calls (future)
- `fact_enrichment_rules` — Workflow definitions (future)

### Agents

| Agent | Purpose | Trigger | Output |
|-------|---------|---------|--------|
| **ResearchAgent** | Crawl websites + extract structured data | Manual via API | Company/prospect data |
| **EnrichmentAgent** | Map extracted data to CRM schema, log changes | After Research | Updated records + audit trail |
| **MonitoringAgent** | Detect changes in monitored companies | Daily (or manual) | Change alerts + execution logs |

---

## Future: HubSpot Open-Source CRM Integration

**Status**: 🔮 Not Started (Phase 2+)

### Why HubSpot OSS?
- ✅ Full-featured CRM (contacts, deals, pipelines, activities)
- ✅ Apache 2.0 license (unlimited commercial use)
- ✅ Extensible (custom fields, workflows, integrations)
- ✅ Industry standard (familiar to sales teams)
- ⚠️ Larger codebase (more migration effort)

### Integration Approach

#### Option A: Replace Custom CRM (Big Bang)
- Migrate prospect data → HubSpot Contacts
- Migrate companies → HubSpot Companies
- Map agents to HubSpot workflows
- Replace API routes with HubSpot SDK calls

**Effort**: High | **Risk**: High | **Benefit**: Complete HubSpot feature set

#### Option B: Keep Custom CRM + Bidirectional Sync (Hybrid)
- Keep current Agentic CRM as autonomous research layer
- Sync research results → HubSpot (one-way, enrichment only)
- Sales team works in HubSpot (familiar interface)
- Agents power the enrichment engine

**Effort**: Medium | **Risk**: Low | **Benefit**: Best of both worlds

#### Option C: Custom CRM + HubSpot Read-Only (Current Path)
- Keep Agentic CRM as primary system
- Optional HubSpot sync for reporting (read-only)
- Sales team uses custom UI (builds domain knowledge)

**Effort**: Low | **Risk**: Lowest | **Benefit**: Full control + custom AI agents

### Migration Checklist (If Needed)

```
[ ] Analyze HubSpot OSS data model
[ ] Map custom Prospect → HubSpot Contact + custom fields
[ ] Map custom Company → HubSpot Company
[ ] Design enrichment workflow in HubSpot (vs agents)
[ ] Create data migration script (PostgreSQL → HubSpot)
[ ] Build HubSpot API integration layer
[ ] Rewrite agents to update HubSpot (vs custom DB)
[ ] Build HubSpot webhook handlers
[ ] Test contact + deal workflows
[ ] Train sales team on new interface
```

---

## Database Strategy

### Current: Supabase PostgreSQL
- ✅ Hosted PostgreSQL (no ops overhead)
- ✅ Vector support (pgvector extension available)
- ✅ Real-time subscriptions (for future live dashboards)
- ✅ Auth integration (JWT + Supabase Auth)
- ✅ Affordable free tier + pay-as-you-go

### Legacy: Local PostgreSQL
- Available in `docker-compose.yml` (commented out)
- Useful for development without Supabase account
- To revert: uncomment postgres service + update `.env`

### Why Not Both?
- Supabase is hosted PostgreSQL (not a separate tool)
- You already use PostgreSQL locally for other projects
- Supabase avoids port collision + local disk management

---

## Vector Store Strategy

### Current: Chroma (Open Source)
- ✅ Free, open source (can self-host or use docker)
- ✅ Native Python client (simple API)
- ✅ Persistent storage (local or remote)
- ✅ Semantic search for document chunks
- ⏳ Phase 2 feature (MVP stores documents, no embeddings yet)

### Future Phase 2: Embedding Pipeline
```
Workflow:
  1. Upload PDF/CSV → stored in dim_documents
  2. Chunk large documents (handled by file_service.py)
  3. Generate embeddings via Gemini or OpenAI
  4. Store embeddings in Chroma
  5. RAG search: semantic search over documents
  6. Retrieve top-K chunks → feed to Gemini for synthesis
```

### Embedding Options
| Option | Cost | Control | Integration |
|--------|------|---------|-------------|
| **Gemini Embeddings** | Free (in API free tier) | Medium | Native Google |
| **OpenAI Ada v2** | $0.02/1K tokens | High | Industry standard |
| **Hugging Face Transformers** | Free (local) | Full | Open source |
| **Chroma Defaults** | Free | Low | Built-in |

---

## Switching Back to Local Postgres

If you ever need local Postgres instead of Supabase:

### Step 1: Uncomment `.env`
```bash
# Comment out:
# DATABASE_URL=postgresql://postgres:...@supabase.co...

# Uncomment:
DATABASE_URL=postgresql://crm_user:crm_password@localhost:5433/agentic_crm
DB_PASSWORD=crm_password
```

### Step 2: Uncomment `docker-compose.yml`
```yaml
# Uncomment postgres service (lines ~20-37)
# Uncomment postgres_data volume (bottom)
# In backend service, change depends_on back to postgres
# Update backend DATABASE_URL environment variable
```

### Step 3: Update `app/database.py` & `app/config.py`
- Uncomment legacy engine in database.py
- Comments are already in place for easy reverting

### Step 4: Restart
```bash
docker-compose down
docker-compose up --build
```

---

## Summary

| Aspect | Current | Future Option |
|--------|---------|----------------|
| **CRM** | Custom Agentic CRM | HubSpot OSS (hybrid or full) |
| **Database** | Supabase PostgreSQL | Local or Managed PostgreSQL |
| **Vector Store** | Chroma | Same or Weaviate/Qdrant |
| **Auth** | JWT (custom) | Supabase Auth or HubSpot OAuth |
| **Agents** | Custom (Research, Enrichment, Monitoring) | Same or HubSpot Workflows |

Choose **Option B (Hybrid)** for best flexibility: keep the autonomous AI agents + add HubSpot for sales team workflows.
