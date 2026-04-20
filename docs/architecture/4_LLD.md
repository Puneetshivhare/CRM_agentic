# Low Level Design (LLD) - Agentic CRM System

**Purpose:** Detailed technical specifications. Database schema, API endpoints, algorithm details, data structures, and implementation notes for developers.

**Audience:** Backend engineers, database architects  
**Version:** 1.0 MVP  
**Date:** April 2026

---

## 1. Database Schema (Snowflake Star Schema)

### 1.1 Authentication Table (Isolated)

```sql
CREATE TABLE auth_users (
    user_id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- NO FOREIGN KEYS to other tables (by design)
    -- Auth is isolated for security
);

CREATE INDEX idx_auth_email ON auth_users(email);
```

**Rationale:** Isolated from data tables. If auth is compromised, data isn't exposed via FK.

---

### 1.2 Dimension Tables

#### dim_prospects
```sql
CREATE TABLE dim_prospects (
    prospect_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,                    -- FK to auth_users (app enforces)
    email VARCHAR(255),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    title VARCHAR(255),                      -- Job title
    company_id INT,                          -- FK to dim_companies
    location VARCHAR(255),
    phone VARCHAR(20),
    linkedin_url VARCHAR(500),
    website_url VARCHAR(500),
    
    -- Enrichment status tracking
    enrichment_status VARCHAR(50),           -- "pending", "enriching", "enriched", "failed"
    enrichment_confidence FLOAT,             -- 0-1 score (how complete is enrichment?)
    
    -- Engagement tracking
    last_contacted_at TIMESTAMP,
    email_opens INT DEFAULT 0,
    email_clicks INT DEFAULT 0,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (company_id) REFERENCES dim_companies(company_id),
    CHECK (enrichment_confidence BETWEEN 0 AND 1)
);

CREATE INDEX idx_prospects_user ON dim_prospects(user_id);
CREATE INDEX idx_prospects_company ON dim_prospects(company_id);
CREATE INDEX idx_prospects_email ON dim_prospects(email);
CREATE INDEX idx_prospects_enrichment ON dim_prospects(enrichment_status, enrichment_confidence);
```

**Columns Explained:**
- `enrichment_status`: Tracks if prospect is being enriched (prevents duplicate jobs)
- `enrichment_confidence`: Used for ranking/display (how much data filled?)
- `email_opens/clicks`: Basic engagement metrics

---

#### dim_companies
```sql
CREATE TABLE dim_companies (
    company_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,                    -- FK to auth_users (app enforces)
    name VARCHAR(255) UNIQUE NOT NULL,
    domain VARCHAR(255),
    description TEXT,
    
    -- Company metrics
    headcount INT,
    headcount_range VARCHAR(20),             -- "50-100", "100-500", etc. (if exact unknown)
    revenue_annual BIGINT,                   -- in USD
    
    -- Company info
    funding_stage VARCHAR(50),               -- "seed", "series_a", "series_b", "ipo", etc.
    latest_funding_date DATE,
    headquarters_city VARCHAR(100),
    headquarters_country VARCHAR(100),
    industry VARCHAR(100),
    
    -- Tech stack (stored as JSON for flexibility)
    tech_stack JSONB DEFAULT '[]',          -- e.g., ["React", "Python", "AWS"]
    
    -- Monitoring
    last_monitoring_run_at TIMESTAMP,
    monitoring_enabled BOOLEAN DEFAULT FALSE,
    
    -- Status
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CHECK (headcount > 0 OR headcount IS NULL)
);

CREATE INDEX idx_companies_user ON dim_companies(user_id);
CREATE INDEX idx_companies_domain ON dim_companies(domain);
CREATE INDEX idx_companies_funding ON dim_companies(funding_stage);
CREATE INDEX idx_companies_monitoring ON dim_companies(monitoring_enabled, last_monitoring_run_at);
```

**Columns Explained:**
- `tech_stack`: JSON for flexibility (no fixed number of technologies)
- `headcount_range`: If exact number unknown, store range for display
- `monitoring_enabled`: User flag to include in daily monitoring

---

#### dim_documents
```sql
CREATE TABLE dim_documents (
    document_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    file_path VARCHAR(500) NOT NULL,         -- e.g., "/uploads/2026-04-19_acme_earnings.pdf"
    file_name VARCHAR(255) NOT NULL,
    document_type VARCHAR(50) NOT NULL,      -- "pdf", "csv", "email_transcript", "call_transcript"
    
    -- Content info
    num_pages INT,
    file_size_bytes INT,
    extracted_text TEXT,                     -- Full text extracted (for RAG)
    
    -- Metadata
    associated_company_id INT,               -- FK to dim_companies (if related to a company)
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (associated_company_id) REFERENCES dim_companies(company_id)
);

CREATE INDEX idx_documents_user ON dim_documents(user_id);
CREATE INDEX idx_documents_company ON dim_documents(associated_company_id);
CREATE INDEX idx_documents_type ON dim_documents(document_type);
```

**RAG Integration:**
- `extracted_text`: Indexed for full-text search
- Later: Add Postgres pgvector column for embeddings

---

#### dim_skills
```sql
CREATE TABLE dim_skills (
    skill_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    skill_name VARCHAR(255) NOT NULL,        -- e.g., "Find SaaS Series B funding"
    skill_type VARCHAR(50) NOT NULL,         -- "research", "outreach", "monitoring", "custom"
    
    -- Skill definition (JSON for flexibility)
    skill_definition JSONB NOT NULL,         -- e.g., {
    -- "criteria": {industry: "SaaS", funding: "Series B"},
    -- "depth": "deep",
    -- "action": "add_to_hot_list"
    -- }
    
    description TEXT,
    version INT DEFAULT 1,                   -- Track changes
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Metrics
    execution_count INT DEFAULT 0,           -- How many times used?
    success_count INT DEFAULT 0,
    avg_execution_time_ms FLOAT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_skills_user ON dim_skills(user_id);
CREATE INDEX idx_skills_type ON dim_skills(skill_type);
CREATE INDEX idx_skills_active ON dim_skills(is_active);
```

**skill_definition JSON Structure:**
```json
{
  "type": "research",
  "criteria": {
    "industry": "SaaS",
    "funding": "Series B",
    "headcount_min": 50,
    "headcount_max": 500
  },
  "depth": "deep",
  "action": {
    "type": "add_to_list",
    "list_name": "hot_list"
  }
}
```

---

#### dim_rules
```sql
CREATE TABLE dim_rules (
    rule_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    rule_name VARCHAR(255) NOT NULL,
    rule_type VARCHAR(50) NOT NULL,         -- "trigger", "data", "workflow"
    
    -- Rule definition (JSON)
    rule_definition JSONB NOT NULL,          -- e.g., {
    -- "type": "trigger",
    -- "condition": "funding_stage = 'Series B'",
    -- "action": "mark_hot"
    -- }
    
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    priority INT DEFAULT 0,                  -- Higher = execute first
    
    -- Metrics
    execution_count INT DEFAULT 0,
    match_count INT DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_rules_user ON dim_rules(user_id);
CREATE INDEX idx_rules_type ON dim_rules(rule_type);
CREATE INDEX idx_rules_active_priority ON dim_rules(is_active, priority DESC);
```

**rule_definition JSON Structure:**
```json
{
  "type": "trigger",
  "condition": "funding_stage = 'Series B' AND headcount > 50",
  "action": {
    "type": "alert",
    "target": "user",
    "message": "Company just got Series B!"
  }
}
```

---

### 1.3 Fact Tables (Immutable Event Logs)

#### fact_interactions
```sql
CREATE TABLE fact_interactions (
    interaction_id SERIAL PRIMARY KEY,
    prospect_id INT NOT NULL,                -- FK to dim_prospects
    interaction_type VARCHAR(50) NOT NULL,   -- "email", "call", "meeting", "linkedin_message"
    
    -- Content
    subject VARCHAR(500),
    body TEXT,
    
    -- Metadata
    initiated_by VARCHAR(50),                -- "user", "prospect"
    interaction_date TIMESTAMP NOT NULL,
    duration_seconds INT,                    -- For calls/meetings
    
    -- Engagement
    email_opened BOOLEAN,
    email_clicked BOOLEAN,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (prospect_id) REFERENCES dim_prospects(prospect_id)
);

CREATE INDEX idx_interactions_prospect ON fact_interactions(prospect_id);
CREATE INDEX idx_interactions_date ON fact_interactions(interaction_date DESC);
CREATE INDEX idx_interactions_type ON fact_interactions(interaction_type);
```

**Immutability:** Inserts only, no updates/deletes (audit trail)

---

#### fact_enrichment_events
```sql
CREATE TABLE fact_enrichment_events (
    event_id SERIAL PRIMARY KEY,
    prospect_id INT NOT NULL,                -- FK to dim_prospects
    field_name VARCHAR(255) NOT NULL,        -- e.g., "company_name", "headcount", "funding"
    old_value TEXT,                          -- Previous value (NULL if new field)
    new_value TEXT NOT NULL,                 -- New value
    
    -- Context
    agent_name VARCHAR(100) NOT NULL,        -- Which agent made the change?
    confidence_score FLOAT,                  -- 0-1 (how confident in this data?)
    source VARCHAR(255),                     -- e.g., "crawl:linkedin", "gemini:extraction"
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (prospect_id) REFERENCES dim_prospects(prospect_id)
);

CREATE INDEX idx_enrichment_prospect ON fact_enrichment_events(prospect_id);
CREATE INDEX idx_enrichment_agent ON fact_enrichment_events(agent_name);
CREATE INDEX idx_enrichment_date ON fact_enrichment_events(created_at DESC);
```

**Immutability:** Complete audit trail of all enrichments

---

#### fact_agent_executions
```sql
CREATE TABLE fact_agent_executions (
    execution_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    agent_type VARCHAR(100) NOT NULL,        -- "ResearchAgent", "EnrichmentAgent", etc.
    agent_name VARCHAR(100),                 -- "ResearchAgent_worker_1" (if parallel)
    task_id VARCHAR(255) NOT NULL,           -- Unique task identifier
    
    -- Task context
    prospect_id INT,                         -- FK to dim_prospects (if applicable)
    company_id INT,                          -- FK to dim_companies (if applicable)
    
    -- Execution details
    status VARCHAR(50) NOT NULL,             -- "pending", "running", "success", "failed"
    input_data JSONB,                        -- What was passed to agent
    output_data JSONB,                       -- What agent returned
    error_message TEXT,                      -- If failed
    
    -- Performance
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration_ms INT,
    tokens_used INT,                         -- For Gemini API calls
    api_cost_cents DECIMAL(10, 2),          -- Cost in cents
    
    -- Decision logging (for Codex)
    decision_description TEXT,               -- e.g., "Found Acme Corp: 150 employees"
    confidence_score FLOAT,                  -- If applicable
    
    memory_hits INT DEFAULT 0,              -- How many times did agent reuse cached data?
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (prospect_id) REFERENCES dim_prospects(prospect_id),
    FOREIGN KEY (company_id) REFERENCES dim_companies(company_id)
);

CREATE INDEX idx_agent_executions_user ON fact_agent_executions(user_id);
CREATE INDEX idx_agent_executions_agent ON fact_agent_executions(agent_type);
CREATE INDEX idx_agent_executions_status ON fact_agent_executions(status);
CREATE INDEX idx_agent_executions_date ON fact_agent_executions(created_at DESC);
CREATE INDEX idx_agent_executions_tokens ON fact_agent_executions(tokens_used);
```

**Purpose:** Codex uses this for:
- Agent working logs (which agents are running)
- Decision history (what did each agent decide)
- Token tracking (how much did we spend on Gemini?)
- Performance metrics (latency, success rate)
- Evaluation metrics (did enriched prospects convert?)

---

### 1.4 Memory Tables

#### memory_store (Flat Memory)
```sql
CREATE TABLE memory_store (
    memory_key VARCHAR(500) PRIMARY KEY,
    memory_value JSONB NOT NULL,
    ttl_seconds INT,                         -- Time to live (optional)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CHECK (ttl_seconds IS NULL OR ttl_seconds > 0)
);

CREATE INDEX idx_memory_accessed ON memory_store(accessed_at DESC);
```

**Key Format Examples:**
```
prospect:123                  → Full prospect context
company:456                   → Full company context
company:456:monitoring_state  → Previous state for change detection
user:789:preferences          → User preferences/settings
cache:research:acme.com       → Cached research results
```

**TTL:** Optional, for temporary cache entries (e.g., 1-hour cache for web crawls)

---

### 1.5 Vector Memory (Embeddings + Semantic Search)

```sql
CREATE TABLE memory_vector (
    vector_id SERIAL PRIMARY KEY,
    embedding_key VARCHAR(500),              -- e.g., "prospect:123:research"
    embedding VECTOR(768),                   -- Gemini embeddings (768 dimensions)
    embedding_text TEXT,                     -- Original text that was embedded
    
    -- Metadata for filtering
    entity_type VARCHAR(50),                 -- "prospect", "company", "skill_result"
    entity_id INT,                           -- Reference to dim_* table
    user_id INT NOT NULL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_embedding CHECK (embedding IS NOT NULL)
);

-- Vector similarity search index (pgvector extension)
CREATE INDEX idx_memory_vector_embedding ON memory_vector USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_memory_vector_user ON memory_vector(user_id);
```

**Usage Example (Python):**
```python
# When Analytics Agent searches for similar companies:
query = "SaaS companies Series B funding 50-200 employees"
query_embedding = gemini_embeddings.embed(query)

results = db.execute("""
    SELECT entity_id, embedding_text, 1 - (embedding <=> %s) as similarity
    FROM memory_vector
    WHERE user_id = %s AND entity_type = 'company'
    ORDER BY similarity DESC
    LIMIT 5
""", (query_embedding, user_id))
```

---

## 2. API Endpoints (FastAPI Routes)

### 2.1 Authentication Routes (`routes/auth.py`)

```
POST /api/auth/signup
  Body: {email, password}
  Response: {user_id, token, message}
  
POST /api/auth/login
  Body: {email, password}
  Response: {token, user_id, email}
  
POST /api/auth/logout
  Response: {message}
  
GET /api/auth/me
  Auth: JWT token
  Response: {user_id, email, created_at}
```

---

### 2.2 Prospect Routes (`routes/prospects.py`)

```
GET /api/prospects
  Query: ?limit=50&offset=0&status=enriching&company_id=123
  Response: {prospects: [...], total_count, page_info}

GET /api/prospects/:id
  Response: {prospect_detail, enrichment_history, interactions}

POST /api/prospects
  Body: {email, first_name, last_name, title, company_id}
  Response: {prospect_id, created_at}

PUT /api/prospects/:id
  Body: {first_name, title, ...}
  Response: {prospect_id, updated_at}

DELETE /api/prospects/:id
  Response: {message}

POST /api/prospects/bulk-create
  Body: {prospects: [{email, first_name, ...}, ...]}
  Response: {created_count, job_id}

POST /api/prospects/:id/enrich
  Body: {depth: "basic" | "deep"}
  Response: {job_id, status, estimated_time_s}

GET /api/prospects/:id/enrichment-history
  Response: {events: [{field, old_value, new_value, agent, timestamp}, ...]}
```

---

### 2.3 Enrichment Routes (`routes/enrichment.py`)

```
POST /api/enrichment/research
  Body: {prospect_id, company_id, depth: "basic"|"deep"}
  Response: {job_id}

POST /api/enrichment/bulk
  Body: {prospect_ids: [1, 2, 3, ...]}
  Response: {job_id, estimated_time_s}

GET /api/enrichment/job/:id
  Response: {status, progress: {completed, total}, results, errors}

POST /api/enrichment/cancel/:id
  Response: {message}
```

---

### 2.4 Monitoring Routes (`routes/monitoring.py`)

```
GET /api/monitoring/watch-list
  Response: {companies: [{company_id, name, last_checked, alerts_count}, ...]}

POST /api/monitoring/watch/:company_id
  Response: {message}

DELETE /api/monitoring/watch/:company_id
  Response: {message}

GET /api/monitoring/alerts
  Query: ?limit=50&unread=true
  Response: {alerts: [{company_id, change_type, description, timestamp}, ...]}

POST /api/monitoring/alert/:id/dismiss
  Response: {message}

POST /api/monitoring/run-now
  Body: {company_ids: [456, 789, ...]}
  Response: {job_id}
```

---

### 2.5 Skills Routes (`routes/skills.py`)

```
GET /api/skills
  Response: {skills: [{skill_id, name, type, execution_count, success_count}, ...]}

GET /api/skills/:id
  Response: {skill_detail, definition, metrics}

POST /api/skills
  Body: {skill_name, skill_type, skill_definition, description}
  Response: {skill_id}

PUT /api/skills/:id
  Body: {skill_name, skill_definition, description}
  Response: {skill_id, version}

DELETE /api/skills/:id
  Response: {message}

POST /api/skills/:id/execute
  Body: {context: {prospect_id, company_id, ...}}
  Response: {job_id}

POST /api/skills/:id/test
  Body: {test_data: {...}}
  Response: {result, success, execution_time_ms}
```

---

### 2.6 Rules Routes (`routes/rules.py`)

```
GET /api/rules
  Response: {rules: [{rule_id, name, type, is_active, execution_count}, ...]}

POST /api/rules
  Body: {rule_name, rule_type, rule_definition}
  Response: {rule_id}

PUT /api/rules/:id
  Body: {rule_name, rule_definition}
  Response: {rule_id}

DELETE /api/rules/:id
  Response: {message}

POST /api/rules/:id/enable
  Response: {message}

POST /api/rules/:id/disable
  Response: {message}
```

---

### 2.7 Codex Routes (`routes/codex.py`)

```
GET /api/codex/dashboard
  Response: {
    agents_running: [{agent, task_id, started_at, progress}],
    recent_decisions: [{agent, decision, timestamp, tokens_used}, ...],
    token_stats: {today_used, today_budget, daily_avg},
    success_rate: 0.95,
    avg_latency_ms: 850
  }

GET /api/codex/decision-logs
  Query: ?agent=ResearchAgent&limit=50&offset=0
  Response: {logs: [{execution_id, agent, decision, result, timestamp}, ...], total}

GET /api/codex/metrics
  Query: ?metric=tokens|latency|success_rate&days=7
  Response: {data: [{date, value}, ...], trend}

GET /api/codex/test-cases
  Query: ?skill_id=10
  Response: {test_cases: [{name, input, expected_output, passed}, ...]}

GET /api/codex/prompt-logs
  Query: ?agent=ResearchAgent
  Response: {prompts: [{prompt_id, version, template, success_rate, avg_tokens}, ...]}
```

---

### 2.8 Documents Routes (`routes/documents.py`)

```
POST /api/documents/upload
  Body: multipart/form-data (file + company_id?)
  Response: {document_id, file_name, extracted_text_preview}

GET /api/documents
  Query: ?company_id=456&type=pdf
  Response: {documents: [{document_id, file_name, type, size_bytes, created_at}, ...]}

GET /api/documents/:id
  Response: {document_detail, extracted_text}

DELETE /api/documents/:id
  Response: {message}

POST /api/documents/search
  Body: {query: "earnings report"}
  Response: {results: [{document_id, file_name, relevance_score, excerpt}, ...]}
```

---

### 2.9 Companies Routes (`routes/companies.py`)

```
GET /api/companies
  Query: ?funding_stage=Series B&industry=SaaS&limit=50
  Response: {companies: [...], total_count}

GET /api/companies/:id
  Response: {company_detail, prospects_count, interactions_count, monitoring_status}

POST /api/companies
  Body: {name, domain, headcount, funding_stage, industry}
  Response: {company_id}

PUT /api/companies/:id
  Body: {headcount, tech_stack, ...}
  Response: {company_id}
```

---

## 3. Core Algorithms & Logic

### 3.1 Research Agent Algorithm

```python
async def research_prospect(prospect_id: str, depth: str = "basic") -> ResearchResult:
    """
    High-level algorithm for research agent
    """
    
    # Step 1: Load context
    prospect = await db.get(Prospect, prospect_id)
    company = await db.get(Company, prospect.company_id)
    
    # Step 2: Check memory (avoid duplicate research)
    cached_company = await memory.get(f"company:{company.id}")
    if cached_company and cache_fresh(cached_company):
        # Cache hit! Skip crawl
        return ResearchResult(
            source="memory_cache",
            data=cached_company,
            tokens_used=0,
            latency_ms=50
        )
    
    # Step 3: Determine crawl scope based on depth
    crawl_targets = []
    if depth == "basic":
        crawl_targets = [company.domain]
    elif depth == "deep":
        crawl_targets = [
            company.domain,
            f"linkedin.com/company/{company.name}",
            f"crunchbase.com/company/{company.name}"
        ]
    
    # Step 4: Crawl web
    crawl_results = []
    for target in crawl_targets:
        try:
            result = await crawl_service.crawl(target)
            crawl_results.append(result)
        except Exception as e:
            logger.error(f"Crawl failed for {target}: {e}")
            # Graceful degradation: skip this target, continue
    
    # Step 5: Parse with Gemini
    raw_text = "\n".join([r.text for r in crawl_results])
    
    parsed_data = await gemini_service.call(
        prompt_template="research_extraction",
        input_data={"raw_crawl": raw_text}
    )
    # Returns: {company_name, headcount, funding_stage, tech_stack, ...}
    
    # Step 6: Store in memory (for future reuse)
    await memory.set(
        key=f"company:{company.id}",
        value=parsed_data,
        ttl_seconds=86400  # 24 hours
    )
    
    # Step 7: Log decision (Codex)
    await codex.log_agent_decision(
        agent="ResearchAgent",
        decision=f"Found {company.name}: {parsed_data.get('headcount')} employees",
        result=parsed_data,
        tokens_used=450,
        memory_hits=1 if cached_company else 0
    )
    
    return ResearchResult(
        source="crawl",
        data=parsed_data,
        tokens_used=450,
        latency_ms=15000,  # Crawl is slowest part
        memory_hits=1 if cached_company else 0
    )
```

---

### 3.2 Enrichment Agent Algorithm

```python
async def enrich_prospect(prospect_id: str, research_data: dict) -> EnrichmentResult:
    """
    Map research findings to CRM schema
    """
    
    prospect = await db.get(Prospect, prospect_id)
    prospect_schema = ProspectModel  # Define what fields can be filled
    
    # Step 1: Prepare mapping prompt
    mapping_prompt = f"""
    Map the following research findings to prospect schema:
    
    Research findings:
    {json.dumps(research_data, indent=2)}
    
    Prospect schema fields:
    {get_schema_description(prospect_schema)}
    
    Rules:
    - Only fill fields with high confidence (>0.8)
    - If multiple values for a field, pick most recent
    - Return JSON matching schema exactly
    """
    
    # Step 2: Call Gemini
    mapped_fields = await gemini_service.call(
        prompt_template="enrichment_mapping",
        input_data={"research_data": research_data}
    )
    # Returns: {company_name: "Acme", company_size: 150, funding: "Series C"}
    
    # Step 3: Validate output
    validated_fields = validate_against_schema(mapped_fields, prospect_schema)
    
    # Step 4: Check for conflicts
    for field, new_value in validated_fields.items():
        old_value = getattr(prospect, field, None)
        if old_value and old_value != new_value:
            # Conflict: which is more recent/trustworthy?
            # Store both, flag for manual review if uncertain
            logger.warning(f"Conflict for {field}: {old_value} vs {new_value}")
    
    # Step 5: Update database (atomic transaction)
    async with db.transaction():
        # Update prospect record
        await db.update(Prospect, prospect_id, validated_fields)
        
        # Log each field change in fact_enrichment_events
        for field, new_value in validated_fields.items():
            old_value = getattr(prospect, field, None)
            await db.create(EnrichmentEvent, {
                "prospect_id": prospect_id,
                "field_name": field,
                "old_value": str(old_value),
                "new_value": str(new_value),
                "agent_name": "EnrichmentAgent",
                "confidence_score": research_data.get(f"{field}_confidence", 0.5),
                "source": "gemini:extraction"
            })
        
        # Update enrichment_status
        await db.update(Prospect, prospect_id, {
            "enrichment_status": "enriched",
            "enrichment_confidence": calculate_confidence(validated_fields)
        })
    
    # Step 6: Log decision (Codex)
    await codex.log_agent_decision(
        agent="EnrichmentAgent",
        decision=f"Filled fields: {', '.join(validated_fields.keys())}",
        result={"fields_filled": len(validated_fields)},
        tokens_used=200
    )
    
    return EnrichmentResult(
        prospect_id=prospect_id,
        fields_filled=validated_fields,
        tokens_used=200
    )
```

---

### 3.3 Monitoring Agent Change Detection Algorithm

```python
async def detect_changes(company_id: str) -> List[ChangeEvent]:
    """
    Compare new crawl with previous state to detect changes
    """
    
    # Step 1: Get previous state from memory
    previous_state = await memory.get(f"company:{company_id}:monitoring_state")
    
    if not previous_state:
        # First time monitoring this company
        # Crawl and store baseline
        current_state = await crawl_service.crawl(company_domain)
        await memory.set(f"company:{company_id}:monitoring_state", current_state)
        return []  # No changes on first run
    
    # Step 2: Crawl fresh data
    current_state = await crawl_service.crawl(company_domain)
    
    # Step 3: Detect changes (use Gemini for smart comparison)
    changes = await gemini_service.call(
        prompt_template="change_detection",
        input_data={
            "previous_state": previous_state,
            "current_state": current_state
        }
    )
    # Returns: [{type: "hiring", detail: "VP Sales hired"}, ...]
    
    # Step 4: For each change, evaluate rules
    alerts = []
    for change in changes:
        matched_rules = []
        
        for rule in await db.get_all(Rule, user_id=company.user_id, is_active=True):
            if await rule_evaluator.matches(rule, change, company):
                matched_rules.append(rule)
                alerts.append(AlertEvent(
                    company_id=company_id,
                    change_type=change["type"],
                    change_detail=change["detail"],
                    triggered_rules=matched_rules
                ))
        
        # Log change in fact_enrichment_events
        await db.create(EnrichmentEvent, {
            "prospect_id": None,  # Company-level change
            "field_name": change["type"],
            "old_value": json.dumps(previous_state.get(change["type"])),
            "new_value": json.dumps(current_state.get(change["type"])),
            "agent_name": "MonitoringAgent",
            "source": "crawl:monitoring"
        })
    
    # Step 5: Update baseline for next run
    await memory.set(
        f"company:{company_id}:monitoring_state",
        current_state
    )
    
    return alerts
```

---

## 4. Job Queue & Async Processing (Celery)

### 4.1 Job Queue Tasks

```python
# app/services/job_queue.py

from celery import Celery

celery_app = Celery(
    "agentic_crm",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379")
)

@celery_app.task(bind=True, max_retries=3)
def enrich_prospect_job(self, prospect_id: int):
    """Async job: enrich single prospect"""
    try:
        research_agent = ResearchAgent()
        enrichment_agent = EnrichmentAgent()
        
        # Research
        research_result = await research_agent.research_prospect(prospect_id)
        
        # Enrichment
        enrichment_result = await enrichment_agent.enrich_prospect(
            prospect_id,
            research_result.data
        )
        
        return {
            "prospect_id": prospect_id,
            "status": "success",
            "fields_filled": len(enrichment_result.fields_filled)
        }
    
    except Exception as exc:
        # Retry with exponential backoff
        retry_count = self.request.retries
        countdown = 2 ** retry_count  # 2, 4, 8 seconds
        raise self.retry(exc=exc, countdown=countdown)

@celery_app.task
def bulk_enrich_prospects_job(prospect_ids: List[int]):
    """Async job: enrich multiple prospects (delegated to task queue)"""
    job_ids = []
    for prospect_id in prospect_ids:
        job = enrich_prospect_job.delay(prospect_id)
        job_ids.append(job.id)
    
    return {"job_ids": job_ids}

@celery_app.task
def monitor_all_watch_list_job():
    """Scheduled job: daily monitoring of all watched companies"""
    monitoring_agent = MonitoringAgent()
    
    watched_companies = db.query(Company).filter_by(monitoring_enabled=True).all()
    
    for company in watched_companies:
        alerts = await monitoring_agent.detect_changes(company.id)
        
        if alerts:
            # Notify user (email/Slack - future)
            notify_user(company.user_id, alerts)

# Schedule this job to run daily at 8 AM
celery_app.conf.beat_schedule = {
    'monitor-watch-list': {
        'task': 'app.services.job_queue.monitor_all_watch_list_job',
        'schedule': crontab(hour=8, minute=0),
    },
}
```

---

## 5. Gemini Prompt Templates

### 5.1 Research Extraction Prompt

```
You are a research data extraction assistant.

From the following web crawl results, extract structured company and prospect data.

Web Crawl Results:
{raw_crawl}

Please extract the following fields (return JSON):
- company_name: (string)
- company_headcount: (integer, null if unknown)
- headcount_range: (string, e.g., "50-100", if exact unknown)
- funding_stage: (string, e.g., "seed", "series_a", "series_b", "series_c", "ipo")
- latest_funding_amount: (string, e.g., "$10M", null if unknown)
- latest_funding_date: (YYYY-MM-DD format, null if unknown)
- headquarters_city: (string)
- headquarters_country: (string)
- industry: (string)
- tech_stack: (array of strings)
- company_description: (string, 1-2 sentences)

For each field, provide:
- value: (the extracted value or null)
- confidence: (0.0 - 1.0, how confident are you?)
- source: (which URL/text did this come from?)

Return ONLY valid JSON, no other text.
```

---

### 5.2 Change Detection Prompt

```
You are a change detection assistant.

I'm monitoring a company for important changes. I'll give you the previous state and current state of company data.

Previous State:
{previous_state}

Current State:
{current_state}

Please identify all meaningful changes. For each change, provide:
- type: (e.g., "funding", "hiring", "tech_change", "news", "restructuring")
- detail: (specific description, e.g., "VP Sales hired: John Smith")
- significance: ("low", "medium", "high")
- timestamp: (estimated date of change, if known)

Return as JSON array:
[
  {
    "type": "...",
    "detail": "...",
    "significance": "...",
    "timestamp": "..."
  },
  ...
]

If no meaningful changes, return empty array [].
```

---

### 5.3 Enrichment Mapping Prompt

```
You are a data mapping assistant.

I have research findings about a prospect and need to map them to my CRM schema.

Research Findings:
{research_data}

CRM Prospect Schema Fields:
- email (string)
- first_name (string)
- last_name (string)
- title (string)
- company_name (string)
- company_size (enum: "1-10", "10-50", "50-200", "200-1000", "1000+")
- company_funding (string)
- company_industry (string)

Rules:
1. Only fill fields if confidence > 0.7
2. For company_size, map exact headcount to enum ranges
3. If conflicting information found, pick most recent
4. Return ONLY JSON matching the schema

Return JSON:
{
  "email": "...",
  "first_name": "...",
  "title": "...",
  "company_name": "...",
  "company_size": "...",
  "company_funding": "...",
  ...
}
```

---

## 6. Error Handling & Edge Cases

### 6.1 Crawl4AI Failures

```python
async def crawl_with_fallback(domain: str) -> CrawlResult:
    try:
        # Try primary: Crawl4AI + LightPanda
        return await crawl4ai_service.crawl(domain)
    
    except CrawlError as e:
        logger.warning(f"Crawl4AI failed: {e}")
        
        try:
            # Fallback 1: Try cached previous crawl
            cached = await memory.get(f"crawl_cache:{domain}")
            if cached and cache_age_hours(cached) < 24:
                logger.info(f"Using cached crawl for {domain}")
                return cached
        except:
            pass
        
        try:
            # Fallback 2: Try LightPanda only (simpler)
            return await lightpanda_service.crawl(domain)
        except:
            pass
        
        # Fallback 3: Synthetic data (risky)
        logger.warning(f"All crawl methods failed for {domain}, returning placeholder")
        return CrawlResult(
            domain=domain,
            status="failed_synthetic",
            text="Unable to crawl website",
            note="Manual review required"
        )
```

---

### 6.2 Gemini API Rate Limiting

```python
from tenacity import (
    retry,
    wait_exponential,
    stop_after_attempt
)

@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    stop=stop_after_attempt(3)
)
async def gemini_call_with_retry(prompt: str, **kwargs):
    """Call Gemini with automatic retry on rate limit"""
    try:
        response = await gemini_service.call(prompt, **kwargs)
        return response
    except RateLimitError as e:
        logger.warning(f"Gemini rate limit hit, retrying...")
        raise  # tenacity will retry
    except Exception as e:
        logger.error(f"Gemini call failed: {e}")
        raise
```

---

## 7. Testing Strategy

### 7.1 Unit Tests

```python
# tests/test_research_agent.py

@pytest.mark.asyncio
async def test_research_prospect_with_cache_hit():
    """Test that research agent reuses cached company data"""
    
    # Setup
    prospect_id = 123
    company_id = 456
    cached_company = {"headcount": 150, "funding": "Series C"}
    
    # Mock memory to return cached data
    mock_memory.get.return_value = cached_company
    
    # Call
    result = await research_agent.research_prospect(prospect_id)
    
    # Assert
    assert result.source == "memory_cache"
    assert result.tokens_used == 0  # No Gemini call!
    assert result.latency_ms < 100  # Cache lookup is fast
```

### 7.2 Integration Tests

```python
# tests/test_enrich_flow.py

@pytest.mark.asyncio
async def test_full_enrichment_flow():
    """Test end-to-end: research → enrichment → memory update"""
    
    # Create test prospect
    prospect = await create_test_prospect(
        email="john@acme.com",
        company="Acme Corp"
    )
    
    # Run orchestrated workflow
    result = await orchestrator.orchestrate(
        task=Task(
            type="enrich",
            prospect_id=prospect.id
        ),
        agents=[research_agent, enrichment_agent]
    )
    
    # Assertions
    assert result.status == "success"
    
    # Check prospect updated
    updated = await db.get(Prospect, prospect.id)
    assert updated.company_name == "Acme Corp"
    assert updated.enrichment_status == "enriched"
    
    # Check memory cached
    cached = await memory.get(f"company:{prospect.company_id}")
    assert cached is not None
    assert cached["headcount"] == 150
```

---

## 8. Performance Optimization Notes

### 8.1 Database Query Optimization

```sql
-- Index on prospect.enrichment_status for quick filtering
CREATE INDEX idx_prospects_enrichment_status 
ON dim_prospects(enrichment_status) 
WHERE enrichment_status IN ('pending', 'enriching');

-- Composite index for common filters
CREATE INDEX idx_prospects_user_company 
ON dim_prospects(user_id, company_id);
```

### 8.2 Memory Reuse Metrics

Track memory hit rate:
```python
memory_hits = db.query(fact_agent_executions).filter(
    memory_hits > 0
).count()

total_executions = db.query(fact_agent_executions).count()

hit_rate = memory_hits / total_executions  # Aim for > 60%
```

---

**Document Version:** 1.0  
**Status:** MVP Phase  
**Last Updated:** April 2026