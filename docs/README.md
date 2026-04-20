# CRM Project Documentation

Complete documentation for the Agentic CRM system.

---

## 📁 Folder Structure

### `/design` — Project Design & Specifications
- **0_TECH_STACK.md** — Technology choices and rationale
- **1_PRD.md** — Product requirements document
- **CRM_INTEGRATION_OPTIONS.md** — Current system vs HubSpot OSS integration paths

### `/architecture` — System Architecture
- **3_HLD.md** — High-level design (agents, API, database)
- **4_LLD.md** — Low-level design (detailed implementation)
- **4_LLD_COMPLETE.md** — Complete low-level specifications

### `/setup` — Setup & Installation
- **2_Claude.md** — Claude Code setup instructions
- **8_IMPLEMENTATION_EXECUTION_PLAN.md** — Step-by-step implementation guide
- **9_PRE_IMPLEMENTATION_CHECKLIST.md** — Pre-launch checklist

### `/testing` — Quality & Production Readiness
- **PRODUCTION_READINESS_TEST_PLAN.md** — Comprehensive test cases and release gates

### `/` (Root) — Meta Documents
- **5_Future_Integration_Plan.md** — Phase 2+ roadmap
- **6_DOCUMENT_REVIEW_AND_COMPLETENESS.md** — Documentation audit
- **7_SECURITY_AND_SCRAPING_MITIGATION.md** — Security & compliance guidelines

---

## 🚀 Quick Links

**Getting Started?** → Read `/setup/2_Claude.md`

**Understanding the System?** → Read `/architecture/3_HLD.md`

**Building on Top?** → Read `/design/CRM_INTEGRATION_OPTIONS.md`

**Security Concerns?** → Read `7_SECURITY_AND_SCRAPING_MITIGATION.md`

---

## 📊 Document Status

| Document | Status | Purpose |
|----------|--------|---------|
| Tech Stack | ✅ Current | Technology choices |
| PRD | ✅ Current | Feature requirements |
| HLD | ✅ Current | System architecture |
| LLD | ✅ Current | Implementation details |
| CRM Integration | ✅ Updated | Current + Future paths |
| Security | ✅ Current | Compliance guidelines |

---

## 🔄 Updating Docs

When making changes to the system:
1. Update relevant architecture doc first
2. Update integration options if affecting CRM/database
3. Update checklist if adding pre-launch requirements
4. Keep design docs in sync with implementation

---

## 📝 Notes

- **Database**: Supabase PostgreSQL (configured in `.env`)
- **Vector Store**: Chroma (in Docker)
- **API**: FastAPI (backend/app/main.py)
- **Agents**: Research, Enrichment, Monitoring (backend/app/agents/)
- **Current Phase**: MVP Complete (all 8 core tasks done)

See `.env` for current credentials (Supabase, Gemini API, JWT secret).
