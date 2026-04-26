#!/bin/bash
# test_hermes_integration.sh — Test script for Hermes Agent integration

set -e

echo "=========================================="
echo "Hermes Agent Integration Test Suite"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
API_BASE="http://localhost:8005/api"
HERMES_BASE="http://localhost:8010"
TOKEN=""  # Will need to get from login

# Helper functions
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Test 1: Docker Compose
echo "Test 1: Checking Docker Compose..."
if docker compose ps &>/dev/null; then
    print_success "Docker Compose is running"
else
    print_error "Docker Compose not running. Start with: docker compose up -d"
    exit 1
fi

# Test 2: Hermes Container Health
echo ""
echo "Test 2: Hermes Container Health..."
if curl -s -f "${HERMES_BASE}/health" &>/dev/null; then
    print_success "Hermes container is healthy"
    HERMES_HEALTH=$(curl -s "${HERMES_BASE}/health")
    print_info "Hermes status: $(echo $HERMES_HEALTH | python -c "import sys,json; print(json.load(sys.stdin)['status'])")"
else
    print_error "Hermes container not healthy. Check logs: docker compose logs hermes"
fi

# Test 3: Database Migration
echo ""
echo "Test 3: Database Migration..."
if docker compose exec -T postgres psql -U crm_user -d agentic_crm -c "SELECT table_name FROM information_schema.tables WHERE table_name LIKE 'hermes_%'" 2>/dev/null | grep -q "hermes_tenants"; then
    print_success "Hermes tables exist in database"
else
    print_error "Hermes tables not found. Run migration: docker compose exec backend alembic upgrade head"
fi

# Test 4: Backend API Health
echo ""
echo "Test 4: Backend API Health..."
if curl -s -f "${API_BASE}/health" &>/dev/null; then
    print_success "Backend API is healthy"
else
    print_error "Backend API not responding"
fi

# Test 5: Hermes Routes Available
echo ""
echo "Test 5: Hermes Routes Available..."
if curl -s -f "${API_BASE}/hermes/health" &>/dev/null || curl -s "${API_BASE}/docs" | grep -q "hermes"; then
    print_success "Hermes routes are registered"
else
    print_error "Hermes routes not found in API"
fi

# Test 6: Create Test Tenant (requires auth token)
echo ""
echo "Test 6: Tenant Provisioning (requires authentication)..."
echo "  To test tenant provisioning:"
echo "  1. Login via frontend or API: POST ${API_BASE}/auth/login"
echo "  2. Get JWT token from response"
echo "  3. Run:"
echo "     curl -X POST ${API_BASE}/hermes/tenants/provision \\"
echo "       -H 'Authorization: Bearer YOUR_TOKEN' \\"
echo "       -H 'Content-Type: application/json' \\"
echo "       -d '{\"tenant_id\": \"test-tenant\", \"tenant_name\": \"Test Tenant\"}'"

# Test 7: Guardrails Configuration
echo ""
echo "Test 7: Guardrails Configuration..."
if [ -f "hermes/guardrails.yml" ]; then
    print_success "Guardrails configuration exists"
    ALLOWED=$(grep -c "allowed_actions:" hermes/guardrails.yml || echo "0")
    BLOCKED=$(grep -c "blocked_actions:" hermes/guardrails.yml || echo "0")
    print_info "Allowed actions defined: $ALLOWED"
    print_info "Blocked actions defined: $BLOCKED"
else
    print_error "Guardrails configuration not found"
fi

# Test 8: Service Files
echo ""
echo "Test 8: Service Files..."
REQUIRED_FILES=(
    "backend/app/services/hermes_service.py"
    "backend/app/routes/hermes.py"
    "backend/app/models/hermes_tenant.py"
    "hermes/Dockerfile"
    "hermes/guardrails.yml"
    "hermes/hermes_app/main.py"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        print_success "File exists: $file"
    else
        print_error "Missing file: $file"
    fi
done

# Test 9: Docker Compose Configuration
echo ""
echo "Test 9: Docker Compose Configuration..."
if grep -q "agentic-crm-hermes" docker-compose.yml; then
    print_success "Hermes service defined in docker-compose.yml"
else
    print_error "Hermes service not found in docker-compose.yml"
fi

if grep -q "HERMES_MODE" docker-compose.yml; then
    print_success "Hermes environment variables configured"
else
    print_error "Hermes environment variables missing"
fi

# Summary
echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo ""
echo "To complete testing:"
echo ""
echo "1. Ensure Docker Desktop is running"
echo "2. Start services:"
echo "   docker compose up -d hermes"
echo ""
echo "3. Run database migration:"
echo "   docker compose exec backend alembic upgrade head"
echo ""
echo "4. Test via API:"
echo "   curl ${HERMES_BASE}/health"
echo "   curl ${API_BASE}/hermes/tenants/{tenant_id}/status"
echo ""
echo "5. Test tenant provisioning (after login):"
echo "   curl -X POST ${API_BASE}/hermes/tenants/provision \\"
echo "     -H 'Authorization: Bearer TOKEN' \\"
echo "     -d '{\"tenant_id\": \"test\", \"tenant_name\": \"Test\"}'"
echo ""
echo "=========================================="
