"""Seed Supabase-backed tables with realistic demo CRM data.

Web-grounded references used for company and leadership inspiration:
  - Atlassian investor relations and executive management
  - Datadog leadership page
  - GitLab company and executive group pages
  - Box leadership page
  - Zoom about and leadership pages
  - Vercel about page
  - Supabase homepage
"""

from __future__ import annotations

import os
import random
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from sqlalchemy import or_

from dotenv import load_dotenv
from faker import Faker
from sqlalchemy import delete

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.auth import hash_password
from app.database import SessionLocal
from app.models.agent_execution import AgentExecution
from app.models.auth import AuthUser
from app.models.campaign import Campaign
from app.models.company import Company
from app.models.document import Document
from app.models.enrichment_event import EnrichmentEvent
from app.models.interaction import Interaction
from app.models.lead_score import LeadScore
from app.models.memory import MemoryStore, MemoryVector
from app.models.prospect import Prospect
from app.models.rule import Rule
from app.models.rule_execution import RuleExecution
from app.models.skill import Skill
from app.utils.logger import configure_logging, trace_logic

import logging


load_dotenv(
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        ".env",
    )
)

fake = Faker()
random.seed(42)
Faker.seed(42)
logger = logging.getLogger("agentic_crm")

SEED_DOMAIN = "agenticcrm.test"
LEGACY_SEED_DOMAIN = "agenticcrm.local"
DEMO_EMAIL = f"demo@{SEED_DOMAIN}"
DEMO_PASSWORD = "DemoPass123!"
TARGET_USER_EMAIL = os.getenv("SEED_TARGET_EMAIL")

USER_COUNT = 30
COMPANY_COUNT = 30
PROSPECT_COUNT = 45
DOCUMENT_COUNT = 30
SKILL_COUNT = 30
CAMPAIGN_COUNT = 30
RULE_COUNT = 30
INTERACTION_COUNT = 45
LEAD_SCORE_COUNT = 45
AGENT_EXECUTION_COUNT = 45
ENRICHMENT_EVENT_COUNT = 45
RULE_EXECUTION_COUNT = 30
MEMORY_STORE_COUNT = 30
MEMORY_VECTOR_COUNT = 30

COMPANY_CATALOG = [
    {
        "name": "Atlassian",
        "domain": "atlassian.com",
        "description": "AI-powered team collaboration, software development, and service management tools.",
        "industry": "Collaboration Software",
        "funding_stage": "ipo",
        "city": "Sydney",
        "country": "Australia",
        "headcount": 12000,
        "tech_stack": ["Java", "Kotlin", "AWS", "PostgreSQL", "React"],
    },
    {
        "name": "Datadog",
        "domain": "datadoghq.com",
        "description": "Observability and security platform for cloud applications and infrastructure.",
        "industry": "Observability",
        "funding_stage": "ipo",
        "city": "New York",
        "country": "United States",
        "headcount": 6500,
        "tech_stack": ["Go", "Python", "Kubernetes", "Kafka", "TypeScript"],
    },
    {
        "name": "GitLab",
        "domain": "gitlab.com",
        "description": "DevSecOps platform spanning planning, code, security, and deployment workflows.",
        "industry": "DevSecOps",
        "funding_stage": "ipo",
        "city": "San Francisco",
        "country": "United States",
        "headcount": 2500,
        "tech_stack": ["Ruby", "Go", "Vue", "PostgreSQL", "GCP"],
    },
    {
        "name": "Box",
        "domain": "box.com",
        "description": "Content cloud platform for secure file sharing, workflow, and enterprise collaboration.",
        "industry": "Content Management",
        "funding_stage": "ipo",
        "city": "Redwood City",
        "country": "United States",
        "headcount": 2500,
        "tech_stack": ["Java", "Node.js", "MySQL", "GCP", "React"],
    },
    {
        "name": "Zoom",
        "domain": "zoom.com",
        "description": "AI-first work platform for human connection, meetings, chat, phone, and contact center.",
        "industry": "Unified Communications",
        "funding_stage": "ipo",
        "city": "San Jose",
        "country": "United States",
        "headcount": 7500,
        "tech_stack": ["C++", "Python", "Go", "AWS", "Redis"],
    },
    {
        "name": "Vercel",
        "domain": "vercel.com",
        "description": "Frontend cloud platform to build, scale, and secure modern web experiences.",
        "industry": "Developer Platform",
        "funding_stage": "series_f",
        "city": "San Francisco",
        "country": "United States",
        "headcount": 800,
        "tech_stack": ["TypeScript", "Next.js", "Rust", "AWS", "PostgreSQL"],
    },
    {
        "name": "Supabase",
        "domain": "supabase.com",
        "description": "Postgres development platform with database, auth, realtime, storage, and vector features.",
        "industry": "Developer Platform",
        "funding_stage": "series_c",
        "city": "Singapore",
        "country": "Singapore",
        "headcount": 300,
        "tech_stack": ["PostgreSQL", "TypeScript", "Deno", "Kubernetes", "Elixir"],
    },
    {
        "name": "Stripe",
        "domain": "stripe.com",
        "description": "Financial infrastructure platform for payments, billing, and money movement.",
        "industry": "FinTech",
        "funding_stage": "series_h",
        "city": "South San Francisco",
        "country": "United States",
        "headcount": 8000,
        "tech_stack": ["Ruby", "Scala", "Kubernetes", "AWS", "PostgreSQL"],
    },
    {
        "name": "Figma",
        "domain": "figma.com",
        "description": "Collaborative design and product development platform for teams.",
        "industry": "Design Software",
        "funding_stage": "ipo",
        "city": "San Francisco",
        "country": "United States",
        "headcount": 1500,
        "tech_stack": ["TypeScript", "WebAssembly", "C++", "AWS", "GraphQL"],
    },
    {
        "name": "Notion",
        "domain": "notion.so",
        "description": "Connected workspace for docs, projects, and knowledge management.",
        "industry": "Productivity Software",
        "funding_stage": "series_c",
        "city": "San Francisco",
        "country": "United States",
        "headcount": 1200,
        "tech_stack": ["TypeScript", "Kotlin", "PostgreSQL", "AWS", "Redis"],
    },
    {
        "name": "Airtable",
        "domain": "airtable.com",
        "description": "App platform that blends database structure with collaborative workflows.",
        "industry": "No-Code Platform",
        "funding_stage": "series_f",
        "city": "San Francisco",
        "country": "United States",
        "headcount": 1500,
        "tech_stack": ["TypeScript", "React", "MySQL", "AWS", "Go"],
    },
    {
        "name": "Plaid",
        "domain": "plaid.com",
        "description": "Data network powering account connectivity and fintech experiences.",
        "industry": "FinTech",
        "funding_stage": "series_d",
        "city": "San Francisco",
        "country": "United States",
        "headcount": 1200,
        "tech_stack": ["Go", "Java", "PostgreSQL", "Kubernetes", "React"],
    },
    {
        "name": "Twilio",
        "domain": "twilio.com",
        "description": "Customer engagement platform for messaging, voice, email, and data.",
        "industry": "Communications API",
        "funding_stage": "ipo",
        "city": "San Francisco",
        "country": "United States",
        "headcount": 6500,
        "tech_stack": ["Java", "Python", "AWS", "Kafka", "React"],
    },
    {
        "name": "Snowflake",
        "domain": "snowflake.com",
        "description": "Cloud data platform for analytics, applications, and AI workloads.",
        "industry": "Data Platform",
        "funding_stage": "ipo",
        "city": "Bozeman",
        "country": "United States",
        "headcount": 7500,
        "tech_stack": ["Java", "Scala", "AWS", "Azure", "GCP"],
    },
    {
        "name": "MongoDB",
        "domain": "mongodb.com",
        "description": "Developer data platform built around the MongoDB database and Atlas cloud service.",
        "industry": "Database",
        "funding_stage": "ipo",
        "city": "New York",
        "country": "United States",
        "headcount": 5000,
        "tech_stack": ["C++", "Go", "Kubernetes", "AWS", "Node.js"],
    },
    {
        "name": "Confluent",
        "domain": "confluent.io",
        "description": "Data streaming platform built around Apache Kafka for real-time systems.",
        "industry": "Data Infrastructure",
        "funding_stage": "ipo",
        "city": "Mountain View",
        "country": "United States",
        "headcount": 3000,
        "tech_stack": ["Java", "Kafka", "Kubernetes", "AWS", "TypeScript"],
    },
    {
        "name": "HashiCorp",
        "domain": "hashicorp.com",
        "description": "Cloud infrastructure automation tools for provisioning, security, and networking.",
        "industry": "Cloud Infrastructure",
        "funding_stage": "ipo",
        "city": "San Francisco",
        "country": "United States",
        "headcount": 2200,
        "tech_stack": ["Go", "Terraform", "Vault", "AWS", "React"],
    },
    {
        "name": "HubSpot",
        "domain": "hubspot.com",
        "description": "CRM platform for marketing, sales, service, content, and operations teams.",
        "industry": "CRM",
        "funding_stage": "ipo",
        "city": "Cambridge",
        "country": "United States",
        "headcount": 8000,
        "tech_stack": ["Java", "HubL", "AWS", "MySQL", "React"],
    },
    {
        "name": "Retool",
        "domain": "retool.com",
        "description": "Internal tools platform for building operations software quickly.",
        "industry": "Developer Platform",
        "funding_stage": "series_c",
        "city": "San Francisco",
        "country": "United States",
        "headcount": 400,
        "tech_stack": ["TypeScript", "React", "PostgreSQL", "Kubernetes", "Node.js"],
    },
    {
        "name": "Linear",
        "domain": "linear.app",
        "description": "Issue tracking and product planning system for modern software teams.",
        "industry": "Product Management",
        "funding_stage": "series_b",
        "city": "San Francisco",
        "country": "United States",
        "headcount": 150,
        "tech_stack": ["TypeScript", "GraphQL", "PostgreSQL", "Vercel", "React"],
    },
    {
        "name": "Sentry",
        "domain": "sentry.io",
        "description": "Application monitoring and developer workflow platform for debugging and performance.",
        "industry": "Observability",
        "funding_stage": "series_e",
        "city": "San Francisco",
        "country": "United States",
        "headcount": 800,
        "tech_stack": ["Python", "Kafka", "ClickHouse", "React", "AWS"],
    },
    {
        "name": "Miro",
        "domain": "miro.com",
        "description": "Collaborative visual workspace for brainstorming, planning, and workshops.",
        "industry": "Collaboration Software",
        "funding_stage": "series_c",
        "city": "Amsterdam",
        "country": "Netherlands",
        "headcount": 1700,
        "tech_stack": ["TypeScript", "React", "Java", "AWS", "MySQL"],
    },
    {
        "name": "Asana",
        "domain": "asana.com",
        "description": "Work management platform for planning, coordination, and execution.",
        "industry": "Work Management",
        "funding_stage": "ipo",
        "city": "San Francisco",
        "country": "United States",
        "headcount": 1800,
        "tech_stack": ["TypeScript", "React", "Scala", "AWS", "MySQL"],
    },
    {
        "name": "Intercom",
        "domain": "intercom.com",
        "description": "Customer communications platform for support, onboarding, and engagement.",
        "industry": "Customer Support",
        "funding_stage": "series_d",
        "city": "Dublin",
        "country": "Ireland",
        "headcount": 1200,
        "tech_stack": ["Ruby", "React", "AWS", "Kafka", "PostgreSQL"],
    },
    {
        "name": "Zapier",
        "domain": "zapier.com",
        "description": "Automation platform connecting apps and workflows without code.",
        "industry": "Automation",
        "funding_stage": "series_c",
        "city": "Remote",
        "country": "United States",
        "headcount": 800,
        "tech_stack": ["Python", "Django", "PostgreSQL", "AWS", "React"],
    },
    {
        "name": "Postman",
        "domain": "postman.com",
        "description": "API platform for design, testing, collaboration, and governance.",
        "industry": "Developer Tools",
        "funding_stage": "series_d",
        "city": "San Francisco",
        "country": "United States",
        "headcount": 900,
        "tech_stack": ["Node.js", "React", "PostgreSQL", "AWS", "GraphQL"],
    },
    {
        "name": "Algolia",
        "domain": "algolia.com",
        "description": "Search and discovery platform for fast, relevant digital experiences.",
        "industry": "Search Infrastructure",
        "funding_stage": "series_d",
        "city": "San Francisco",
        "country": "United States",
        "headcount": 700,
        "tech_stack": ["C++", "Go", "Kubernetes", "AWS", "React"],
    },
    {
        "name": "Segment",
        "domain": "segment.com",
        "description": "Customer data platform for collecting, unifying, and activating customer signals.",
        "industry": "Customer Data Platform",
        "funding_stage": "acquired",
        "city": "San Francisco",
        "country": "United States",
        "headcount": 1000,
        "tech_stack": ["Go", "TypeScript", "Kafka", "AWS", "PostgreSQL"],
    },
    {
        "name": "Mural",
        "domain": "mural.co",
        "description": "Visual collaboration platform for distributed teamwork and facilitation.",
        "industry": "Collaboration Software",
        "funding_stage": "series_c",
        "city": "San Francisco",
        "country": "United States",
        "headcount": 700,
        "tech_stack": ["TypeScript", "React", "Node.js", "AWS", "Redis"],
    },
    {
        "name": "Coda",
        "domain": "coda.io",
        "description": "Docs-as-apps platform combining documents, data, and automations.",
        "industry": "Productivity Software",
        "funding_stage": "series_c",
        "city": "San Francisco",
        "country": "United States",
        "headcount": 300,
        "tech_stack": ["TypeScript", "React", "PostgreSQL", "AWS", "GraphQL"],
    },
]

PUBLIC_EXECUTIVES = [
    ("Datadog", "Olivier", "Pomel", "Chief Executive Officer"),
    ("Datadog", "Alexis", "Le-Quoc", "Chief Technology Officer"),
    ("Datadog", "David", "Obstler", "Chief Financial Officer"),
    ("Datadog", "Yanbing", "Li", "Chief Product Officer"),
    ("Datadog", "Sean", "Walters", "Chief Revenue Officer"),
    ("Datadog", "Emilio", "Escobar", "Chief Information Security Officer"),
    ("Datadog", "Kerry", "Acocella", "General Counsel"),
    ("Atlassian", "Mike", "Cannon-Brookes", "Chief Executive Officer"),
    ("Atlassian", "Amy", "Glancey", "Chief of Staff"),
    ("Atlassian", "Avani", "Prabhakar", "Chief People and AI Enablement Officer"),
    ("Atlassian", "Brian", "Duffy", "Chief Revenue Officer"),
    ("Atlassian", "James", "Chuong", "Chief Financial Officer"),
    ("Atlassian", "Stan", "Shepard", "General Counsel"),
    ("Atlassian", "Tamar", "Yehoshua", "Chief Product and AI Officer"),
    ("Atlassian", "Vikram", "Rao", "CTO Enterprise, Chief Trust Officer"),
    ("GitLab", "Bill", "Staples", "Chief Executive Officer"),
    ("GitLab", "Jessica", "Ross", "Chief Financial Officer"),
    ("GitLab", "Ian", "Steward", "Chief Revenue Officer"),
    ("GitLab", "Manav", "Khurana", "Chief Product and Marketing Officer"),
    ("GitLab", "Siva", "Padisetty", "Chief Technology Officer"),
    ("GitLab", "Manu", "Narayan", "Chief Information Officer"),
    ("GitLab", "Josh", "Lemos", "Chief Information Security Officer"),
    ("GitLab", "Robin", "Schulman", "Chief Legal Officer"),
    ("GitLab", "Rob", "Allen", "Chief People Officer"),
    ("Box", "Aaron", "Levie", "Chief Executive Officer"),
    ("Box", "Dylan", "Smith", "Chief Financial Officer"),
    ("Box", "Olivia", "Nottebohm", "Chief Operating Officer"),
    ("Box", "Tricia", "Gellman", "Chief Marketing Officer"),
    ("Box", "Jon", "Herstein", "Chief Customer Officer"),
    ("Box", "David", "Leeb", "Chief Legal Officer"),
    ("Box", "Jeff", "Nuzum", "Chief Revenue Officer"),
    ("Box", "Jessica", "Swank", "Chief People Officer"),
    ("Box", "Diego", "Dugatkin", "Chief Product Officer"),
    ("Box", "Ben", "Kus", "Chief Technology Officer"),
    ("Zoom", "Eric", "Yuan", "Founder and Chief Executive Officer"),
]

RULE_TEMPLATES = [
    ("High-intent enrichment follow-up", "enrichment_complete", "workflow"),
    ("Executive visit monitoring", "signal_detected", "trigger"),
    ("Lead score acceleration", "lead_score_high", "data"),
    ("Inactive prospect re-engagement", "prospect_stale", "workflow"),
    ("Funding news outreach", "company_funding_update", "trigger"),
]

CAMPAIGN_TEMPLATES = [
    "Executive intro sequence",
    "Product-led growth outreach",
    "Platform migration campaign",
    "Security modernization nurture",
    "QBR expansion program",
]

SKILL_TYPES = ["research", "outreach", "monitoring", "custom"]
INTERACTION_TYPES = ["email", "call", "meeting", "linkedin_message"]
AGENT_TYPES = ["ResearchAgent", "EnrichmentAgent", "MonitoringAgent"]


def slugify(value: str) -> str:
    return (
        value.lower()
        .replace("&", "and")
        .replace(",", "")
        .replace(".", "")
        .replace("/", "-")
        .replace(" ", "-")
    )


def make_seed_emails() -> list[str]:
    emails = [DEMO_EMAIL]
    emails.extend(f"seed.user{index:02d}@{SEED_DOMAIN}" for index in range(1, USER_COUNT))
    return emails


def resolve_target_user(db) -> AuthUser | None:
    query = (
        db.query(AuthUser)
        .filter(~AuthUser.email.like(f"%@{SEED_DOMAIN}"))
        .filter(~AuthUser.email.like(f"%@{LEGACY_SEED_DOMAIN}"))
        .filter(~AuthUser.email.like("seed.user%@%"))
        .filter(~AuthUser.email.like("demo@%"))
    )

    if TARGET_USER_EMAIL:
        return query.filter(AuthUser.email == TARGET_USER_EMAIL).first()

    return (
        query
        .filter(~AuthUser.email.like("codex.frontend.%"))
        .order_by(AuthUser.updated_at.desc(), AuthUser.created_at.desc())
        .first()
    )


def cleanup_existing_seed_data(db) -> None:
    seed_users = (
        db.query(AuthUser)
        .filter(
            or_(
                AuthUser.email.like(f"%@{SEED_DOMAIN}"),
                AuthUser.email.like(f"%@{LEGACY_SEED_DOMAIN}"),
                AuthUser.email.like("seed.user%@%"),
                AuthUser.email.like("demo@%"),
            )
        )
        .all()
    )
    if not seed_users:
        return

    user_ids = [user.user_id for user in seed_users]
    prospect_ids = [
        prospect_id
        for (prospect_id,) in db.query(Prospect.prospect_id).filter(Prospect.user_id.in_(user_ids)).all()
    ]

    trace_logic(logger, "seed.cleanup.start", user_count=len(user_ids), prospect_count=len(prospect_ids))

    if prospect_ids:
        db.execute(delete(EnrichmentEvent).where(EnrichmentEvent.prospect_id.in_(prospect_ids)))
        db.execute(delete(Interaction).where(Interaction.prospect_id.in_(prospect_ids)))
        db.execute(delete(LeadScore).where(LeadScore.prospect_id.in_(prospect_ids)))

    db.execute(delete(RuleExecution).where(RuleExecution.user_id.in_(user_ids)))
    db.execute(delete(AgentExecution).where(AgentExecution.user_id.in_(user_ids)))
    db.execute(delete(MemoryVector).where(MemoryVector.user_id.in_(user_ids)))
    db.execute(delete(MemoryStore).where(MemoryStore.memory_key.like("seed:%")))
    db.execute(delete(Campaign).where(Campaign.user_id.in_(user_ids)))
    db.execute(delete(Rule).where(Rule.user_id.in_(user_ids)))
    db.execute(delete(Document).where(Document.user_id.in_(user_ids)))
    db.execute(delete(Skill).where(Skill.user_id.in_(user_ids)))
    db.execute(delete(Prospect).where(Prospect.user_id.in_(user_ids)))
    db.execute(delete(Company).where(Company.user_id.in_(user_ids)))
    db.execute(delete(AuthUser).where(AuthUser.user_id.in_(user_ids)))
    db.commit()


def create_users(db) -> tuple[AuthUser, list[AuthUser]]:
    users = []
    for index, email in enumerate(make_seed_emails()):
        password = DEMO_PASSWORD if index == 0 else f"SeedPass{index:02d}!"
        user = AuthUser(email=email, password_hash=hash_password(password))
        db.add(user)
        users.append(user)

    db.commit()
    for user in users:
        db.refresh(user)

    demo_user = users[0]
    trace_logic(logger, "seed.users.created", count=len(users), demo_user_id=demo_user.user_id)
    return demo_user, users


def create_companies(db, demo_user: AuthUser) -> list[Company]:
    companies = []
    for index, company_data in enumerate(COMPANY_CATALOG[:COMPANY_COUNT], start=1):
        company = Company(
            user_id=demo_user.user_id,
            name=company_data["name"],
            domain=company_data["domain"],
            description=company_data["description"],
            headcount=company_data["headcount"],
            headcount_range=f"{max(10, company_data['headcount'] - 200)}-{company_data['headcount'] + 200}",
            revenue_annual=company_data["headcount"] * random.randint(90000, 180000),
            funding_stage=company_data["funding_stage"],
            headquarters_city=company_data["city"],
            headquarters_country=company_data["country"],
            industry=company_data["industry"],
            tech_stack=company_data["tech_stack"],
            monitoring_enabled=(index % 3 != 0),
        )
        db.add(company)
        companies.append(company)

    db.commit()
    for company in companies:
        db.refresh(company)

    trace_logic(logger, "seed.companies.created", count=len(companies))
    return companies


def build_exec_email(first_name: str, last_name: str, domain: str) -> str:
    local = f"{slugify(first_name)}.{slugify(last_name)}"
    return f"{local}@{domain}"


def create_prospects(db, demo_user: AuthUser, companies: list[Company]) -> list[Prospect]:
    companies_by_name = {company.name: company for company in companies}
    prospects: list[Prospect] = []

    for company_name, first_name, last_name, title in PUBLIC_EXECUTIVES:
        company = companies_by_name[company_name]
        prospect = Prospect(
            user_id=demo_user.user_id,
            company_id=company.company_id,
            email=build_exec_email(first_name, last_name, company.domain),
            first_name=first_name,
            last_name=last_name,
            title=title,
            phone=fake.numerify(text="+1-###-###-####"),
            location=f"{company.headquarters_city}, {company.headquarters_country}",
            linkedin_url=f"https://www.linkedin.com/in/{slugify(first_name)}-{slugify(last_name)}",
            website_url=f"https://{company.domain}",
            enrichment_status=random.choice(["enriched", "pending", "enriching"]),
            enrichment_confidence=round(random.uniform(0.62, 0.97), 2),
            email_opens=random.randint(0, 9),
            email_clicks=random.randint(0, 4),
            last_contacted_at=datetime.utcnow() - timedelta(days=random.randint(1, 45)),
        )
        db.add(prospect)
        prospects.append(prospect)

    while len(prospects) < PROSPECT_COUNT:
        company = random.choice(companies)
        first_name = fake.first_name()
        last_name = fake.last_name()
        prospect = Prospect(
            user_id=demo_user.user_id,
            company_id=company.company_id,
            email=build_exec_email(first_name, last_name, company.domain),
            first_name=first_name,
            last_name=last_name,
            title=random.choice(
                [
                    "VP Revenue Operations",
                    "Director of Platform Engineering",
                    "Head of Security Operations",
                    "Senior Product Manager",
                    "Chief of Staff",
                    "Director of Customer Success",
                    "Principal Solutions Architect",
                ]
            ),
            phone=fake.numerify(text="+1-###-###-####"),
            location=f"{company.headquarters_city}, {company.headquarters_country}",
            linkedin_url=f"https://www.linkedin.com/in/{slugify(first_name)}-{slugify(last_name)}",
            website_url=f"https://{company.domain}",
            enrichment_status=random.choice(["enriched", "pending", "failed", "enriching"]),
            enrichment_confidence=round(random.uniform(0.48, 0.96), 2),
            email_opens=random.randint(0, 12),
            email_clicks=random.randint(0, 5),
            last_contacted_at=datetime.utcnow() - timedelta(days=random.randint(1, 60)),
        )
        db.add(prospect)
        prospects.append(prospect)

    db.commit()
    for prospect in prospects:
        db.refresh(prospect)

    trace_logic(logger, "seed.prospects.created", count=len(prospects))
    return prospects


def create_documents(db, demo_user: AuthUser, companies: list[Company]) -> list[Document]:
    documents = []
    doc_types = ["pdf", "csv", "email_transcript", "call_transcript"]
    for index in range(DOCUMENT_COUNT):
        company = companies[index % len(companies)]
        file_name = f"{slugify(company.name)}-brief-{index + 1}.pdf"
        document = Document(
            user_id=demo_user.user_id,
            file_path=f"/seed-data/{slugify(company.name)}/{file_name}",
            file_name=file_name,
            document_type=doc_types[index % len(doc_types)],
            num_pages=random.randint(2, 14),
            file_size_bytes=random.randint(120_000, 2_400_000),
            extracted_text=(
                f"{company.name} account brief covering buying committee signals, stack notes, and current growth focus. "
                f"Industry: {company.industry}. Monitoring enabled: {company.monitoring_enabled}."
            ),
            associated_company_id=company.company_id,
            upload_date=datetime.utcnow() - timedelta(days=random.randint(1, 90)),
        )
        db.add(document)
        documents.append(document)

    db.commit()
    trace_logic(logger, "seed.documents.created", count=len(documents))
    return documents


def create_skills(db, demo_user: AuthUser) -> list[Skill]:
    skills = []
    for index in range(SKILL_COUNT):
        skill_type = SKILL_TYPES[index % len(SKILL_TYPES)]
        skill = Skill(
            user_id=demo_user.user_id,
            skill_name=f"{skill_type.title()} Skill {index + 1}",
            skill_type=skill_type,
            skill_definition={
                "criteria": {"intent_score": 60 + (index % 20)},
                "playbook": skill_type,
                "channel": random.choice(["email", "call", "linkedin", "monitoring"]),
            },
            description=f"Reusable {skill_type} motion for seeded CRM automation tests.",
            version=1 + (index % 3),
            is_active=(index % 5 != 0),
            execution_count=random.randint(0, 18),
            success_count=random.randint(0, 16),
            avg_execution_time_ms=round(random.uniform(180.0, 2800.0), 2),
        )
        db.add(skill)
        skills.append(skill)

    db.commit()
    trace_logic(logger, "seed.skills.created", count=len(skills))
    return skills


def create_campaigns(db, demo_user: AuthUser, companies: list[Company]) -> list[Campaign]:
    campaigns = []
    for index in range(CAMPAIGN_COUNT):
        company = companies[index % len(companies)]
        template = CAMPAIGN_TEMPLATES[index % len(CAMPAIGN_TEMPLATES)]
        campaign = Campaign(
            user_id=demo_user.user_id,
            name=f"{template} - {company.name}",
            description=f"Automated outbound sequence targeting {company.industry.lower()} teams.",
            sequence_steps=[
                {
                    "day": 0,
                    "subject": f"{company.name} team automation idea",
                    "body": f"Sharing a short note on workflow improvements for {company.name}.",
                },
                {
                    "day": 4,
                    "subject": f"Follow-up on {company.name} growth systems",
                    "body": "Circling back with a tighter operational angle and proof points.",
                },
                {
                    "day": 9,
                    "subject": "Worth a working session?",
                    "body": "Happy to map the current workflow and propose an automation blueprint.",
                },
            ],
            target_criteria={
                "industry": company.industry,
                "funding_stage": company.funding_stage,
                "monitoring_enabled": company.monitoring_enabled,
            },
            is_active=(index % 4 != 0),
            enrolled_count=random.randint(5, 40),
            opened_count=random.randint(3, 25),
            clicked_count=random.randint(1, 18),
            replied_count=random.randint(0, 9),
            conversion_rate=round(random.uniform(0.03, 0.28), 2),
            created_at=datetime.utcnow() - timedelta(days=random.randint(5, 110)),
            updated_at=datetime.utcnow() - timedelta(days=random.randint(1, 30)),
        )
        db.add(campaign)
        campaigns.append(campaign)

    db.commit()
    trace_logic(logger, "seed.campaigns.created", count=len(campaigns))
    return campaigns


def create_rules(db, demo_user: AuthUser) -> list[Rule]:
    rules = []
    for index in range(RULE_COUNT):
        base_name, trigger_event, rule_type = RULE_TEMPLATES[index % len(RULE_TEMPLATES)]
        priority = (index % 10) + 1
        rule = Rule(
            user_id=demo_user.user_id,
            rule_name=f"{base_name} {index + 1}",
            rule_type=rule_type,
            rule_definition={
                "trigger_event": trigger_event,
                "conditions": {
                    "enrichment_confidence": {"gte": round(0.5 + ((index % 5) * 0.1), 2)},
                    "intent_score": {"gte": 55 + (index % 20)},
                },
                "actions": [
                    {"action_type": "send_email", "action_params": {"template": "follow-up"}},
                    {"action_type": "create_task", "action_params": {"owner": "revops"}},
                ],
            },
            description="Seeded automation rule for workflow and orchestration testing.",
            is_active=(index % 6 != 0),
            priority=priority,
            execution_count=random.randint(0, 24),
            match_count=random.randint(0, 18),
            created_at=datetime.utcnow() - timedelta(days=random.randint(15, 120)),
            updated_at=datetime.utcnow() - timedelta(days=random.randint(1, 20)),
        )
        db.add(rule)
        rules.append(rule)

    db.commit()
    for rule in rules:
        db.refresh(rule)

    trace_logic(logger, "seed.rules.created", count=len(rules))
    return rules


def create_interactions(db, prospects: list[Prospect]) -> list[Interaction]:
    interactions = []
    for index in range(INTERACTION_COUNT):
        prospect = prospects[index % len(prospects)]
        interaction_type = INTERACTION_TYPES[index % len(INTERACTION_TYPES)]
        opened = interaction_type == "email" and random.choice([True, False])
        clicked = opened and random.choice([True, False])
        interaction = Interaction(
            prospect_id=prospect.prospect_id,
            interaction_type=interaction_type,
            subject=f"{interaction_type.title()} touchpoint #{index + 1}",
            body=f"Seeded {interaction_type} content for {prospect.first_name} {prospect.last_name}.",
            initiated_by=random.choice(["user", "prospect"]),
            interaction_date=datetime.utcnow() - timedelta(days=random.randint(1, 90)),
            duration_seconds=random.randint(180, 3600) if interaction_type in {"call", "meeting"} else None,
            email_opened=opened if interaction_type == "email" else None,
            email_clicked=clicked if interaction_type == "email" else None,
            created_at=datetime.utcnow() - timedelta(days=random.randint(1, 90)),
        )
        db.add(interaction)
        interactions.append(interaction)

    db.commit()
    trace_logic(logger, "seed.interactions.created", count=len(interactions))
    return interactions


def create_lead_scores(db, demo_user: AuthUser, prospects: list[Prospect]) -> list[LeadScore]:
    scores = []
    for index, prospect in enumerate(prospects[:LEAD_SCORE_COUNT]):
        fit_score = round(random.uniform(55, 96), 2)
        engagement_score = round(random.uniform(20, 92), 2)
        propensity_score = round(random.uniform(35, 94), 2)
        total_score = round((fit_score * 0.45) + (engagement_score * 0.2) + (propensity_score * 0.35), 2)
        grade = "A" if total_score >= 85 else "B" if total_score >= 70 else "C" if total_score >= 55 else "D"

        score = LeadScore(
            prospect_id=prospect.prospect_id,
            company_id=prospect.company_id,
            user_id=demo_user.user_id,
            fit_score=fit_score,
            engagement_score=engagement_score,
            propensity_score=propensity_score,
            total_score=total_score,
            grade=grade,
            score_breakdown={
                "industry_fit": fit_score,
                "engagement": engagement_score,
                "propensity": propensity_score,
            },
            signals=[
                {"signal_type": "email_open", "value": prospect.email_opens, "weight": 0.2},
                {"signal_type": "monitoring", "value": 1 if index % 2 == 0 else 0, "weight": 0.3},
            ],
            is_hot_lead=total_score >= 80,
            created_at=datetime.utcnow() - timedelta(days=random.randint(1, 45)),
            updated_at=datetime.utcnow() - timedelta(days=random.randint(0, 10)),
        )
        db.add(score)
        scores.append(score)

    db.commit()
    trace_logic(logger, "seed.lead_scores.created", count=len(scores))
    return scores


def create_agent_executions(db, demo_user: AuthUser, prospects: list[Prospect], companies: list[Company]) -> list[AgentExecution]:
    executions = []
    for index in range(AGENT_EXECUTION_COUNT):
        prospect = prospects[index % len(prospects)]
        company = companies[index % len(companies)]
        start_time = datetime.now(timezone.utc) - timedelta(days=random.randint(0, 45), hours=random.randint(0, 12))
        status = random.choice(["success", "success", "running", "failed"])
        duration_ms = None if status == "running" else random.randint(250, 4200)
        execution = AgentExecution(
            user_id=demo_user.user_id,
            agent_type=AGENT_TYPES[index % len(AGENT_TYPES)],
            agent_name=f"{AGENT_TYPES[index % len(AGENT_TYPES)].lower()}_seed",
            task_id=fake.uuid4(),
            prospect_id=prospect.prospect_id,
            company_id=company.company_id,
            status=status,
            input_data={"company": company.name, "prospect": prospect.email},
            output_data={"summary": "Seeded execution output", "status": status} if status != "running" else None,
            error_message="Timeout while crawling public docs" if status == "failed" else None,
            start_time=start_time,
            end_time=start_time + timedelta(milliseconds=duration_ms) if duration_ms else None,
            duration_ms=duration_ms,
            tokens_used=random.randint(1200, 24000),
            api_cost_cents=Decimal(str(round(random.uniform(0.12, 8.75), 2))),
            decision_description=f"Seeded {status} execution for {company.name}.",
            confidence_score=round(random.uniform(0.52, 0.98), 2),
            memory_hits=random.randint(0, 5),
            created_at=start_time,
        )
        db.add(execution)
        executions.append(execution)

    db.commit()
    trace_logic(logger, "seed.agent_executions.created", count=len(executions))
    return executions


def create_enrichment_events(db, prospects: list[Prospect]) -> list[EnrichmentEvent]:
    events = []
    field_names = ["enrichment_status", "title", "location", "linkedin_url", "company_id"]
    for index in range(ENRICHMENT_EVENT_COUNT):
        prospect = prospects[index % len(prospects)]
        field_name = field_names[index % len(field_names)]
        event = EnrichmentEvent(
            prospect_id=prospect.prospect_id,
            field_name=field_name,
            old_value="pending" if field_name == "enrichment_status" else None,
            new_value=str(getattr(prospect, field_name, "updated")),
            agent_name=random.choice(["EnrichmentAgent", "ResearchAgent", "MonitoringAgent"]),
            confidence_score=round(random.uniform(0.51, 0.97), 2),
            source=random.choice(["crawl:public-web", "gemini:extraction", "manual:seed-script"]),
            created_at=datetime.utcnow() - timedelta(days=random.randint(0, 35)),
        )
        db.add(event)
        events.append(event)

    db.commit()
    trace_logic(logger, "seed.enrichment_events.created", count=len(events))
    return events


def create_rule_executions(db, demo_user: AuthUser, rules: list[Rule], prospects: list[Prospect]) -> list[RuleExecution]:
    executions = []
    for index in range(RULE_EXECUTION_COUNT):
        rule = rules[index % len(rules)]
        prospect = prospects[index % len(prospects)]
        execution = RuleExecution(
            rule_id=rule.rule_id,
            user_id=demo_user.user_id,
            prospect_id=prospect.prospect_id,
            company_id=prospect.company_id,
            trigger_event=rule.rule_definition.get("trigger_event", "signal_detected"),
            triggered=(index % 5 != 0),
            action_taken=random.choice(["send_email", "create_task", "update_lead_score"]),
            result=random.choice(["success", "success", "failed"]),
            trigger_data={"prospect_id": prospect.prospect_id, "rule_id": rule.rule_id},
            action_result={"queued": True, "channel": "email"},
            error_message="Sequence paused due to bounce risk" if index % 11 == 0 else None,
            created_at=datetime.utcnow() - timedelta(days=random.randint(0, 25)),
        )
        db.add(execution)
        executions.append(execution)

    db.commit()
    trace_logic(logger, "seed.rule_executions.created", count=len(executions))
    return executions


def create_memory_entries(db, demo_user: AuthUser, companies: list[Company], prospects: list[Prospect]) -> None:
    for index in range(MEMORY_STORE_COUNT):
        if index % 2 == 0:
            company = companies[index % len(companies)]
            key = f"seed:company:{company.company_id}:snapshot"
            value = {
                "company": company.name,
                "industry": company.industry,
                "monitoring_enabled": company.monitoring_enabled,
            }
        else:
            prospect = prospects[index % len(prospects)]
            key = f"seed:prospect:{prospect.prospect_id}:summary"
            value = {
                "name": f"{prospect.first_name} {prospect.last_name}",
                "title": prospect.title,
                "status": prospect.enrichment_status,
            }

        db.add(
            MemoryStore(
                memory_key=key,
                memory_value=value,
                ttl_seconds=None if index % 3 == 0 else 86400 * (1 + (index % 7)),
                created_at=datetime.utcnow() - timedelta(days=random.randint(0, 20)),
                accessed_at=datetime.utcnow() - timedelta(days=random.randint(0, 5)),
            )
        )

    for index in range(MEMORY_VECTOR_COUNT):
        prospect = prospects[index % len(prospects)]
        db.add(
            MemoryVector(
                embedding_key=f"seed:prospect:{prospect.prospect_id}:embedding",
                embedding="[" + ",".join(f"{random.uniform(-1, 1):.5f}" for _ in range(8)) + "]",
                embedding_text=(
                    f"{prospect.first_name} {prospect.last_name} works as {prospect.title} at prospect company {prospect.company_id}."
                ),
                entity_type="prospect",
                entity_id=prospect.prospect_id,
                user_id=demo_user.user_id,
                created_at=datetime.utcnow() - timedelta(days=random.randint(0, 15)),
            )
        )

    db.commit()
    trace_logic(
        logger,
        "seed.memory.created",
        memory_store_count=MEMORY_STORE_COUNT,
        memory_vector_count=MEMORY_VECTOR_COUNT,
    )


def seed_database() -> None:
    configure_logging()
    db = SessionLocal()
    try:
        trace_logic(logger, "seed.start", provider=os.getenv("ACTIVE_DB_PROVIDER", "unknown"))
        cleanup_existing_seed_data(db)

        demo_user, _ = create_users(db)
        target_user = resolve_target_user(db) or demo_user
        companies = create_companies(db, target_user)
        prospects = create_prospects(db, target_user, companies)
        create_documents(db, target_user, companies)
        create_skills(db, target_user)
        campaigns = create_campaigns(db, target_user, companies)
        rules = create_rules(db, target_user)
        create_interactions(db, prospects)
        create_lead_scores(db, target_user, prospects)
        create_agent_executions(db, target_user, prospects, companies)
        create_enrichment_events(db, prospects)
        create_rule_executions(db, target_user, rules, prospects)
        create_memory_entries(db, target_user, companies, prospects)

        trace_logic(
            logger,
            "seed.complete",
            demo_email=DEMO_EMAIL,
            demo_password=DEMO_PASSWORD,
            target_user_email=target_user.email,
            target_user_id=target_user.user_id,
            campaigns=len(campaigns),
            companies=len(companies),
            prospects=len(prospects),
            rules=len(rules),
        )
    except Exception as exc:
        db.rollback()
        trace_logic(logger, "seed.error", error=str(exc))
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
