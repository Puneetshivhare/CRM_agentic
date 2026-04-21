import sys
import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import random
from faker import Faker
from dotenv import load_dotenv

# Add backend root to sys.path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine, Base
from app.models.auth import AuthUser
from app.models.company import Company
from app.models.prospect import Prospect
from app.models.agent_execution import AgentExecution
from app.auth import hash_password

# Load environment variables from root .env
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env'))

fake = Faker()

def seed_database():
    db = SessionLocal()
    try:
        print("🚀 Starting database seeding...")

        # 1. Clear existing data
        print("🧹 Wiping existing data...")
        db.query(AgentExecution).delete()
        db.query(Prospect).delete()
        db.query(Company).delete()
        db.query(AuthUser).delete()
        db.commit()

        # 2. Create Admin User
        print("👤 Creating admin user...")
        admin = AuthUser(
            email="admin@example.com",
            password_hash=hash_password("admin123")
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        user_id = admin.user_id

        # 3. Create Companies (15)
        print("🏢 Seeding companies...")
        companies = []
        industries = ["SaaS", "FinTech", "HealthTech", "E-commerce", "AI/ML", "Cybersecurity", "Logistics", "EdTech"]
        funding_stages = ["seed", "series_a", "series_b", "series_c", "ipo", "bootstrapped"]
        
        for _ in range(15):
            company_name = fake.company()
            domain = company_name.lower().replace(" ", "").replace(",", "").replace("-", "") + ".com"
            company = Company(
                user_id=user_id,
                name=company_name,
                domain=domain,
                description=fake.catch_phrase(),
                headcount=random.randint(10, 5000),
                industry=random.choice(industries),
                funding_stage=random.choice(funding_stages),
                headquarters_city=fake.city(),
                headquarters_country=fake.country(),
                tech_stack=["React", "Python", "AWS", "Next.js", "PostgreSQL", "Docker"][:random.randint(2, 6)],
                monitoring_enabled=True
            )
            db.add(company)
            companies.append(company)
        
        db.commit()

        # 4. Create Prospects (20)
        print("👨‍💼 Seeding prospects...")
        status_options = ["enriched", "pending", "failed"]
        for i in range(20):
            company = random.choice(companies)
            status = random.choices(status_options, weights=[0.6, 0.2, 0.2])[0]
            prospect = Prospect(
                user_id=user_id,
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                email=fake.email(),
                title=fake.job(),
                company_id=company.company_id,
                enrichment_status=status,
                enrichment_confidence=random.uniform(0.7, 0.99) if status == "enriched" else 0.0,
                location=f"{fake.city()}, {fake.country()}"
            )
            db.add(prospect)
        
        db.commit()

        # 5. Create Agent Executions (10)
        print("🤖 Seeding agent analytics...")
        agent_types = ["ResearchAgent", "EnrichmentAgent", "MonitoringAgent"]
        execution_statuses = ["success", "failed", "running"]
        
        for _ in range(10):
            start = datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 48))
            duration = random.randint(500, 5000)
            status = random.choice(execution_statuses)
            
            execution = AgentExecution(
                user_id=user_id,
                agent_type=random.choice(agent_types),
                task_id=fake.uuid4(),
                status=status,
                start_time=start,
                end_time=start + timedelta(milliseconds=duration) if status != "running" else None,
                duration_ms=duration if status != "running" else None,
                tokens_used=random.randint(1000, 50000),
                decision_description=fake.sentence(),
                confidence_score=random.uniform(0.7, 1.0)
            )
            db.add(execution)
        
        db.commit()

        print("✅ Seeding completed successfully!")
        print(f"Summary: 1 Admin, 15 Companies, 20 Prospects, 10 Executions")

    except Exception as e:
        db.rollback()
        print(f"❌ Error during seeding: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
