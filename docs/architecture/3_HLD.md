# High Level Design (HLD) - Agentic CRM System

**Purpose:** System-level architecture. How components interact, data flow, agent orchestration patterns, memory architecture, and integration points.

**Audience:** Architects, lead engineers, AI/agent specialists  
**Version:** 1.0 MVP  
**Date:** April 2026

---

## 1. System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            FRONTEND (Next.js)                               │
│  Prospect Table | Skills | Rules | Monitoring | Codex Dashboard | Auth      │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                        HTTP API / WebSocket
                                    │
┌───────────────────────────────────▼─────────────────────────────────────────┐
│                      BACKEND API (FastAPI/Python)                           │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                     AGENT LAYER (Core Business Logic)                │   │
│  │  ┌────────┬──────────┬───────────┬──────────┬──────────┐            │   │
│  │  │Research│Enrichment│Monitoring │Outreach  │Analytics │ Orchestr. │   │
│  │  │ Agent  │  Agent   │  Agent    │  Agent   │  Agent   │  (Smart)  │   │
│  │  └────────┴──────────┴───────────┴──────────┴──────────┘            │   │
│  │                          ▲                                           │   │
│  │                    Memory Interface                                  │   │
│  │                          │                                           │   │
│  ├──────────────────────────┼──────────────────────────────────────────┤   │
│  │ SERVICES LAYER           │                                          │   │
│  │  ├─ Crawl Service (Crawl4AI + LightPanda)                          │   │
│  │  ├─ Gemini Service (API calls + prompt templates + caching)        │   │
│  │  ├─ RAG Service (document embeddings + semantic search)            │   │
│  │  ├─ Skill Executor (parse + run user skills)                       │   │
│  │  ├─ Rule Evaluator (trigger + data + workflow rules)               │   │
│  │  └─ Job Queue Service (Celery: async tasks)                        │   │
│  │                          │                                           │   │
│  ├──────────────────────────┼──────────────────────────────────────────┤   │
│  │ MEMORY LAYER             │                                          │   │
│  │  ├─ Flat Memory (Postgres table: memory_store)                     │   │
│  │  ├─ Hierarchical Memory (prospect/company/user context layers)     │   │
│  │  ├─ Vector Memory (embeddings + semantic search)                    │   │
│  │  └─ Memory Interface (unified access)                               │   │
│  │                          │                                           │   │
│  ├──────────────────────────┼──────────────────────────────────────────┤   │
│  │ CODEX LAYER (Observability + Improvement)                           │   │
│  │  ├─ Decision Logger (all agent actions)                             │   │
│  │  ├─ Test Generator (auto-generate test cases)                       │   │
│  │  ├─ Prompt Optimizer (track Gemini performance)                     │   │
│  │  ├─ Metrics Tracker (tokens, latency, success rate)                 │   │
│  │  └─ Dashboard Data (aggregate for UI)                               │   │
│  │                          │                                           │   │
│  └──────────────────────────┼──────────────────────────────────────────┘   │
│                             │                                               │
└─────────────────────────────┼───────────────────────────────────────────────┘
                              │
                    Database + Cache Layer
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼──────┐     ┌────────▼────────┐   ┌───────▼──────────┐
│  Postgres    │     │  Supabase Auth  │   │  Vector DB       │
│  (Snowflake  │     │  (JWT tokens)   │   │  (Embeddings +   │
│   Schema)    │     │                 │   │   Semantic       │
│              │     │                 │   │   Search)        │
│ fact_*       │     │ auth_users      │   │                  │
│ dim_*        │     │ (isolated)      │   │ Integrated into  │
│ memory_*     │     │                 │   │ Postgres         │
└──────────────┘     └─────────────────┘   └──────────────────┘

External Services:
├─ Crawl4AI (web scraping)
├─ LightPanda (JS rendering)
├─ Gemini 2.5 Flash API (LLM)
└─ Gemini Embeddings API (vectorization)
```

---

## 2. Data Flow Diagrams

### 2.1 Single Prospect Enrichment Flow (MVP)

```
USER ACTION: Click "Enrich" on prospect "John at Acme Corp"
│
├─ FRONTEND
│  └─ POST /api/prospects/123/enrich
│     └─ triggers backend
│
├─ API ROUTER
│  └─ routes/enrichment.py::enrich_prospect_endpoint(prospect_id=123)
│     ├─ Validates prospect exists
│     ├─ Checks if already enriching (prevent duplicate)
│     └─ Queues async job + returns job_id
│
├─ JOB QUEUE (Celery)
│  └─ Creates job: enrich_prospect_job(prospect_id=123)
│
├─ ORCHESTRATOR (Smart Routing)
│  └─ orchestrator.orchestrate(task="enrich_prospect_123", agents=[research, enrichment])
│     ├─ Detects: sequential pattern (research → enrichment)
│     └─ Executes chain
│
├─ RESEARCH AGENT
│  ├─ memory.get_prospect_context(prospect_123)
│  │  └─ Returns: {name: "John", company_id: 456, title: "CTO"}
│  │
│  ├─ memory.get_company_context(company_456)
│  │  └─ Check if already researched (cache hit!)
│  │     └─ If hit: skip crawl, reuse findings
│  │     └─ If miss: proceed to crawl
│  │
│  ├─ crawl_service.crawl(company_domain="acme.com", prospect_name="John")
│  │  ├─ Crawl4AI fetches acme.com → LinkedIn John profile → news about Acme
│  │  └─ Returns: raw_crawl_output = {company: "Acme Corp", headcount: "150", funding: "Series C", ...}
│  │
│  ├─ gemini_service.extract_company_data(raw_crawl_output)
│  │  ├─ Prompt: "Extract structured data from crawl: ..."
│  │  └─ Returns: {company_name: "Acme Corp", headcount: 150, funding: "Series C", confidence: 0.95}
│  │
│  ├─ memory.set("company:456", {headcount: 150, funding: "Series C", ...})
│  │  └─ Cache for future agents
│  │
│  └─ codex.log_agent_decision(
│      agent="ResearchAgent",
│      decision="Found Acme Corp: 150 headcount, Series C funded",
│      tokens_used=450
│     )
│
├─ ENRICHMENT AGENT
│  ├─ memory.get("company:456")
│  │  └─ Returns cached findings
│  │
│  ├─ gemini_service.map_to_schema(findings, ProspectSchema)
│  │  ├─ Prompt: "Map these findings to CRM schema: ..."
│  │  └─ Returns: {company_name: "Acme Corp", company_size: "150", funding: "Series C"}
│  │
│  ├─ database.update(Prospect, prospect_id=123, {...mapped_data...})
│  │  └─ Prospect now enriched in DB
│  │
│  ├─ memory.set("prospect:123:enrichment_event", {timestamp: "...", fields_filled: [...]})
│  │  └─ Cache enrichment history
│  │
│  └─ codex.log_agent_decision(
│      agent="EnrichmentAgent",
│      decision="Filled fields: company_name, company_size, funding",
│      tokens_used=200
│     )
│
├─ CODEX DASHBOARD
│  └─ Captures all logs + metrics
│     ├─ Decision logs: what each agent did
│     ├─ Token usage: 450 + 200 = 650 total
│     ├─ Latency: 25 seconds (research + enrichment)
│     └─ Memory hits: 1 (company already researched)
│
└─ FRONTEND
   └─ Display: Prospect enriched ✓ (company, size, funding filled)
      └─ Show codex summary: "Enriched in 25s, reused cached research"
```

### 2.2 Bulk CSV Enrichment Flow

```
USER ACTION: Upload "prospects.csv" with 100 prospects
│
├─ FRONTEND
│  └─ POST /api/prospects/bulk-enrich (file upload)
│     ├─ Parse CSV
│     └─ Send to backend
│
├─ API ROUTER
│  └─ routes/enrichment.py::bulk_enrich(file_data)
│     ├─ Store file in Documents table
│     ├─ Create 100 prospect records
│     └─ Queue bulk_enrich_job(prospect_ids=[...])
│
├─ JOB QUEUE
│  └─ bulk_enrich_job spawns N parallel tasks
│     └─ For prospects 1-100, call enrich_prospect (async)
│
├─ ORCHESTRATOR
│  └─ Detects: parallel pattern (all researches simultaneous)
│     ├─ Creates 4-5 Research Agent workers
│     └─ Each handles 20-25 prospects in parallel
│
├─ RESEARCH AGENT WORKERS (Parallel)
│  ├─ Worker 1: research prospects 1-25
│  │  ├─ Check memory for cached companies
│  │  ├─ If cache hit: reuse (saves 75% of crawls!)
│  │  ├─ If cache miss: crawl
│  │  └─ Store findings in memory
│  │
│  ├─ Worker 2-5: same pattern
│  │
│  └─ (All workers share same memory—no duplicate research)
│
├─ ENRICHMENT AGENTS (After research complete)
│  └─ Parallel enrichment agents map all 100 findings to schema
│
├─ MONITORING (Optional)
│  └─ After enrichment, trigger monitoring on all 100 companies
│
├─ PROGRESS TRACKING
│  └─ Job queue reports: "75/100 enriched, 15 in progress, 10 waiting..."
│     └─ Frontend shows progress bar
│
└─ CODEX METRICS
   ├─ Token usage: ~50K tokens (100 prospects * 450 avg per research + enrichment)
   ├─ Duration: 5-10 minutes (parallel)
   ├─ Memory reuse: if 30 unique companies, saved 3 crawls × 2K tokens each = 6K tokens!
   └─ Cost: ~$0.15 (Gemini Flash pricing)
```

### 2.3 Monitoring & Change Detection Flow

```
SCHEDULED JOB: Every morning at 8 AM
│
├─ MONITORING AGENT (scheduled trigger)
│  └─ monitoring.monitor_all_watch_list()
│     ├─ Fetch all prospects marked "watch"
│     └─ For each watched company, detect changes
│
├─ FOR EACH COMPANY
│  ├─ memory.get("company:456:monitoring_state")
│  │  └─ Returns previous research findings (from last run)
│  │
│  ├─ crawl_service.crawl(company_domain, recent=True)
│  │  └─ Crawl fresh data (LinkedIn job postings, news, etc.)
│  │
│  ├─ gemini_service.detect_changes(
│       old_findings=previous_state,
│       new_findings=fresh_crawl
│      )
│     └─ Returns: [
│          ChangeEvent(type="hiring", detail="VP Sales hired"),
│          ChangeEvent(type="news", detail="Series B funding announced"),
│          ...
│        ]
│
│  ├─ FOR EACH CHANGE
│  │  ├─ rule_evaluator.evaluate_against_rules(change)
│  │  │  └─ Check: does this change match any user-defined rules?
│  │  │     └─ Rule 1: "IF funding_stage = Series B THEN mark hot"
│  │  │     └─ Rule 2: "IF hires VP sales THEN send alert"
│  │  │
│  │  ├─ IF rules match:
│  │  │  ├─ Create AlertEvent
│  │  │  ├─ Update prospect priority
│  │  │  └─ (Optional) Send notification to user
│  │  │
│  │  └─ Store change in fact_enrichment_events + memory
│  │
│  └─ memory.set("company:456:monitoring_state", new_findings)
│     └─ Update baseline for next run
│
├─ AGGREGATION
│  └─ Collect all alerts from all companies
│     └─ Example output: [
│          {prospect: "John at Acme", change: "Series B funded", priority: "hot"},
│          {prospect: "Jane at Bolt", change: "VP Sales hired", priority: "medium"},
│          ...
│        ]
│
├─ NOTIFICATIONS
│  ├─ Email user: "3 of your watched companies have updates"
│  └─ (Future) Slack integration: post alerts to #sales channel
│
└─ CODEX
   └─ Log all monitoring decisions + changes detected
      └─ Used later for: "Which rule fires most often?" → optimize
```

---

## 3. Agent Orchestration Strategy

### 3.1 Decision Matrix: When to Use Which Pattern

```
Task Type                    Pattern         Why?
────────────────────────────────────────────────────────────
Single prospect enrich       Sequential      Simple, one prospect, minimal parallelization
Bulk (100+ prospects)        Parallel        Leverage N agents, speed up 5x
Complex skill execution      Hierarchical    Manager agent routes by prospect type
Change monitoring (many)     Parallel+Async  All companies checked simultaneously
Custom workflow (all steps)  Contextual      Agent decides based on task complexity
```

### 3.2 Sequential Pattern

```
Research Agent → (results) → Enrichment Agent → (results) → Monitoring Agent
                                                   (optional)
```

**When:**
- Single prospect
- Results depend on prior steps (research must complete before enrichment)
- Fast feedback loop (agent wants result before moving on)

**Latency:** ~30 seconds (research: 15s + enrichment: 10s + monitoring: 5s)

### 3.3 Parallel Pattern

```
      ┌─ Research Agent (batch 1)
      ├─ Research Agent (batch 2)
      ├─ Research Agent (batch 3)
      └─ Research Agent (batch 4)
           (all run simultaneously)
                   │
            (all complete)
                   │
      ┌─ Enrichment Agent (batch 1)
      ├─ Enrichment Agent (batch 2)
      ├─ Enrichment Agent (batch 3)
      └─ Enrichment Agent (batch 4)
           (all run simultaneously)
```

**When:**
- Bulk task (100+ prospects)
- Steps are independent (each Research Agent doesn't depend on others)
- Speed is priority

**Latency:** ~5 minutes for 100 prospects (vs. 50 minutes sequential)
**Memory reuse:** High (if 30 unique companies, cached after first worker researches them)

### 3.4 Hierarchical Pattern

```
                    Orchestrator (Manager)
                    │ Parses skill definition
                    │ Decides routing strategy
                    │ Delegates to workers
                    ├─────────────────┬──────────────────┬─────────────┐
                    │                 │                  │             │
           ┌────────▼─────┐  ┌───────▼────────┐  ┌─────▼──────┐  ┌───▼────────┐
           │ Research Ag. │  │ Research Ag.   │  │ Research   │  │ Research   │
           │  (Worker A)  │  │  (Worker B)    │  │ Agent      │  │ Agent      │
           │              │  │                │  │ (Worker D) │  │ (Worker E) │
           │ Handles:     │  │ Handles:       │  │            │  │            │
           │ Prospects    │  │ Prospects      │  │ Prospects  │  │ Prospects  │
           │ 1-20         │  │ 21-40          │  │ 41-60      │  │ 61-80      │
           └──────────────┘  └────────────────┘  └────────────┘  └────────────┘
                    │                 │                  │             │
                    └─────────────────┬──────────────────┴─────────────┘
                                      │ (merge results)
                           Enrichment Agents (same pattern)
                                      │
                                Manager Aggregates
                                      │
                    Final: All 80 prospects enriched
```

**When:**
- Complex, multi-step workflow (research → enrich → qualify → outreach)
- Task has multiple sub-tasks that can run in parallel
- Need error handling at each stage

**Latency:** Optimized (parallel where possible, sequential where needed)

---

## 4. Memory Architecture Deep Dive

### 4.1 Memory Layers Visualization

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        AGENT QUERIES MEMORY                             │
│  memory.get_prospect_context(prospect_id) ← calls unified interface     │
└────────────────────────┬────────────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
   ┌────────────┐  ┌─────────────┐  ┌──────────────────┐
   │ FLAT MEM.  │  │ HIERARCHICAL│  │ VECTOR MEM.      │
   │            │  │ MEMORY      │  │                  │
   │ KV Store   │  │             │  │ Embeddings +     │
   │ Postgres   │  │ Prospect    │  │ Semantic Search  │
   │ memory_*   │  │ ├─ name     │  │                  │
   │            │  │ ├─ role     │  │ When agent       │
   │ Key: str   │  │ └─ hist.    │  │ asks: "similar   │
   │ Value:     │  │             │  │ companies to     │
   │ {data}     │  │ Company     │  │ Acme?"           │
   │            │  │ ├─ name     │  │                  │
   │ Fast O(1)  │  │ ├─ size     │  │ Returns ranked   │
   │ lookup     │  │ └─ funding  │  │ list with scores │
   │            │  │             │  │                  │
   │ Use: cache │  │ User        │  │ Postgres vector  │
   │ known      │  │ ├─ prefs    │  │ column (pgvector)│
   │ values     │  │ └─ skills   │  │                  │
   │            │  │             │  │                  │
   │            │  │ Good for:   │  │ Good for:        │
   │            │  │ organized   │  │ pattern matching,│
   │            │  │ context,    │  │ similarity, no   │
   │            │  │ reduces     │  │ duplicate        │
   │            │  │ fetch calls │  │ research         │
   └────────────┘  └─────────────┘  └──────────────────┘
        │                │                │
        └────────────────┼────────────────┘
                         │
                    ┌────▼────┐
                    │ POSTGRES │
                    │ All layers│
                    │ stored in │
                    │ single DB │
                    └──────────┘
```

### 4.2 Memory Reuse Example

```
Timeline:
──────────────────────────────────────────────────────────────────

T1: Research Agent researches "Acme Corp"
    ├─ Crawl: acme.com → LinkedIn → news
    ├─ Result: {name: "Acme Corp", headcount: 150, funding: "Series C"}
    └─ Memory write:
        ├─ Flat: memory["company:acme"] = {...}
        ├─ Hierarchical: memory["company:456"]["size"] = 150
        └─ Vector: embeddings["SaaS Series C 150 employees"]

T2: Enrichment Agent needs company info for prospect "John at Acme"
    ├─ Query memory: memory.get_company_context("acme")
    ├─ Result: CACHE HIT! (150ms instead of 20s crawl)
    ├─ Reuses: company name, size, funding
    └─ Update prospect with this data

T3: Monitoring Agent checks for hiring changes at Acme
    ├─ Query memory: memory.get("company:acme:monitoring_state")
    ├─ Previous state: {size: 150, hires: [Tom, Jane]}
    ├─ New crawl: {size: 155, hires: [Tom, Jane, Mike]}
    ├─ Detect change: "New hire: Mike"
    ├─ Evaluate rule: "IF new hire in sales THEN alert"
    ├─ Result: Create alert
    └─ Update memory: monitoring_state = new_state

T4: Analytics Agent summarizes interactions with Acme
    ├─ Query memory: memory.semantic_search("Acme company context")
    ├─ Results: all cached Acme findings
    ├─ No duplicate research needed!
    ├─ RAG over documents + memory = rich context
    └─ Summarize all interactions

Memory Reuse Statistics:
├─ T1 Research Agent: 450 tokens (first research)
├─ T2 Enrichment Agent: 200 tokens (memory reuse, no crawl)
├─ T3 Monitoring Agent: 300 tokens (new crawl, small diff detection)
├─ T4 Analytics Agent: 150 tokens (memory + RAG, minimal new work)
└─ TOTAL: 1,100 tokens saved vs. if all agents researched independently: 3,200 tokens
         → 66% cost reduction!
```

---

## 5. Service Layer Overview

### 5.1 Crawl Service (Crawl4AI + LightPanda)
```
crawl_service.crawl(domain: str, prospect_name: str = None) → CrawlResult
│
├─ Input: "acme.com", "John Smith"
├─ Step 1: Fetch acme.com with LightPanda (JS rendering)
├─ Step 2: Extract text + structure (Crawl4AI)
├─ Step 3: Search for prospect name mentions (name matching)
├─ Step 4: Extract key entities (company name, headcount, funding, etc.)
├─ Step 5: Cache result in Documents table (for RAG later)
└─ Output: {
     url: "acme.com",
     title: "Acme Corp",
     text: "...",
     structured_data: {...},
     parsed_entities: {...}
   }
```

### 5.2 Gemini Service (API + Prompt Templates + Caching)
```
gemini_service.call(
    prompt_template: str,  # e.g., "research_extraction"
    input_data: dict,      # e.g., {raw_crawl: "..."}
    model: str = "gemini-2.5-flash"
) → str

Within the service:
├─ Lookup prompt template from cache
├─ Format template with input_data
├─ Call Gemini API
├─ Log decision (for Codex)
├─ Cache result + tokens used
└─ Return structured output
```

### 5.3 RAG Service (Document Embeddings + Search)
```
rag_service.ingest_document(file_path: str) → None
├─ Read PDF/CSV
├─ Extract text/tables
├─ Chunk into 500-token chunks
├─ Generate embeddings (Gemini Embeddings API)
└─ Store in Postgres vector column

rag_service.search(query: str, top_k: int = 5) → List[Document]
├─ Embed query (Gemini Embeddings)
├─ Vector similarity search (Postgres pgvector)
└─ Return top K matching documents (with relevance scores)
```

### 5.4 Skill Executor (Parse + Execute User Skills)
```
skill_executor.execute(skill_id: str, context: dict) → Result
│
├─ Load skill definition from DB
├─ Parse skill JSON: {
     name: "Research SaaS with Series B",
     type: "research",
     criteria: {industry: "SaaS", funding: "Series B"},
     depth: "deep"
   }
├─ Route to appropriate agent (Research Agent for "research" type)
├─ Pass context (prospect/company data)
├─ Agent executes with skill constraints
└─ Return result
```

### 5.5 Rule Evaluator (Trigger + Data + Workflow Rules)
```
rule_evaluator.evaluate(rule_id: str, context: dict) → bool
│
├─ Load rule definition: {
     type: "trigger",
     condition: "IF funding_stage = 'Series B'",
     action: "add_to_hot_list"
   }
├─ Extract context variables (prospectdata, company data)
├─ Evaluate condition (boolean logic)
├─ IF true: execute action
└─ Return boolean (rule matched or not)
```

---

## 6. Database Architecture (Snowflake Schema)

### 6.1 Schema Overview

```
DIMENSIONS (Slowly Changing Dimensions):
├─ dim_prospects: people records
│  └─ prospect_id (PK), name, email, title, company_id (FK), created_at, updated_at
│
├─ dim_companies: organization records
│  └─ company_id (PK), domain, name, headcount, funding_stage, headquarters, created_at
│
├─ dim_documents: uploaded PDFs, CSVs, emails, transcripts
│  └─ document_id (PK), file_path, document_type (PDF/CSV/transcript), created_at
│
├─ dim_skills: user-defined workflows
│  └─ skill_id (PK), user_id (FK), skill_json, created_at, updated_at
│
└─ dim_rules: user-defined logic
   └─ rule_id (PK), user_id (FK), rule_json, created_at, updated_at

FACTS (Immutable Event Logs):
├─ fact_interactions: emails, calls, meetings
│  └─ interaction_id (PK), prospect_id (FK), type, timestamp, content, created_at
│
├─ fact_enrichment_events: audit trail of what data was added
│  └─ event_id (PK), prospect_id (FK), field, old_value, new_value, agent_id, timestamp
│
└─ fact_agent_executions: every agent run
   └─ execution_id (PK), agent_type, task_id, result, tokens_used, latency_ms, created_at

MEMORY (Key-Value Store):
└─ memory_store: {key: str, value: json, ttl: timestamp, created_at}
   └─ Used for flat memory (fast lookup), hierarchical context, recent results

AUTH (Isolated):
└─ auth_users: email, password_hash, created_at
   └─ NO FOREIGN KEYS to other tables (by design)
```

### 6.2 Why Snowflake Schema?

| Aspect | Benefit |
|---|---|
| **Separation of concerns** | Dimensions slow-change (prospects), facts are immutable (events) |
| **OLTP + OLAP** | CRM queries (fast reads) + analytics queries (aggregations) |
| **Scalability** | Can add new dimension/fact tables without breaking existing code |
| **Audit trail** | fact_enrichment_events + fact_agent_executions = full history |
| **Normalization** | No data duplication (prospect → company via FK) |

---

## 7. Integration Points (MVP → Future)

### 7.1 MVP (In Scope)
- ✓ Supabase (Postgres + Auth)
- ✓ Gemini 2.5 Flash (LLM)
- ✓ Crawl4AI + LightPanda (web scraping)
- ✓ Docker (local deployment)

### 7.2 Phase 2 (v1.1, Planned)
- ☐ Email (Gmail/Outlook) - auto-log emails, extract context
- ☐ Calendar (Google Calendar) - pre-meeting research
- ☐ Slack webhooks - send alerts to sales channel

### 7.3 Future (v1.2+)
- ☐ Jira integration - link prospects to tickets
- ☐ Salesforce sync - bidirectional data sync
- ☐ Zapier - trigger workflows from external tools

**See Future Integration Plan document for details.**

---

## 8. Performance & Scalability Targets

### 8.1 MVP Performance SLAs

| Metric | Target | How |
|---|---|---|
| Single prospect enrich | <30s | Crawl (15s) + Gemini (10s) + enrich (5s) |
| Bulk 100 prospects | <5 min | Parallel agents + memory reuse |
| Prospect search | <500ms | Indexed DB query |
| Monitor 1000 companies | <30 min nightly | Async job queue + parallel workers |
| Memory lookup | <50ms | Postgres indexed KV table |

### 8.2 Scaling to Enterprise (Future)

**Bottleneck 1: Crawl4AI throughput**
- Solution: Crawl queue with rate limiting (avoid blocking target websites)

**Bottleneck 2: Gemini API cost**
- Solution: Prompt caching (Gemini 2.5 feature), reuse cached results, optimize prompts

**Bottleneck 3: Memory lookup at scale**
- Solution: Redis cache layer (short-term), pgvector for similarity queries (no full table scan)

**Bottleneck 4: Document RAG at scale (100K+ documents)**
- Solution: Separate vector DB (Pinecone/Weaviate), batch embeddings, hierarchical search

---

## 9. Security Architecture

### 9.1 Data Isolation
```
┌─────────────────────────────┐
│ User A                      │
├─────────────────────────────┤
│ Prospects, Companies        │
│ Skills, Rules               │
│ (via user_id in queries)    │
└─────────────────────────────┘

┌─────────────────────────────┐
│ User B                      │
├─────────────────────────────┤
│ Own Prospects, Companies    │
│ Own Skills, Rules           │
│ (via user_id in queries)    │
└─────────────────────────────┘

* Auth table (isolated): email, password_hash
* No FK from auth to other tables
* All queries filtered by user_id (row-level security)
```

### 9.2 API Security
```
┌──────────────────────┐
│ Request              │
├──────────────────────┤
│ JWT token (Supabase) │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Middleware: auth.py          │
├──────────────────────────────┤
│ 1. Validate JWT              │
│ 2. Extract user_id           │
│ 3. Pass to route handler     │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Route Handler                │
├──────────────────────────────┤
│ All DB queries filtered by   │
│ WHERE user_id = {extracted}  │
└──────────────────────────────┘
```

### 9.3 Sensitive Data (Environment Variables)
```
.env (never committed):
├─ SUPABASE_URL=https://...
├─ SUPABASE_KEY=...
├─ GEMINI_API_KEY=...
└─ DATABASE_URL=postgresql://...

Docker secrets (production):
├─ /run/secrets/gemini_key
└─ /run/secrets/db_password
```

---

## 10. Error Handling & Resilience

### 10.1 Agent Failures
```
Agent Task Execution:
├─ Try: await agent.run(task)
├─ Catch TemporaryError: retry (exponential backoff)
├─ Catch PermanentError: log + alert + queue for manual review
└─ Finally: log decision (success or failure)
```

### 10.2 Graceful Degradation
```
If Crawl4AI fails:
├─ Try: LightPanda fallback
├─ Try: Cached previous crawl
├─ Try: Ask Gemini to generate synthetic data (risky!)
└─ Last resort: Return error + alert user

If Gemini fails:
├─ Try: Retry (rate limit?)
├─ Try: Use cached previous extraction
└─ Last resort: Return partial result + alert

If Postgres fails:
├─ Try: Reconnect (connection pool recovery)
├─ Try: Use in-memory memory cache (temporary)
└─ Fail: System down (alert ops)
```

---

## 11. Deployment Architecture

### 11.1 Local Docker Setup (MVP)
```
docker-compose.yml:
├─ postgres:14 (data + memory)
├─ backend:py39 (FastAPI + agents)
└─ frontend:node18 (Next.js)

Host: WSL on Windows
Network: Docker bridge (services talk internally)
Volumes: ./data/postgres (persistent DB)
```

### 11.2 Future Cloud Deployment
```
┌─────────────────────────────────┐
│ Cloud Provider (AWS/GCP/Azure)  │
├─────────────────────────────────┤
│ ┌────────────────────────────┐  │
│ │ Frontend (Vercel/Netlify)  │  │
│ └────────────┬───────────────┘  │
│              │ API calls        │
│ ┌────────────▼───────────────┐  │
│ │ Backend (Cloud Run/Lambda) │  │
│ │ ├─ Agent layer             │  │
│ │ ├─ Memory layer            │  │
│ │ └─ Services layer          │  │
│ └────────────┬───────────────┘  │
│              │ Queries          │
│ ┌────────────▼───────────────┐  │
│ │ Supabase (Postgres + Auth) │  │
│ └────────────────────────────┘  │
│              │ Embeddings API   │
│              │ (Gemini)         │
│ ┌────────────▼───────────────┐  │
│ │ External APIs              │  │
│ │ ├─ Gemini                  │  │
│ │ ├─ Crawl4AI               │  │
│ │ └─ Email/Slack (future)    │  │
│ └────────────────────────────┘  │
└─────────────────────────────────┘
```

---

## 12. Next Steps

1. **Review this HLD** with team for feasibility
2. **Start LLD** (database schema, API endpoints, algorithm details)
3. **Setup Docker** (Postgres + backend scaffolding)
4. **Implement Research Agent first** (core workflow)
5. **Build memory layer** (foundation for agent autonomy)
6. **Add Enrichment Agent**
7. **Implement Codex** (observability + improvement loop)
8. **Test + optimize** based on Codex metrics

---

**Document Version:** 1.0  
**Status:** MVP Phase  
**Last Updated:** April 2026