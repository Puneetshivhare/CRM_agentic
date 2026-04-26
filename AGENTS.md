# CRM Project — Codex Instructions

## ⚠️ CRITICAL: Separate Docker Projects Running

**DO NOT touch or modify these containers — they are from a separate project:**
- `nova-frontend` (local_setup-frontend, port 3000)
- `nova-backend` (local_setup-backend, port 8000)

These are independent and should be left running as-is. Only work with **agentic-crm-*** containers.

## Project Containers
- **agentic-crm-redis** — Redis cache (port 6380)
- **agentic-crm-backend** — FastAPI backend (port 8000, shared with nova but different container)
- **agentic-crm-chroma** — Vector DB (disabled temporarily, port 8005)

When running `docker compose` commands, they only affect the agentic-crm project containers, not nova.
