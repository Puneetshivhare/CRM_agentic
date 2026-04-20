# Claude.md - Agentic CRM Codebase Architecture

**Purpose:** This document is the shared memory for all agents (Claude instances) working on this project. It describes the codebase structure, module responsibilities, agent types, orchestration patterns, and memory architecture. When spawning new agents or resuming work, reference this document first.

**Last Updated:** April 2026  
**Status:** MVP Phase

---

## 1. Project Structure Overview

```
agentic-crm/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app initialization
│   │   ├── config.py               # Environment config (Supabase URL, Gemini key, etc.)
│   │   ├── database.py             # Postgres connection + connection pool
│   │   ├── auth.py                 # JWT token validation
│   │   │
│   │   ├── agents/                 # Agent implementations (core business logic)
│   │   │   ├── __init__.py
│   │   │   ├── base_agent.py       # Base class for all agents
│   │   │   ├── research_agent.py   # Web crawl + enrichment logic
│   │   │   ├── enrichment_agent.py # Fill CRM fields via Gemini
│   │   │   ├── monitoring_agent.py # Watch for changes
│   │   │   ├── outreach_agent.py   # Email drafting + qualification
│   │   │   ├── analytics_agent.py  # RAG-based analysis
│   │   │   └── orchestrator.py     # Smart routing between agents
│   │   │
│   │   ├── memory/                 # Shared memory system (critical for autonomy)
│   │   │   ├── __init__.py
│   │   │   ├── memory_store.py     # Flat memory (simple KV store in Postgres)
│   │   │   ├── hierarchical_memory.py  # Prospect/Company/User context layers
│   │   │   ├── vector_memory.py    # Vector embeddings + semantic search
│   │   │   └── memory_interface.py # Unified interface for agents
│   │   │
│   │   ├── models/                 # Pydantic/SQLAlchemy models
│   │   │   ├── __init__.py
│   │   │   ├── prospect.py
│   │   │   ├── company.py
│   │   │   ├── interaction.py
│   │   │   ├── enrichment_event.py
│   │   │   ├── agent_execution.py
│   │   │   ├── document.py
│   │   │   ├── skill.py
│   │   │   └── rule.py
│   │   │
│   │   ├── routes/                 # API endpoints
│   │   │   ├── __init__.py
│   │   │   ├── prospects.py        # CRUD for prospects
│   │   │   ├── companies.py        # CRUD for companies
│   │   │   ├── enrichment.py       # Trigger research/enrichment
│   │   │   ├── monitoring.py       # Monitoring control
│   │   │   ├── skills.py           # User skill management
│   │   │   ├── rules.py            # Rules engine
│   │   │   ├── documents.py        # Upload/manage documents
│   │   │   ├── codex.py            # Codex dashboard data (logs, metrics)
│   │   │   └── agents.py           # Debug: view agent status
│   │   │
│   │   ├── services/               # Business logic (not API-specific)
│   │   │   ├── __init__.py
│   │   │   ├── crawl_service.py    # Crawl4AI wrapper + caching
│   │   │   ├── gemini_service.py   # Gemini API calls + prompt templates
│   │   │   ├── rag_service.py      # Document embeddings + semantic search
│   │   │   ├── skill_executor.py   # Run user-defined skills
│   │   │   ├── rule_evaluator.py   # Evaluate user-defined rules
│   │   │   └── job_queue.py        # Async task queue (Celery)
│   │   │
│   │   ├── codex/                  # Codex system (observability + improvement)
│   │   │   ├── __init__.py
│   │   │   ├── decision_logger.py  # Log all agent decisions
│   │   │   ├── test_generator.py   # Auto-generate test cases
│   │   │   ├── prompt_optimizer.py # Track Gemini prompt performance
│   │   │   ├── metrics_tracker.py  # Token usage, latency, success rates
│   │   │   └── dashboard_data.py   # Aggregate data for UI dashboard
│   │   │
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── logger.py
│   │       ├── constants.py
│   │       └── helpers.py
│   │
│   ├── migrations/                 # Alembic DB migrations
│   ├── tests/                      # Unit + integration tests
│   ├── requirements.txt            # Python dependencies
│   └── Dockerfile                  # Docker config for backend
│
├── frontend/
│   ├── app/
│   │   ├── (page)/
│   │   │   ├── page.tsx            # Home/dashboard
│   │   │   └── layout.tsx
│   │   ├── prospects/
│   │   │   ├── page.tsx            # Prospect table + actions
│   │   │   ├── [id]/
│   │   │   │   └── page.tsx        # Prospect detail + enrichment history
│   │   │   └── enrich/
│   │   │       └── page.tsx        # Bulk enrich page
│   │   ├── companies/
│   │   │   └── page.tsx
│   │   ├── monitoring/
│   │   │   └── page.tsx            # Watch list + alerts
│   │   ├── skills/
│   │   │   ├── page.tsx            # List + create skills
│   │   │   └── [id]/
│   │   │       └── page.tsx        # Edit skill
│   │   ├── rules/
│   │   │   ├── page.tsx            # Manage rules
│   │   │   └── [id]/
│   │   │       └── page.tsx        # Edit rule
│   │   ├── codex/
│   │   │   ├── page.tsx            # Main dashboard
│   │   │   ├── decision-logs/
│   │   │   │   └── page.tsx        # Agent decision history
│   │   │   ├── test-cases/
│   │   │   │   └── page.tsx        # Auto-generated test cases
│   │   │   ├── prompt-logs/
│   │   │   │   └── page.tsx        # Gemini prompt performance
│   │   │   └── metrics/
│   │   │       └── page.tsx        # Token tracking + performance
│   │   ├── api/                    # API route handlers (Next.js API routes)
│   │   │   ├── auth/
│   │   │   ├── prospects/
│   │   │   └── ... (proxy to backend)
│   │   ├── components/
│   │   │   ├── ProspectTable.tsx   # Dynamic table component
│   │   │   ├── EnrichmentStatus.tsx
│   │   │   ├── SkillBuilder.tsx    # Skill creation UI
│   │   │   ├── RuleBuilder.tsx     # Rule creation UI
│   │   │   ├── CodexDashboard.tsx
│   │   │   └── ...
│   │   ├── lib/
│   │   │   ├── api-client.ts       # Axios/fetch wrapper
│   │   │   ├── auth.ts             # Supabase auth helper
│   │   │   └── types.ts
│   │   └── hooks/
│   │       ├── useProspects.ts
│   │       ├── useEnrichment.ts
│   │       └── ...
│   ├── public/
│   ├── package.json
│   ├── tsconfig.json
│   └── next.config.js
│
├── docker-compose.yml              # Local Docker setup (Postgres + backend)
├── .env.example                    # Environment variables template
├── README.md
└── DEVELOPMENT.md                  # For developers

```

---

## 2. Core Agent Types & Responsibilities

All agents inherit from `BaseAgent` which provides:
- Memory access interface
- Error handling + retry logic
- Logging + decision capture
- Token tracking

### 2.1 Research Agent (`research_agent.py`)
**Responsibility:** Crawl web for prospect/company data, store findings in memory.

**Key Methods:**
```python
async def research_prospect(prospect_id: str, depth: str = "basic") -> ResearchResult
async def research_company(company_id: str) -> CompanyResearchResult
async def batch_research(prospect_ids: List[str]) -> List[ResearchResult]
```

**Process:**
1. Takes prospect/company identifier (name, domain, email)
2. Uses Crawl4AI + LightPanda to extract web data
3. Queries Gemini to structure/enrich findings (e.g., extract company funding, team size)
4. Stores raw crawl in Documents table + parsed data in memory
5. Logs decision: "Found 150 employees, Series C funded, HQ in SF"
6. Returns structured data for enrichment

**Memory Usage:**
- Stores in hierarchical memory: `prospect/{id}/research_findings`
- Also stores in vector memory with semantic tags: "funding", "headcount", "location"
- If similar company researched before, retrieves cached findings

**Triggers:**
- Manual: User clicks "Enrich" on prospect
- Bulk: CSV upload → job queue triggers async batch_research
- Monitoring: Scheduled daily for watch list

---

### 2.2 Enrichment Agent (`enrichment_agent.py`)
**Responsibility:** Take research findings, fill CRM record fields intelligently.

**Key Methods:**
```python
async def enrich_prospect(prospect_id: str, research_data: dict) -> EnrichmentResult
async def map_to_schema(research_data: dict, prospect_model: ProspectModel) -> dict
```

**Process:**
1. Receives raw research data from Research Agent
2. Uses Gemini to intelligently map findings to CRM schema (e.g., extracted text → company_name, role)
3. Handles conflicts (e.g., multiple funding amounts found → picks most recent)
4. Updates Prospect/Company records in database
5. Logs: "Filled: company_name, role, company_size from research data"

**Memory Usage:**
- Reads: Research Agent's findings from memory
- Writes: Enrichment decision log (what was filled, confidence scores)
- Reuses: If similar prospect exists, applies same field mappings

---

### 2.3 Monitoring Agent (`monitoring_agent.py`)
**Responsibility:** Watch for company changes (hiring, funding, news), trigger alerts.

**Key Methods:**
```python
async def monitor_prospect(prospect_id: str) -> List[AlertEvent]
async def detect_changes(company_id: str, previous_state: dict) -> List[ChangeEvent]
async def evaluate_against_rules(change: ChangeEvent, rules: List[Rule]) -> bool
```

**Process:**
1. Scheduled daily job: re-research each watched company
2. Compare new research to previous findings (stored in memory)
3. Detect changes: "New hire in sales", "Series B announced", "Tech stack changed"
4. Evaluate user-defined rules: "IF Series B THEN mark hot-list"
5. Create alerts + notifications
6. Log: "Detected: VP Sales hired at Acme Corp → triggered rule_hot_list_series_b"

**Memory Usage:**
- Reads: Previous company state (hierarchical: `company/{id}/monitoring_state`)
- Writes: Change events + alert history
- Vector search: "Have we seen similar hiring patterns before?"

---

### 2.4 Outreach Agent (`outreach_agent.py`)
**Responsibility:** Draft emails, qualify leads, suggest next steps based on prospect data.

**Key Methods:**
```python
async def draft_email(prospect_id: str, email_type: str = "cold_outreach") -> EmailDraft
async def qualify_prospect(prospect_id: str, qualification_skill: Skill) -> QualificationScore
async def suggest_next_step(prospect_id: str) -> NextStepSuggestion
```

**Process:**
1. User triggers outreach (manual or via skill)
2. Agent retrieves prospect + company context from memory
3. Uses Gemini + user-defined Outreach Skill to draft personalized email
4. Evaluates prospect fit (via qualification rules)
5. Suggests next step (call, demo, add to campaign)
6. Logs: "Drafted email for John at Acme (high fit score 0.85) → suggested follow-up call"

**Memory Usage:**
- Reads: All prospect context (company, role, past interactions)
- Reads: Outreach Skill definition + email templates
- Writes: Draft history + qualification scores
- Vector search: "Similar prospects → what worked?"

---

### 2.5 Analytics Agent (`analytics_agent.py`)
**Responsibility:** Summarize interactions, generate insights via RAG.

**Key Methods:**
```python
async def summarize_interactions(prospect_id: str, time_range: str) -> InteractionSummary
async def compare_prospects(prospect_ids: List[str], dimension: str) -> Comparison
async def analyze_via_rag(query: str, context: str) -> AnalysisResult
```

**Process:**
1. Takes query: "Summarize all emails with Company X in last 90 days"
2. Searches interactions (emails, calls, meeting notes) for Company X
3. Uses RAG to retrieve relevant documents (stored PDFs, call transcripts)
4. Queries Gemini: "Based on these interactions + documents, what's our status?"
5. Returns structured summary + key insights
6. Logs: "Analyzed 23 interactions → found pattern: prospect interested in product A"

**Memory Usage:**
- Reads: Interaction history + documents (via vector search)
- Writes: Analysis results + insights
- Updates: Memory with new learnings (e.g., "Company X uses Salesforce")

---

### 2.6 Orchestrator (`orchestrator.py`)
**Responsibility:** Smart routing—decide how agents collaborate (sequential, parallel, hierarchical).

**Key Methods:**
```python
async def orchestrate(task: Task, agents: List[Agent]) -> Result
async def route_sequential(agents: List[Agent], task: Task) -> Result
async def route_parallel(agents: List[Agent], task: Task) -> Result
async def route_hierarchical(manager: Agent, workers: List[Agent], task: Task) -> Result
```

**Process:**
1. Task comes in: "Enrich and qualify 50 prospects"
2. Orchestrator analyzes task complexity
3. Selects routing:
   - **Sequential:** Research → Enrichment → Qualification (step-by-step)
   - **Parallel:** Research Agent on 50, Enrichment Agent on results (async)
   - **Hierarchical:** Manager Agent (e.g., Orchestrator) decides which Agent handles each prospect type
4. Executes chosen pattern
5. Aggregates results + error handling

**Example Route Decision:**
- Task: "Enrich 100 prospects"
- Size: Large → Parallel (Research + Enrichment agents run simultaneously)
- Fallback: If one fails, retry; if repeated failure, queue for manual review

---

## 3. Memory Architecture (Critical for Autonomy)

**Goal:** Agents never re-research the same prospect. They reuse findings, learn from history, and collaborate via shared memory.

### 3.1 Memory Layers

#### Flat Memory (Simple KV Store)
```python
# In Postgres table: memory_store
# Key-value: prospect:123 -> {name, company, role, ...}
# Fast lookup, no hierarchy
memory.get("prospect:123")  # Returns full prospect context
memory.set("prospect:123:research", {...})  # Store research findings
```

#### Hierarchical Memory (Layered Context)
```python
# Prospect context
memory.get_prospect_context("prospect:123")  # → name, company, role, enrichment history

# Company context
memory.get_company_context("company:456")  # → funding, headcount, tech stack, recent news

# User context
memory.get_user_context("user:puneet")  # → preferences, past skills, performance metrics
```

#### Vector Memory (Semantic Search)
```python
# Store embeddings + metadata in Postgres vector column
# When agent needs similar prospects: "Find companies similar to Acme Corp (SaaS, Series B, 50-200 employees)"
results = memory.semantic_search("SaaS companies Series B headcount:50-200", top_k=5)
# Returns: [Company A, Company B, ...] with similarity scores
```

### 3.2 Memory Store Implementation (`memory_store.py`)
```python
class MemoryStore:
    """Unified memory interface for all agents"""
    
    async def get(self, key: str) -> dict
    async def set(self, key: str, value: dict) -> None
    async def search(self, query: str, top_k: int = 10) -> List[dict]
    
    # Hierarchical shortcuts
    async def get_prospect_context(self, prospect_id: str) -> dict
    async def get_company_context(self, company_id: str) -> dict
    async def get_user_context(self, user_id: str) -> dict
    
    # Logging
    async def log_agent_decision(self, agent_name: str, decision: str, result: dict) -> None
```

### 3.3 Memory Reuse Flow

```
1. Agent A (Research) researches "Acme Corp"
   → Stores findings in hierarchical memory: company:456 = {headcount: 150, funding: Series C, ...}
   → Also stores in vector memory with tags: ["SaaS", "Series C", "150 employees"]

2. Agent B (Enrichment) needs to fill company fields for prospect at Acme
   → Queries memory: "Get company context for Acme"
   → Retrieves cached findings (no re-research!)

3. Agent C (Analytics) later queries: "Find companies similar to Acme"
   → Vector search: "SaaS Series C headcount:100-200"
   → Gets Acme + similar companies (learns from prior research)

4. Monitoring Agent checks daily
   → Compares new research to memory: company:456 (old state)
   → Detects changes: "headcount increased to 175"
   → Updates memory + triggers alerts
```

### 3.4 Decision Logging in Memory
Every agent action is logged for transparency:
```python
# When Research Agent finds something
memory.log_agent_decision(
    agent_name="ResearchAgent",
    decision="Found company Acme Corp",
    result={
        "company_name": "Acme Corp",
        "headcount": 150,
        "funding": "Series C",
        "confidence": 0.95,
        "source": "crawl:linkedin + crawl:company_website"
    }
)
# Stored in fact_agent_executions table (Codex queries this for dashboard)
```

---

## 4. Agent Orchestration Patterns

### 4.1 Sequential Orchestration (Simple Workflows)
```
Task: Enrich single prospect
│
├─ Research Agent: Crawl web for data
│  └─ Output: raw_findings
│
├─ Enrichment Agent: Map findings to CRM schema
│  └─ Output: enriched_prospect
│
└─ Monitoring Agent: (optional) Check for any alerts on company
   └─ Output: alerts (if any)
```

### 4.2 Parallel Orchestration (Bulk/Speed)
```
Task: Enrich 100 prospects
│
├─ Research Agent (async job queue): Crawl all 100
│  └─ Output: 100 raw_findings
│
└─ Enrichment Agent (waits): Map all 100 findings
   └─ Output: 100 enriched_prospects
```

### 4.3 Hierarchical Orchestration (Complex Workflows)
```
Task: "Execute my custom Research Skill on 100 prospects"
│
├─ Orchestrator (Manager): Parse skill definition
│  ├─ Skill requirement: "Find SaaS companies with Series B funding"
│  ├─ Depth: "deep" (full team roster)
│  └─ Action: "Add to hot list if headcount > 50"
│
├─ Worker: Research Agent A handles prospects 1-25
├─ Worker: Research Agent B handles prospects 26-50
├─ Worker: Research Agent C handles prospects 51-75
├─ Worker: Research Agent D handles prospects 76-100
│  └─ All agents run in parallel, using shared memory
│
└─ Orchestrator (Manager): Aggregate results
   ├─ Check rules: did any match "Series B + headcount > 50"?
   └─ Output: hot_list_prospects, metrics
```

---

## 5. Shared Context & No Re-Context Required

**Problem:** Each agent spawn costs context tokens (re-explaining the system).  
**Solution:** Store shared context in memory + pass task-specific context only.

### 5.1 Context Hierarchy

**Level 1: System Context (stored once, referenced always)**
```
Path: memory:system_context
Content: Agent types, memory architecture, orchestration rules, API endpoints
Size: ~5K tokens
Reuse: All agents query this on startup (cache in-memory)
```

**Level 2: Project Context (user's project-specific setup)**
```
Path: memory:project_context
Content: User skills, rules, CRM schema customizations, integrations
Size: ~2K tokens
Reuse: All agents access when executing user workflows
```

**Level 3: Task Context (specific to current work)**
```
Path: memory:task_context:{task_id}
Content: Prospect ID, company ID, skill to execute, rules to check
Size: ~1K tokens
Reuse: Only for agents working on this specific task
```

### 5.2 Context Reuse Flow

```
Agent 1 (Research) runs:
1. Load system_context from memory (cached, no re-read)
2. Load project_context (user skills, rules)
3. Receive task_context (prospect_id, skill_name)
4. Execute research
5. Update task_context with findings

Agent 2 (Enrichment) runs:
1. Load system_context (already cached!)
2. Load project_context (already cached!)
3. Receive task_context (now contains findings from Agent 1)
4. Execute enrichment (no context rebuild!)

Agent 3 (Monitoring) runs:
1. Same pattern—no wasted context
```

**Result:** First agent costs 8K tokens (system + project + task). Subsequent agents cost only 1K tokens (task context only).

---

## 6. Gemini Integration (`gemini_service.py`)

### 6.1 Gemini Prompts by Agent

**Research Agent:**
```
You are a research assistant. Extract structured company/prospect data from web crawl results.
Crawl data: {raw_crawl_output}
Extract: company_name, employee_count, funding_status, tech_stack, headquarters, founders
For each field, provide confidence score (0-1).
```

**Enrichment Agent:**
```
Map the following research findings to CRM prospect schema:
Research: {research_findings}
Schema: {prospect_schema}
Mapping rules:
- If multiple phone numbers found, pick most recent
- If funding amount unclear, ask for clarification
Output: valid JSON matching schema, null for unknown fields
```

**Outreach Agent:**
```
Draft a personalized cold email for this prospect using their context:
Prospect: {prospect_name} at {company_name}
Company Context: {company_findings}
Email Type: {template_name}
Tone: {user_preference}
Personalization: mention {company_event} or {prospect_achievement}
```

### 6.2 Prompt Caching & Optimization

```python
# Store prompt templates in memory
memory.set("prompt:research_extraction", {...})

# Log every prompt + result for evaluation
codex.log_prompt(
    agent="ResearchAgent",
    prompt_template="research_extraction",
    input_data={...},
    output={...},
    tokens_used=450,
    success=True
)

# Later: Gemini evaluates which prompts perform best
gemini_eval = await gemini.evaluate_prompts(
    agent="ResearchAgent",
    metric="extraction_accuracy"
)
# Result: prompt_v2 is 5% better, costs 10% fewer tokens
→ Update prompt_template in memory
→ All future Research Agent calls use better prompt
```

---

## 7. Codex System (`codex/` folder)

**Purpose:** Observability + continuous improvement. Every agent action is logged; Gemini analyzes patterns.

### 7.1 Decision Logger (`decision_logger.py`)
```python
class DecisionLogger:
    async def log(self, agent_name: str, decision: dict) -> None
        """
        Log structure:
        {
            "timestamp": "2026-04-19T10:30:00Z",
            "agent": "ResearchAgent",
            "task_id": "task_123",
            "decision": "Found company Acme Corp with 150 employees",
            "reasoning": "Matched company name on LinkedIn + website",
            "confidence": 0.95,
            "tokens_used": 450,
            "memory_hits": 2,  # How many times reused memory?
            "result": {...},
            "error": null
        }
        """
```

### 7.2 Test Generator (`test_generator.py`)
```python
# Auto-generate test cases from agent workflows
# E.g., if Outreach Agent drafts email for "SaaS founders", generate test:
test_case = TestCase(
    name="Outreach email to SaaS founder",
    input={"prospect": "John at Acme Corp", "company_size": 50},
    expected_output={"email_sent": True, "open_rate": "> 0.3"},
    agent="OutreachAgent"
)
```

### 7.3 Prompt Optimizer (`prompt_optimizer.py`)
```python
# Track all Gemini prompts + evaluate success
# Use Gemini itself to suggest improvements
# "Prompt v1 had 40% hallucinations, Prompt v2 has 5%"
```

### 7.4 Metrics Tracker (`metrics_tracker.py`)
```python
# Track per agent:
# - Token usage (daily total, average per task)
# - Success rate (% of tasks completed without error)
# - Latency (avg time per task)
# - Cost (total Gemini API cost)
# - Memory reuse rate (% of lookups served from memory vs. re-research)
```

### 7.5 Dashboard Data (`dashboard_data.py`)
Aggregates all above into views:
- **Agent Working Logs:** Real-time, which agents are running?
- **Decision History:** All agent decisions, searchable
- **Eval Metrics:** Post-task evaluation (did enriched prospect convert to meeting?)
- **Token Tracking:** Money spent, trending up/down?

---

## 8. Key Design Decisions & Rationales

| Decision | Rationale |
|---|---|
| **Memory-first architecture** | Agents reuse findings; each agent spawn doesn't rebuild context |
| **Gemini 2.5 Flash** | Fast, cheap, good instruction-following for structured extraction |
| **Postgres + vector search** | Relational for strict data, vectors for semantic search (all in one DB) |
| **Async job queue** | Bulk enrichment doesn't block UI; background workers handle heavy lifting |
| **Skill/Rule system** | Users define workflows without coding; agents execute safely |
| **Codex dashboard** | Transparency + continuous improvement (Gemini itself suggests prompt fixes) |
| **Snowflake schema** | Scales well; supports both OLTP (CRM) and OLAP (analytics) |

---

## 9. Error Handling & Resilience

### 9.1 Agent Failure Recovery
```python
# In BaseAgent
async def execute_with_retry(self, task, max_retries=3):
    for attempt in range(max_retries):
        try:
            result = await self.run(task)
            return result
        except TemporaryError as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                continue
            else:
                log_error(f"Agent {self.name} failed after {max_retries} attempts")
                raise
```

### 9.2 Graceful Degradation
```
If Crawl4AI fails:
├─ Try LightPanda fallback
├─ Try cached previous crawl
├─ Return "manual review required" + alert user
└─ Don't crash entire pipeline
```

### 9.3 Data Consistency
```
All agent writes are atomic (Postgres transactions):
├─ Update prospect record
├─ Log agent execution
├─ Update memory
└─ All succeed or all rollback
```

---

## 10. Development Workflow for New Agents

When adding a new agent (e.g., MatchAgent to match prospects to accounts):

1. **Create agent class** (`match_agent.py`):
   ```python
   class MatchAgent(BaseAgent):
       async def match_prospect_to_account(self, prospect_id: str) -> MatchResult:
           # 1. Load prospect + company context from memory
           prospect = await self.memory.get_prospect_context(prospect_id)
           company = await self.memory.get_company_context(prospect.company_id)
           
           # 2. Query Gemini for match logic
           match = await self.gemini_service.match(prospect, company)
           
           # 3. Log decision
           await self.codex.log_agent_decision(
               agent_name=self.name,
               decision=f"Matched {prospect.name} to account {match.account_id}",
               result={"confidence": match.confidence}
           )
           
           return match
   ```

2. **Register in orchestrator** (`orchestrator.py`):
   ```python
   agents = {
       "research": ResearchAgent(...),
       "enrichment": EnrichmentAgent(...),
       "match": MatchAgent(...),  # NEW
   }
   ```

3. **Add to memory reference** (`claude.md`): Update this doc with new agent responsibility

4. **Test via Codex**: Auto-generate test cases, track performance

---

## 11. Quick Reference: Agent Entry Points

When spawning a new agent, reference this quick lookup:

```python
# From orchestrator or API
await agents["research"].research_prospect(prospect_id)
await agents["enrichment"].enrich_prospect(prospect_id, research_data)
await agents["monitoring"].monitor_prospect(prospect_id)
await agents["outreach"].draft_email(prospect_id, email_type)
await agents["analytics"].summarize_interactions(prospect_id, "90d")
await orchestrator.orchestrate(task, agents)
```

---

## 12. When to Reference This Document

- **Starting new agent development:** Read Section 2 + 9
- **Debugging context/memory issues:** Read Section 3 + 5
- **Adding new Gemini prompt:** Read Section 6.2
- **Understanding orchestration:** Read Section 4 + 5
- **Improving performance:** Read Section 7 + Codex
- **Error handling:** Read Section 9

---

**Document Version:** 1.0  
**Status:** MVP Phase  
**Maintainer:** Puneet Shivhare  
**Last Updated:** April 2026