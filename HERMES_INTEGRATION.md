"""
HERMES_INTEGRATION.md — Hermes Agent SaaS Integration Guide

Overview
========
This document describes how Hermes Agent is integrated into Agentic CRM as a
multi-tenant SaaS service with restricted operations and isolated skill libraries.

Architecture
============

┌─────────────────────────────────────────────────────────────────────────────┐
│                           AGENTIC CRM SAAS                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────────┐     │
│  │   Frontend   │───▶│   Backend    │───▶│   Hermes Agent           │     │
│  │   (Next.js)  │    │   (FastAPI)  │    │   (Per-tenant container) │     │
│  └──────────────┘    └──────────────┘    └──────────────────────────┘     │
│                              │                        │                    │
│                              ▼                        ▼                    │
│                        ┌──────────┐           ┌────────────┐               │
│                        │  Redis   │           │PostgreSQL │               │
│                        │(Pub/Sub) │           │(Shared DB) │               │
│                        └──────────┘           └────────────┘               │
└─────────────────────────────────────────────────────────────────────────────┘

Key Features
============

1. Separate Hermes Container Per Tenant
   - Each tenant gets isolated memory and skills
   - Shared infrastructure (cost-effective for SaaS)
   - Namespace-based isolation within single container

2. Restricted Operations (Guardrails)
   ✓ ALLOWED: web_search, web_crawl, prospect_research, company_enrichment
   ✓ ALLOWED: MCP connections (crm_backend, graphify, web_search)
   ✗ BLOCKED: bash_execution, python_execution, system_commands
   ✗ BLOCKED: file_system_write, ssh_connect, code_interpreter

3. REST API Integration
   - CRM Backend → Hermes REST API (Option B)
   - Async task execution with webhook callbacks
   - Comprehensive execution logging

Quick Start
===========

1. Start the services:
   
   docker compose up -d hermes

2. Provision a tenant:
   
   curl -X POST http://localhost:8005/api/hermes/tenants/provision \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "tenant_id": "tenant-123",
       "tenant_name": "Acme Corp"
     }'

3. Enrich a prospect:
   
   curl -X POST http://localhost:8005/api/hermes/prospects/456/enrich \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "tenant_id": "tenant-123"
     }'

API Endpoints
=============

Tenant Management:
- POST   /api/hermes/tenants/provision    → Create tenant
- GET    /api/hermes/tenants/{id}/status   → Tenant status
- GET    /api/hermes/tenants/{id}/config   → Guardrails config

Task Execution:
- POST   /api/hermes/tasks/research        → Execute research task
- POST   /api/hermes/prospects/{id}/enrich → Enrich prospect
- POST   /api/hermes/search                → Web search

Skills & Memory:
- GET    /api/hermes/tenants/{id}/skills   → List learned skills
- GET    /api/hermes/tenants/{id}/executions → Execution history

Integration with Existing Enrichment
====================================

The existing enrichment flow can leverage Hermes:

# In your existing code:
from app.services.hermes_service import hermes_service

async def enrich_prospect_with_hermes(
    prospect_id: int,
    tenant_id: str,
    user_id: int,
    db: Session,
):
    '''Use Hermes for web research instead of direct crawling.'''
    
    result = await hermes_service.enrich_prospect(
        tenant_id=tenant_id,
        user_id=user_id,
        prospect_id=prospect_id,
    )
    
    if result["status"] == "completed":
        # Process Hermes results
        data = result["data"]
        # Update prospect, create documents, etc.
        pass
    
    return result

Guardrails Configuration
========================

File: hermes/guardrails.yml

- web_crawl.max_depth: 1 (no deep crawling)
- web_crawl.max_pages_per_session: 10
- web_search.max_results: 10
- rate_limits.requests_per_minute: 60
- rate_limits.tokens_per_day: 100000

Adding blocked domains or patterns:
  blocked_domains:
    - *.gov
    - *.mil
  
  blocked_query_patterns:
    - "hack *"
    - "*password*"

Environment Variables
=====================

Add to backend/.env:

# Hermes Integration
HERMES_BASE_URL=http://hermes:8000
HERMES_API_KEY=your_secure_key_here

Add to root .env:

# Hermes Container
HERMES_CRM_API_KEY=your_secure_key_here

Multi-Tenant Deployment
=======================

For production SaaS with many tenants:

Option 1: Namespace Isolation (Current)
- Single Hermes container
- Tenant data isolated by namespace in shared database
- Skills stored per-tenant in isolated directories
- Cost-effective for early-stage SaaS

Option 2: Container Per Tenant (Future)
- Each tenant gets dedicated container
- Full isolation at container level
- Higher cost but maximum security
- Use Docker Swarm/Kubernetes for orchestration

Monitoring
==========

Health Check:
curl http://localhost:8010/health

Tenant Status:
curl http://localhost:8005/api/hermes/tenants/{tenant_id}/status

Execution Logs:
curl http://localhost:8005/api/hermes/tenants/{tenant_id}/executions

Security Considerations
=======================

1. API Key Authentication
   - All Hermes endpoints require X-API-Key header
   - Tenant isolation validated on every request

2. Guardrails Enforcement
   - Actions validated before execution
   - MCP servers whitelisted
   - Search queries sanitized

3. Data Isolation
   - Tenant ID required on all operations
   - Database queries filtered by tenant
   - Skills stored in tenant-isolated directories

4. Rate Limiting
   - Per-tenant rate limits enforced
   - Prevents resource exhaustion

Troubleshooting
===============

Issue: Hermes container won't start
→ Check docker-compose logs: docker compose logs hermes

Issue: Tasks blocked by guardrails
→ Check guardrails.yml configuration
→ Review blocked_actions list

Issue: Database connection failed
→ Verify DATABASE_URL in hermes environment
→ Check postgres container is healthy

Issue: Rate limit exceeded
→ Adjust rate_limits in guardrails.yml
→ Implement client-side throttling

Next Steps
==========

1. Run database migrations:
   docker compose exec backend alembic upgrade head

2. Test with sample tenant:
   ./scripts/test_hermes_integration.sh

3. Configure Graphify integration:
   - Set GRAPHIFY_URL in environment
   - Create knowledge graph for codebase

4. Monitor first tenants:
   - Check execution logs
   - Review skill creation
   - Validate data isolation
