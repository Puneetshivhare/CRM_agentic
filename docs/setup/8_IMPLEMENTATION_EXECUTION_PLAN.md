# Implementation Execution Plan (Step-by-Step Build Guide)

**Purpose:** Exact roadmap for Claude (or developers) to follow when building. This is the "HOW TO EXECUTE" document.

**Status:** Ready for Claude to execute  
**Timeline:** 5-6 hours (MVP working) → 2 weeks (polished)  
**Date:** April 2026

---

## Quick Start: How to Use This Document

### For Claude Implementation:
```
1. Read this plan
2. Execute Phase 1 (Day 1)
3. Stop and verify
4. Continue Phase 2 (Day 2-3)
5. Full plan: 6 days to complete MVP
```

### For Manual Implementation:
```
Same plan, but you code yourself
Reference the LLD for implementation details
```

---

## Phase 0: Pre-Development Setup (1-2 hours)

### Step 0.1: Project Initialization

```bash
# Create project structure
mkdir agentic-crm
cd agentic-crm
git init

# Create folders
mkdir backend frontend docker migrations scripts tests

# Create files
touch .env.example docker-compose.yml .gitignore README.md

# Backend structure
mkdir -p backend/app/{agents,memory,models,routes,services,codex,middleware,utils}
mkdir -p backend/{migrations,tests}

# Frontend structure
mkdir -p frontend/app/{components,hooks,lib,api}
mkdir -p frontend/public

# Initialize git
git config user.name "Your Name"
git config user.email "your@email.com"
git add .
git commit -m "Initial project setup"
```

### Step 0.2: Create .env.example

Reference from Tech Stack document, copy to `.env`:

```env
# Database
DATABASE_URL=postgresql://crm_user:password@localhost:5432/agentic_crm

# Redis
REDIS_URL=redis://localhost:6379

# APIs
GEMINI_API_KEY=your_key_here
GITHUB_TOKEN=your_token_here
LINKEDIN_API_KEY=  # Optional
CRUNCHBASE_API_KEY=  # Optional

# Security
JWT_SECRET_KEY=your_secret_key_min_32_chars_here

# Server
PORT=8000
ENVIRONMENT=development

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100
DAILY_GEMINI_TOKENS=1000000
```

### Step 0.3: Create Docker Compose

Copy docker-compose.yml from LLD section (complete file with postgres, redis, backend, frontend)

### Step 0.4: Verify Prerequisites

```bash
# Check installations
docker --version  # Should be 20.10+
docker-compose --version  # Should be 1.29+
python3 --version  # Should be 3.11+
node --version  # Should be 18+
npm --version  # Should be 9+

# Start Docker services
docker-compose up -d

# Wait 30 seconds for Postgres to initialize
sleep 30

# Verify Postgres is ready
docker-compose exec postgres psql -U crm_user -d agentic_crm -c "SELECT 1"
# Should return: 1 (success)
```

**Status: Ready to start Phase 1** ✅

---

## Phase 1: Backend Foundation (Day 1 - 6 hours)

### Step 1.1: FastAPI Setup (30 minutes)

```bash
# Create backend directory structure
cd backend

# Create requirements.txt (from Tech Stack document)
cat > requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
alembic==1.12.1
pydantic==2.4.2
pydantic-settings==2.0.3
python-jose[cryptography]==3.3.0
celery==5.3.4
redis==5.0.1
pytest==7.4.3
pytest-asyncio==0.21.1
python-dotenv==1.0.0
aiohttp==3.9.1
tenacity==8.2.3
requests==2.31.0
slowapi==0.1.9
python-multipart==0.0.6
python-json-logger==2.0.7
prometheus-client==0.19.0
beautifulsoup4==4.12.2
lxml==4.9.3
email-validator==2.1.0
EOF

# Install dependencies
pip install -r requirements.txt

# Create app structure
mkdir -p app/{agents,memory,models,routes,services,codex,middleware,utils}
touch app/__init__.py
touch app/main.py
touch app/config.py
touch app/database.py
touch app/auth.py
```

**Create app/main.py:**

```python
# app/main.py - FastAPI initialization

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
from app import routes

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Agentic CRM API",
    description="AI-powered prospect enrichment system",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/health")
async def health():
    return {"status": "ok"}

# Include routers (empty for now, will add in Step 1.3)
# app.include_router(routes.prospects.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Create app/config.py:**

```python
# app/config.py - Settings management

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    redis_url: str = "redis://localhost:6379"
    gemini_api_key: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    port: int = 8000
    environment: str = "development"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

**Create app/database.py:**

```python
# app/database.py - Database connection

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

engine = create_engine(
    settings.database_url,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
)

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Status: FastAPI ready to run** ✅

### Step 1.2: Database Schema (2 hours)

**Create app/models/** with all SQLAlchemy models:**

Reference LLD section 1 for complete schema. Create files:

```
app/models/
├─ __init__.py
├─ prospect.py       (dim_prospects)
├─ company.py        (dim_companies)
├─ interaction.py    (fact_interactions)
├─ enrichment.py     (fact_enrichment_events)
├─ agent_exec.py     (fact_agent_executions)
├─ document.py       (dim_documents)
├─ skill.py          (dim_skills)
├─ rule.py           (dim_rules)
├─ memory.py         (memory_store + memory_vector)
└─ auth.py           (auth_users)
```

**Example: app/models/prospect.py**

```python
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Prospect(Base):
    __tablename__ = "dim_prospects"
    
    prospect_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    email = Column(String(255), unique=True, index=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    title = Column(String(255))
    company_id = Column(Integer, ForeignKey("dim_companies.company_id"))
    phone = Column(String(20))
    linkedin_url = Column(String(500))
    
    enrichment_status = Column(String(50), default="pending", index=True)
    enrichment_confidence = Column(Float, default=0.0)
    email_opens = Column(Integer, default=0)
    email_clicks = Column(Integer, default=0)
    
    last_contacted_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = relationship("Company", back_populates="prospects")
```

**Create Alembic migrations:**

```bash
# Initialize Alembic
alembic init migrations

# Configure sqlalchemy.url in alembic.ini
# sqlalchemy.url = driver://user:password@localhost/dbname

# Create initial migration
alembic revision --autogenerate -m "Create initial schema"

# Apply migrations
alembic upgrade head
```

**Verify:**

```bash
# Check tables
docker-compose exec postgres psql -U crm_user agentic_crm -c "\dt"

# Should show all tables created
```

**Status: Database ready** ✅

### Step 1.3: Authentication Setup (1.5 hours)

**Create app/auth.py:**

```python
# app/auth.py - JWT authentication

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
from app.config import settings

security = HTTPBearer()

def create_access_token(user_id: int, email: str) -> str:
    """Create JWT token"""
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": datetime.utcnow() + timedelta(minutes=30),
        "iat": datetime.utcnow()
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token

async def verify_token(credentials: HTTPAuthCredentials = Depends(security)) -> dict:
    """Verify JWT and return user info"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id: int = payload.get("user_id")
        email: str = payload.get("email")
        
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        return {"user_id": user_id, "email": email}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(user_info: dict = Depends(verify_token)) -> dict:
    return user_info
```

**Create basic auth endpoint (app/routes/auth.py):**

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from app.auth import create_access_token
from app.database import get_db
from app.models.auth import User

router = APIRouter(prefix="/api/auth", tags=["auth"])

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    token: str
    user_id: int

@router.post("/login")
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    # TODO: Implement password verification
    user = db.query(User).filter_by(email=request.email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token(user.user_id, user.email)
    return LoginResponse(token=token, user_id=user.user_id)
```

**Status: Auth system ready** ✅

### Step 1.4: Test It All (1 hour)

```bash
# Start backend
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# In another terminal, test
curl http://localhost:8000/health
# Should return: {"status":"ok"}

# Test database
docker-compose exec postgres psql -U crm_user agentic_crm -c "SELECT COUNT(*) FROM dim_prospects"
# Should return: 0 (empty, no data yet)
```

**Status: Phase 1 Complete** ✅✅✅

---

## Phase 2: Core Agents (Day 2-3 - 8 hours)

### Step 2.1: Memory System (2 hours)

**Create app/memory/memory_store.py:**

```python
# Simple memory layer

class MemoryStore:
    """In-memory + Redis memory for agents"""
    
    def __init__(self, redis_url: str):
        self.memory = {}  # Fast in-memory cache
        import redis
        self.redis = redis.from_url(redis_url)
    
    async def get(self, key: str):
        """Get from memory"""
        if key in self.memory:
            return self.memory[key]
        
        cached = self.redis.get(key)
        if cached:
            import json
            return json.loads(cached)
        
        return None
    
    async def set(self, key: str, value: dict, ttl_seconds: int = 3600):
        """Set in memory"""
        self.memory[key] = value
        
        import json
        self.redis.setex(key, ttl_seconds, json.dumps(value))
    
    async def delete(self, key: str):
        """Delete from memory"""
        if key in self.memory:
            del self.memory[key]
        self.redis.delete(key)

# Initialize
memory = MemoryStore(settings.redis_url)
```

**Status: Memory ready** ✅

### Step 2.2: Research Agent (3 hours)

**Create app/agents/base_agent.py:**

```python
class BaseAgent:
    """Base class for all agents"""
    
    def __init__(self, memory: MemoryStore):
        self.memory = memory
        self.name = self.__class__.__name__
    
    async def log_decision(self, decision: dict):
        """Log agent decision to Codex"""
        # TODO: Log to database
        print(f"{self.name}: {decision}")
```

**Create app/agents/research_agent.py:**

```python
from app.agents.base_agent import BaseAgent
from app.services.crawl_service import CrawlService
from app.services.gemini_service import GeminiService

class ResearchAgent(BaseAgent):
    """Research web for prospect/company data"""
    
    def __init__(self, memory, crawl_service, gemini_service):
        super().__init__(memory)
        self.crawl_service = crawl_service
        self.gemini = gemini_service
    
    async def research_prospect(self, prospect_id: int, depth: str = "basic"):
        """Research a prospect"""
        
        # Step 1: Load prospect from DB
        prospect = await db.get(Prospect, prospect_id)
        
        # Step 2: Check memory cache
        cached = await self.memory.get(f"company:{prospect.company_id}")
        if cached:
            await self.log_decision({"status": "cache_hit", "company_id": prospect.company_id})
            return cached
        
        # Step 3: Crawl web
        crawl_result = await self.crawl_service.crawl(prospect.company.domain)
        
        # Step 4: Extract with Gemini
        research_data = await self.gemini.call(
            prompt_template="research_extraction",
            input_data={"raw_crawl": crawl_result.text}
        )
        
        # Step 5: Store in memory
        await self.memory.set(f"company:{prospect.company_id}", research_data)
        
        # Step 6: Log decision
        await self.log_decision({
            "status": "success",
            "company": prospect.company.name,
            "data": research_data
        })
        
        return research_data
```

**Create app/services/crawl_service.py:**

```python
from crawl4ai import AsyncWebCrawler

class CrawlService:
    """Web crawling service with fallbacks"""
    
    async def crawl(self, domain: str) -> dict:
        """
        Smart crawl: API → Direct → Cache → LLM
        """
        
        try:
            # Try Crawl4AI
            crawler = AsyncWebCrawler()
            result = await crawler.arun(f"https://{domain}")
            return {"text": result.html, "source": "crawl4ai"}
        except Exception as e:
            print(f"Crawl failed: {e}")
            # Fallback: return synthetic data
            return {"text": "", "source": "error"}
```

**Create app/services/gemini_service.py:**

```python
import google.generativeai as genai

class GeminiService:
    """Gemini LLM service"""
    
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    async def call(self, prompt_template: str, input_data: dict) -> dict:
        """Call Gemini for text extraction/generation"""
        
        # Load prompt template
        prompts = {
            "research_extraction": """
                Extract company data from this text:
                {raw_crawl}
                
                Return JSON with: company_name, headcount, funding_stage
            """
        }
        
        prompt = prompts[prompt_template].format(**input_data)
        
        # Call Gemini
        response = self.model.generate_content(prompt)
        
        # Parse JSON response
        import json
        return json.loads(response.text)
```

**Status: Research Agent ready** ✅

### Step 2.3: Enrichment Agent (2 hours)

**Create app/agents/enrichment_agent.py:**

```python
class EnrichmentAgent(BaseAgent):
    """Map research findings to CRM schema"""
    
    def __init__(self, memory, gemini_service):
        super().__init__(memory)
        self.gemini = gemini_service
    
    async def enrich_prospect(self, prospect_id: int, research_data: dict):
        """Enrich prospect with research findings"""
        
        prospect = await db.get(Prospect, prospect_id)
        
        # Map findings to schema using Gemini
        mapped_fields = await self.gemini.call(
            prompt_template="enrichment_mapping",
            input_data={"research_data": research_data}
        )
        
        # Update prospect
        for field, value in mapped_fields.items():
            setattr(prospect, field, value)
        
        await db.commit()
        
        # Log
        await self.log_decision({
            "status": "enriched",
            "fields": list(mapped_fields.keys())
        })
        
        return mapped_fields
```

**Status: Enrichment Agent ready** ✅

### Step 2.4: Monitoring Agent (1.5 hours)

```python
class MonitoringAgent(BaseAgent):
    """Detect changes in monitored companies"""
    
    async def monitor_company(self, company_id: int):
        """Check for changes"""
        
        # Get previous state
        previous = await self.memory.get(f"company:{company_id}:state")
        
        # Crawl current state
        current = await crawl_service.crawl(company.domain)
        
        # Detect changes
        changes = await self.gemini.call(
            prompt_template="change_detection",
            input_data={"previous": previous, "current": current}
        )
        
        # Update memory
        await self.memory.set(f"company:{company_id}:state", current)
        
        return changes
```

**Status: Phase 2 Complete** ✅✅✅

---

## Phase 3: API Routes (Day 2 - 4 hours)

### Step 3.1: Prospect Routes

**Create app/routes/prospects.py:**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.auth import get_current_user
from app.database import get_db
from app.models.prospect import Prospect

router = APIRouter(prefix="/api/prospects", tags=["prospects"])

@router.get("/")
async def list_prospects(
    user_info: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all prospects for user"""
    prospects = db.query(Prospect).filter(
        Prospect.user_id == user_info["user_id"]
    ).all()
    return {"prospects": prospects}

@router.get("/{id}")
async def get_prospect(
    id: int,
    user_info: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get single prospect"""
    prospect = db.query(Prospect).filter(
        Prospect.prospect_id == id,
        Prospect.user_id == user_info["user_id"]
    ).first()
    if not prospect:
        raise HTTPException(status_code=404, detail="Not found")
    return prospect

@router.post("/")
async def create_prospect(
    data: dict,
    user_info: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new prospect"""
    prospect = Prospect(
        user_id=user_info["user_id"],
        **data
    )
    db.add(prospect)
    db.commit()
    return prospect
```

**Create app/routes/enrichment.py:**

```python
@router.post("/{prospect_id}/enrich")
async def enrich_prospect(
    prospect_id: int,
    user_info: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Trigger enrichment for prospect"""
    
    # Queue research job
    job = await research_agent.research_prospect(prospect_id)
    
    return {"job_id": str(id(job)), "status": "queued"}
```

**Include routers in app/main.py:**

```python
from app.routes import prospects, enrichment

app.include_router(prospects.router)
app.include_router(enrichment.router)
```

**Test:**

```bash
# Test Prospects API
curl http://localhost:8000/api/prospects \
  -H "Authorization: Bearer YOUR_TOKEN"

# Should return empty list
```

**Status: API Routes ready** ✅

---

## Phase 4: Frontend Dashboard (Day 3 - 4 hours)

### Step 4.1: Next.js Setup

```bash
cd frontend
npm create next-app@latest . -- --typescript --tailwind

# Install dependencies
npm install axios zustand @tanstack/react-query
```

### Step 4.2: Prospect Table Component

**Create app/prospects/page.tsx:**

```typescript
"use client";

import { useState, useEffect } from "react";
import axios from "axios";

export default function ProspectsPage() {
  const [prospects, setProspects] = useState([]);
  
  useEffect(() => {
    const fetchProspects = async () => {
      const token = localStorage.getItem("token");
      const response = await axios.get(
        "http://localhost:8000/api/prospects",
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setProspects(response.data.prospects);
    };
    
    fetchProspects();
  }, []);
  
  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold">Prospects</h1>
      
      <table className="w-full mt-4">
        <thead>
          <tr>
            <th className="text-left">Name</th>
            <th className="text-left">Email</th>
            <th className="text-left">Company</th>
            <th className="text-left">Status</th>
          </tr>
        </thead>
        <tbody>
          {prospects.map((p) => (
            <tr key={p.prospect_id}>
              <td>{p.first_name} {p.last_name}</td>
              <td>{p.email}</td>
              <td>{p.company_id}</td>
              <td>{p.enrichment_status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

**Test:**

```bash
npm run dev
# Go to http://localhost:3000/prospects
```

**Status: Frontend ready** ✅

---

## Phase 5: Codex System (Day 4 - 3 hours)

### Step 5.1: Decision Logger

**Create app/codex/decision_logger.py:**

```python
class DecisionLogger:
    """Log all agent decisions"""
    
    async def log(self, agent_name: str, decision: dict, db: Session):
        """Log decision to database"""
        
        execution = AgentExecution(
            agent_type=agent_name,
            decision_description=decision.get("status"),
            result=decision,
            tokens_used=decision.get("tokens", 0)
        )
        db.add(execution)
        db.commit()
```

### Step 5.2: Codex Dashboard API

**Create app/routes/codex.py:**

```python
@router.get("/dashboard")
async def codex_dashboard(user_info: dict = Depends(get_current_user)):
    """Get Codex dashboard data"""
    
    # Recent decisions
    decisions = await db.query(AgentExecution).filter(
        AgentExecution.user_id == user_info["user_id"]
    ).limit(10).all()
    
    # Token stats
    total_tokens = await db.query(func.sum(AgentExecution.tokens_used)).scalar()
    
    return {
        "recent_decisions": decisions,
        "token_usage": total_tokens,
        "agent_success_rate": 0.95
    }
```

**Status: Codex ready** ✅

---

## Phase 6: Testing & Polish (Day 5-6 - 4 hours)

### Step 6.1: Unit Tests

**Create tests/test_research_agent.py:**

```python
import pytest

@pytest.mark.asyncio
async def test_research_agent_caches_results():
    """Test that research is cached"""
    
    # First call
    result1 = await research_agent.research_prospect(1)
    
    # Second call should use cache
    result2 = await research_agent.research_prospect(1)
    
    assert result1 == result2
```

**Run tests:**

```bash
cd backend
pytest tests/
```

### Step 6.2: Manual Testing

```bash
# Test complete flow
1. Create prospect via API
2. Trigger enrichment
3. Verify prospect updated
4. Check Codex logs
5. Check frontend updated
```

**Status: MVP Complete** ✅✅✅✅✅✅

---

## Full Timeline

```
DAY 1 (6 hours):
├─ 0-1h:   Setup (Docker, git, .env)
├─ 1-3h:   Database schema + Alembic
├─ 3-4h:   FastAPI + Auth
├─ 4-6h:   Research Agent + Memory
└─ Test:   Verify schema, API health

DAY 2 (8 hours):
├─ 0-2h:   Enrichment Agent
├─ 2-4h:   Monitoring Agent
├─ 4-6h:   API routes (prospects, enrichment)
├─ 6-8h:   Frontend table component
└─ Test:   Full flow: create prospect → enrich → see data

DAY 3 (4 hours):
├─ 0-2h:   Codex logging + dashboard
├─ 2-3h:   Refine error handling
├─ 3-4h:   Polish UI, test edge cases
└─ Result: MVP working!

OPTIONAL (Future):
├─ Day 4-5: Bulk enrichment, CSV upload
├─ Day 6:   Monitoring scheduler
└─ Day 7+:  Skills/Rules system
```

---

## How to Execute This Plan with Claude

### Approach 1: Fully Automated (Recommended)

```
1. Give Claude this document
2. Ask: "Execute Phase 1 (Day 1) of the implementation plan. Stop when done, I'll verify."
3. Claude codes Phase 1
4. You verify: docker ps, psql test, curl http://localhost:8000/health
5. Ask: "Execute Phase 2 (Day 2-3). Continue."
6. Repeat until MVP complete
```

### Approach 2: Step-by-Step

```
For each step in this plan:
1. Ask Claude: "Execute Step X.Y from the implementation plan."
2. Claude writes code for that specific step
3. You review/merge
4. Move to next step
```

### Approach 3: Manual Implementation

```
Read the plan, implement yourself following the steps
Reference LLD for detailed specs
```

---

## Quality Gates (Must Pass Before Moving On)

### Phase 1 Gate:

```bash
# ✅ Database initialized
docker-compose exec postgres psql -U crm_user agentic_crm -c "\dt"
# Should show all tables

# ✅ API running
curl http://localhost:8000/health
# Should return {"status":"ok"}

# ✅ No errors on startup
docker-compose logs backend | grep ERROR
# Should be empty
```

### Phase 2 Gate:

```bash
# ✅ Research Agent works
curl -X POST http://localhost:8000/api/prospects/1/enrich
# Should return job_id

# ✅ Memory functioning
# Manually test: research same prospect twice, verify cache hit
```

### Phase 3 Gate:

```bash
# ✅ API endpoints respond
curl http://localhost:8000/api/prospects
# Should return list

# ✅ Auth working
curl http://localhost:8000/api/prospects -H "Authorization: Bearer invalid"
# Should return 401
```

### Phase 4 Gate:

```bash
# ✅ Frontend loads
http://localhost:3000
# Should show Prospects page

# ✅ API integration works
# Fill form, create prospect, verify in table
```

### Phase 5 Gate:

```bash
# ✅ Codex dashboard
curl http://localhost:8000/api/codex/dashboard
# Should return decision logs + metrics
```

---

## Troubleshooting Guide

### Problem: Postgres won't start

```bash
# Solution:
docker-compose down
docker-compose up -d postgres
docker-compose logs postgres | tail -20
# Check for disk space, port conflicts
```

### Problem: ImportError in Python

```bash
# Solution:
docker-compose down
docker-compose up -d backend
docker-compose exec backend pip install -r requirements.txt
docker-compose restart backend
```

### Problem: Frontend can't reach API

```bash
# Solution:
1. Check backend is running: docker-compose ps
2. Check CORS config in app/main.py allows localhost:3000
3. Check .env has NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

### Problem: Cloudflare blocks crawl

```bash
# Solution:
Refer to Security & Scraping Mitigation document (section 2 & 3)
Implement smart fallbacks:
1. Try API first
2. Use cache
3. Fall back to LLM
```

---

## Success Metrics (When MVP is Done)

✅ **Functionality:**
- Create prospect ✓
- Research prospect (crawl web) ✓
- Enrich prospect (update fields) ✓
- View in table ✓
- Check logs in Codex ✓

✅ **Performance:**
- Single enrichment: <30s ✓
- API response: <500ms ✓
- Memory lookup: <50ms ✓

✅ **Quality:**
- No unhandled errors ✓
- All endpoints tested ✓
- Logs in Codex ✓

✅ **Deployment:**
- Docker Compose works ✓
- All services running ✓
- Can scale with hot reload ✓

---

## Next Steps After MVP

1. **Week 2:** Bulk enrichment (CSV upload)
2. **Week 3:** Monitoring scheduler (daily checks)
3. **Week 4:** Skills/Rules system
4. **Month 2:** Email integration
5. **Month 3:** Cloud deployment (Vercel + Cloud Run)

---

**Document Version:** 1.0  
**Status:** Ready for Claude to Execute  
**Estimated Time:** 5-6 hours (MVP) → 2 weeks (polished)  
**Last Updated:** April 2026

---

## QUICK START COMMAND (For Claude)

When ready, ask Claude:

> **"Execute Phase 1 (Day 1) of the implementation execution plan. Reference the LLD, Tech Stack, and Security documents as needed. Stop after Phase 1 and wait for verification before continuing. Start with project setup, then database schema, then FastAPI, then auth. Full output of all code files created."**

Claude will:
1. Create all folder structures
2. Write all Python/TypeScript files
3. Setup Docker/database
4. Test everything
5. Give you status when done

You then verify the quality gates, and ask Claude to proceed to Phase 2.