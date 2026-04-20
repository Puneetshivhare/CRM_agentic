# Product Requirements Document (PRD)
## Agentic CRM with AI-Powered Prospect Enrichment

**Project Name:** SalesAI Pro (Internal Codename: Agentic-CRM)  
**Version:** 1.0 MVP  
**Date:** April 2026  
**Author:** Puneet Shivhare  
**Status:** Architecture Phase → Development Ready  

---

## 1. Executive Summary

SalesAI Pro is an **agentic AI-powered CRM** designed for B2B SaaS/Software sales teams to autonomously research, enrich, and monitor prospects. Unlike traditional CRMs that require manual data entry, agents work together to:
- **Crawl the web** (Crawl4AI + LightPanda) for company/prospect data
- **Enrich records** in real-time using Gemini 2.5 Flash
- **Monitor for changes** (hiring, funding, product updates)
- **Execute custom workflows** (skills) defined by sales reps
- **Share learnings** via distributed memory (no context rebuilding)

**Target User:** B2B SaaS/Software sales reps and teams  
**Primary Value:** 10x faster prospect research, automated lead qualification, change-based outreach

---

## 2. Problem Statement

### Current Pain Points
1. **Manual Research:** Sales reps spend 2-3 hours daily researching prospects manually (LinkedIn, company websites, news)
2. **Data Fragmentation:** Prospect info scattered across email, LinkedIn, CRM, notes (no single source of truth)
3. **Context Loss:** Each team member reruns the same research because context isn't shared
4. **Change Blindness:** Can't detect when a prospect company hires, gets funded, or changes direction
5. **Repetitive Workflows:** Same outreach patterns (email drafting, qualification rules) applied manually each time

### Why Existing Solutions Fall Short
- HubSpot/Salesforce: Manual enrichment, no autonomous research
- LinkedIn Sales Navigator: No CRM integration, no automation
- Clay/Hunter: Batch enrichment only, not intelligent/contextual
- Generic LLMs (ChatGPT): No persistent memory, no workflow automation, no integration with CRM

---

## 3. Solution Overview

### Core Offering
An **agentic system** where multiple AI agents collaborate to manage the full prospect research lifecycle:

| Agent Type | Responsibility | Triggers |
|---|---|---|
| **Research Agent** | Web crawl, company/prospect profiling | Manual lookup, bulk CSV, scheduled monitoring |
| **Enrichment Agent** | Fill CRM fields using crawled data + Gemini | Post-research, on-demand |
| **Monitoring Agent** | Watch for company changes (hiring, funding, news) | Daily scheduler, webhook triggers |
| **Outreach Agent** | Draft emails, qualify leads, suggest next steps | User skill definition, rules-based |
| **Analytics Agent** | Summarize interactions, generate insights via RAG | Triggered on demand, scheduled reports |

### Agent Orchestration
- **Smart Routing:** Agents decide if they work sequentially, parallel, or hierarchical based on task complexity
- **Shared Memory:** All agents access flat/hierarchical/vector memory—no repeated research
- **Autonomy:** Agents self-regulate based on rules and skills defined by users

---

## 4. User Personas & Workflows

### Persona 1: Account Executive (AE)
**Daily Workflow:**
1. **9:00 AM:** Receive list of prospects to target
2. **9:10 AM:** Upload CSV to CRM → Research Agent kicks off batch enrichment
3. **10:00 AM:** Review enriched prospects (company info, team size, tech stack) in CRM table
4. **11:00 AM:** Outreach Agent auto-drafts 5 personalized emails based on custom skill
5. **2:00 PM:** Check alerts—Monitoring Agent flagged 3 companies that just raised funding
6. **3:00 PM:** Manual follow-up with those hot prospects

### Persona 2: Sales Operations Manager
**Weekly Workflow:**
1. Define new Skills (e.g., "Identify companies with >50% revenue growth YoY")
2. Set monitoring Rules (e.g., "Alert if any prospect company hires in sales")
3. Review Codex Dashboard: agent decision logs, token usage, success rates
4. Iterate prompts based on Gemini evaluation suggestions
5. Share learnings with team via shared memory

### Persona 3: Sales Development Rep (SDR)
**Daily Workflow:**
1. Work through daily queue of pre-qualified prospects (Qualification Skill pre-filtered them)
2. Review Research Agent's findings + Outreach Agent's suggested talking points
3. Make calls armed with company context (from RAG analysis of past emails)
4. Log call outcomes—triggers Monitoring Agent to re-evaluate prospect score

---

## 5. Core Features (MVP → v1.1)

### Phase 1: MVP (Week 1-2)
**Minimum Viable Product focused on single-prospect workflow**

#### 5.1.1 Prospect Management (CRM Core)
- [ ] Dynamic table view with custom columns (email, company, role, location, etc.)
- [ ] Add/edit/delete prospects manually or via CSV import
- [ ] Column templates (quick add "email", "phone", "company_funding", etc.)
- [ ] Search/filter prospects by any field

#### 5.1.2 Single Prospect Enrichment (Agent 1)
- [ ] User enters prospect name/company → **Research Agent** automatically:
  - Crawls web (Crawl4AI + LightPanda)
  - Finds company info, prospect role, social links, company funding
  - Enriches Prospect table with found data
  - Stores raw crawl results in Documents table (for RAG)
- [ ] Enrichment status indicator (pending, success, failed)
- [ ] Option to manually trigger re-research

#### 5.1.3 Basic Monitoring (Agent 2)
- [ ] Watch list: select prospects to monitor
- [ ] Daily job checks for:
  - New funding announcements (via web crawl + Gemini keyword detection)
  - New hires in sales/product teams
  - Company news/mentions
- [ ] Alert panel showing flagged prospects

#### 5.1.4 Supabase Integration
- [ ] Auth: email/password signup via Supabase
- [ ] Tables: Prospects, Companies, Interactions, Enrichment Events, Agent Executions, Documents
- [ ] Auth table NOT linked to others (isolated for security)
- [ ] Postgres connection local via Docker

#### 5.1.5 File Handling (RAG Foundation)
- [ ] Upload PDFs (company reports, earnings calls, playbooks)
- [ ] Upload CSVs (prospect lists, company lists)
- [ ] Extract text/tables from PDFs (pypdf or similar)
- [ ] Store document metadata + embeddings for semantic search (using Gemini embeddings)

### Phase 2: Advanced Features (Week 3-4)
**Multi-agent orchestration, user-defined skills, full RAG**

#### 5.2.1 Bulk Enrichment
- [ ] CSV upload → async job queue
- [ ] Process 100s of prospects in background
- [ ] Progress tracker (X/Y completed, failures logged)
- [ ] Export enriched data back to CSV

#### 5.2.2 User-Defined Skills (Rule + Workflow)
- [ ] UI to create custom Skills:
  - **Research Skill:** "Find all SaaS companies in California with 50-200 employees"
    - Criteria: industry, location, headcount range
    - Enrichment depth: basic (company info) vs. deep (full team roster)
  - **Outreach Skill:** "Draft cold email personalizing for company growth metrics"
    - Template + dynamic fields (company, founder, growth rate)
    - Outreach Agent fills and sends via email
  - **Monitoring Skill:** "Alert if any prospect company hires VP Sales"
    - Trigger: new hire detected in sales department
    - Action: add to hot list, notify Slack
  - **Custom Skill:** Arbitrary workflows (analysis, comparison, qualification)
- [ ] Skill versioning and testing

#### 5.2.3 Rules Engine
- [ ] Trigger rules: IF prospect company gets Series B funding THEN mark as hot-list
- [ ] Data rules: IF email domain is @company.com AND revenue > $10M THEN high priority
- [ ] Workflow rules: IF research incomplete THEN run web crawl before drafting email
- [ ] Custom rule builder (advanced)

#### 5.2.4 RAG & Analysis Agent
- [ ] Search across all documents (PDFs, emails, call transcripts) for prospect insights
- [ ] Summarization: "Summarize all interactions with Company X in last 90 days"
- [ ] Comparison: "How does Company A's tech stack compare to Company B?"
- [ ] Prompt user with contextual insights during outreach

#### 5.2.5 Codex & Observability Dashboard
- [ ] **Agent Decision Logs:** Each agent action logged with reasoning
  - "Research Agent ran web crawl for acme.com → found 150 employees, Series C funded"
  - "Outreach Agent evaluated 5 email templates → selected template_3 with highest historical open rate"
- [ ] **Test Case Auto-Generation:** For each skill, generate test cases
- [ ] **Prompt Engineering Logs:** Track Gemini prompt variations and success rates
- [ ] **Performance Metrics:** Token usage per agent, latency, success rate, cost breakdown
- [ ] **Agent Working Logs:** Real-time view of which agents are running, what they're doing
- [ ] **Eval Metrics Dashboard:** Post-completion evaluation (prospects qualified correctly? emails opened? meetings booked?)
- [ ] **Token Tracker:** Cumulative tokens spent per day/week/month

### Phase 3: Future (v1.1+)
See **Future Integration Plan** document.

---

## 6. Non-Functional Requirements

### Performance
- Single prospect enrichment: < 30 seconds (crawl + Gemini)
- Bulk enrichment (100 prospects): < 5 minutes (async)
- CRM table rendering: < 1 second
- Search/filter: < 500ms over 10K prospects
- Agent decision: < 5 seconds

### Reliability
- Agent failure recovery: automatic retry (max 3 times)
- Graceful degradation: if Crawl4AI fails, skip research (or fetch from cache)
- Data durability: all agent decisions logged to Postgres
- Uptime: 99% (acceptable downtime for local Docker)

### Security
- Auth table isolated (no FK to other tables)
- Prospect/Company data at rest: encrypted (Supabase handles)
- API keys (Gemini): stored in environment variables (Docker secrets)
- Audit log: all agent actions + human reviews logged

### Scalability
- Design for scale (even though MVP is small):
  - Async job queue (Celery/Bull) for background enrichment
  - Connection pooling to Postgres
  - Vector DB prepared for 100K+ documents (future)
  - Agent memory uses semantic search (not full context replay)

---

## 7. Data Model Overview (Snowflake Schema)

### Core Dimensions
- **Prospects** (dim_prospects): people records
- **Companies** (dim_companies): organization records
- **Documents** (dim_documents): uploaded PDFs, transcripts, playbooks
- **Skills** (dim_skills): user-defined workflows
- **Rules** (dim_rules): user-defined logic constraints

### Core Facts
- **Interactions** (fact_interactions): emails, calls, meetings with prospects
- **Enrichment Events** (fact_enrichment_events): audit trail of data added by agents
- **Agent Executions** (fact_agent_executions): every agent run (what it did, result, tokens, time)

**See LLD document for full schema.**

---

## 8. Success Metrics

### User-Level Metrics
- **Prospect research time reduced:** from 2 hours → 20 minutes per prospect
- **Bulk list enrichment time:** 100 prospects enriched in <30 minutes (vs. manual 8+ hours)
- **Email open rate:** templated + AI-personalized emails open at 45%+ (vs. 15-20% generic)
- **Meeting booking rate:** from enriched prospects, 20%+ convert to meetings (vs. 5% cold)

### Product-Level Metrics
- **Agent accuracy:** enriched data matches manual research 95%+ of the time
- **False positives in alerts:** <5% (monitoring agent accuracy)
- **Skill reuse:** 80%+ of enrichment tasks use existing skills (not one-offs)
- **Cost efficiency:** cost per enriched prospect < $0.10 (Gemini API)

### Observability Metrics (via Codex)
- **Agent success rate:** >90% of agent runs complete without error
- **Token efficiency:** improving over time (better prompts = fewer tokens)
- **Memory reuse:** >60% of agent tasks reuse prior findings (not re-researching)

---

## 9. Technical Stack (Quick Reference)

| Component | Choice | Rationale |
|---|---|---|
| **Frontend** | React + Next.js | Fast iteration, component reuse |
| **Backend** | Python (FastAPI) or Node.js | Fast startup, good async support |
| **Database** | Postgres (Supabase) | Relational + affordable + Docker-ready |
| **Web Scraping** | Crawl4AI + LightPanda | No Windows limitation, handles JS-heavy sites |
| **LLM API** | Gemini 2.5 Flash | Fast, affordable, good instruction following |
| **RAG/Embeddings** | Gemini embeddings + vector search | Native to Gemini, cheaper than alternatives |
| **Job Queue** | Celery (Python) or Bull (Node) | Async enrichment, monitoring, email sending |
| **Deployment** | Docker (WSL on Windows) | Local dev, portable to cloud |
| **Auth** | Supabase Auth | Built-in, JWT-based, no external service needed |

---

## 10. Assumptions & Constraints

### Assumptions
1. **Gemini API availability:** Assumes Gemini 2.5 Flash is stable and affordable
2. **Web crawlability:** Most prospect/company websites are crawlable (not behind paywalls)
3. **User adoption:** Users will define skills correctly (training required)
4. **Data quality:** Enriched data is ~95% accurate (hallucinations possible, human review encouraged)

### Constraints
1. **MVP 5-6 hours to working version:** Must focus on core workflows, skip nice-to-haves
2. **Windows WSL Docker:** No native Windows support for Crawl4AI initially
3. **Single user (MVP):** Supabase auth exists but no multi-team collaboration yet
4. **No real-time:** Async jobs, not WebSockets for live updates (v1.1)
5. **PDF handling:** Basic text extraction (no table recognition in MVP)

---

## 11. Out of Scope (For Future Releases)

- Slack/Jira integrations (Phase 2, v1.1)
- Email account integration (v1.1)
- Calendar integration (v1.1)
- Multi-user collaboration (v1.1)
- Advanced analytics dashboard (v1.2)
- Custom LLM training/fine-tuning (v2.0)
- On-prem deployment (future)

---

## 12. Go-to-Market & Pricing (Strategic Notes)

**Model:** SaaS subscription (MVP is self-hosted Docker; later cloud-hosted)

**Pricing Tiers (Future):**
- **Starter:** 500 prospects, 5 skills, $99/month
- **Pro:** 10K prospects, unlimited skills, $299/month
- **Enterprise:** Custom (with Jira/Slack/calendar integrations)

**Key Message:** "Your AI sales co-pilot that researches, enriches, and qualifies prospects while you focus on selling."

---

## 13. Handoff to Development

### Documents to Follow
1. **Claude.md** - Codebase structure, module architecture, how agents interact
2. **HLD** - System design, data flow, agent orchestration patterns
3. **LLD** - Database schema, API endpoints, algorithm details
4. **Future Integration Plan** - Roadmap for integrations and scaling

### Next Steps
1. Review this PRD with Claude (AI) for completeness
2. Review HLD for technical feasibility
3. Begin backend development (Postgres schema first)
4. Build Research Agent + basic enrichment
5. Iterate with Codex feedback loop

---

**Document Version:** 1.0  
**Last Updated:** April 2026  
**Next Review:** After MVP completion (Week 2)