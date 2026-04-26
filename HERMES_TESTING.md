# Hermes Integration Testing Checklist

## Pre-requisites
- [ ] Docker Desktop is running
- [ ] You're on the `codex/backend_refactor` branch
- [ ] `.env` file has required variables

## Step-by-Step Testing

### 1. Check Git Status
```bash
git status
git branch  # Should show: * codex/backend_refactor
```

### 2. Start Services
```bash
# Build and start Hermes
docker compose build hermes
docker compose up -d hermes

# Verify containers are running
docker compose ps
```

### 3. Run Database Migration
```bash
# Apply new migration
docker compose exec backend alembic upgrade head

# Verify tables created
docker compose exec postgres psql -U crm_user -d agentic_crm -c "\dt hermes_*"
```

### 4. Test Hermes Health
```bash
# Hermes health check
curl http://localhost:8010/health

# Expected response:
# {"status": "healthy", "service": "hermes-agent", ...}
```

### 5. Test Backend Integration
```bash
# Backend health (should include Hermes routes)
curl http://localhost:8005/api/health

# Check OpenAPI docs for Hermes routes
curl http://localhost:8005/api/openapi.json | grep hermes
```

### 6. Create Test Tenant (requires authentication)

First, login to get a token:
```bash
# Login (if you have test credentials)
curl -X POST http://localhost:8005/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "your_password"
  }'
```

Then provision a tenant:
```bash
# Replace YOUR_TOKEN with the JWT token from login
curl -X POST http://localhost:8005/api/hermes/tenants/provision \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "test-tenant-123",
    "tenant_name": "Test Tenant"
  }'
```

### 7. Test Web Search (via Hermes)
```bash
curl -X POST http://localhost:8005/api/hermes/search \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "test-tenant-123",
    "query": "Agentic CRM software",
    "max_results": 5
  }'
```

### 8. Check Execution Logs
```bash
# List executions for tenant
curl "http://localhost:8005/api/hermes/tenants/test-tenant-123/executions" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 9. Verify Guardrails
Test that blocked operations are rejected:
```bash
# This should fail (bash_execution is blocked)
curl -X POST http://localhost:8005/api/hermes/tasks/research \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "test-tenant-123",
    "task_type": "bash_execution",
    "context": {"command": "ls -la"}
  }'
# Expected: {"status": "blocked", "error": "Task type 'bash_execution' is not allowed"}
```

### 10. Check Tenant Isolation
```bash
# Get tenant status
curl http://localhost:8005/api/hermes/tenants/test-tenant-123/status \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get tenant skills (should be empty initially)
curl http://localhost:8005/api/hermes/tenants/test-tenant-123/skills \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Troubleshooting

### Hermes container won't start
```bash
# Check logs
docker compose logs hermes

# Common issues:
# - Missing environment variables
# - Port conflict (8010 already in use)
# - Database connection failed
```

### Database migration fails
```bash
# Check migration status
docker compose exec backend alembic current

# If needed, stamp and retry
docker compose exec backend alembic stamp d015e4203320
docker compose exec backend alembic upgrade head
```

### Backend can't connect to Hermes
```bash
# Check network connectivity
docker compose exec backend curl http://hermes:8000/health

# Verify backend config
docker compose exec backend env | grep HERMES
```

## Expected Results

After successful testing, you should see:
- [ ] Hermes container running on port 8010
- [ ] Database tables: `hermes_tenants`, `hermes_executions`, `hermes_skills`
- [ ] API endpoints responding at `/api/hermes/*`
- [ ] Guardrails blocking restricted operations
- [ ] Tenant isolation working (skills isolated per tenant)
- [ ] Execution logs stored in database

## Current Branch Status

Your changes are on branch: `codex/backend_refactor`

To merge to main:
```bash
# Commit changes
git add hermes/ backend/app/services/hermes_service.py backend/app/routes/hermes.py backend/app/models/hermes_tenant.py backend/migrations/versions/d015e4203321_add_hermes_agent_models.py HERMES_INTEGRATION.md
git commit -m "Add Hermes Agent SaaS integration with multi-tenant support"

# Merge to main
git checkout main
git merge codex/backend_refactor
git push origin main
```

**Note:** Other modified files (.env, docker-compose.yml, etc.) are on your current branch. The Hermes integration files are new and ready for testing.
