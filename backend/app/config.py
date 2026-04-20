"""
app/config.py — Application settings loaded from environment variables.

Uses Pydantic-settings for type-safe, validated configuration management.
All values are sourced from environment variables or a .env file.

DATABASE CONFIGURATION:
  Current: Supabase PostgreSQL (DATABASE_URL from Supabase connection string)
  Legacy: Local PostgreSQL (commented below — to revert, uncomment DATABASE_URL line)
"""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application-wide settings. Never commit real values — use .env or Docker secrets."""

    # ── Database ──────────────────────────────────────────────────────────────
    # CURRENT: Supabase PostgreSQL connection string
    database_url: str = Field(
        ...,
        description="Supabase PostgreSQL connection string (format: postgresql://user:pass@host:port/dbname)",
    )

    # LEGACY: Local PostgreSQL (uncomment DATABASE_URL in .env to revert)
    # To switch back to local Postgres:
    # 1. Uncomment "DATABASE_URL=postgresql://crm_user:crm_password@localhost:5433/agentic_crm" in .env
    # 2. Uncomment postgres service in docker-compose.yml
    # 3. Comment out chroma service in docker-compose.yml (or keep both)

    # ── Cache / Broker ────────────────────────────────────────────────────────
    redis_url: str = Field(
        default="redis://redis:6379",
        description="Redis connection URL (used for caching and Celery broker)",
    )

    # ── Vector Store (Chroma) ─────────────────────────────────────────────────
    chroma_host: str = Field(
        default="chroma",
        description="Chroma vector DB host (localhost or Docker service name)",
    )
    chroma_port: int = Field(
        default=8000,
        description="Chroma vector DB port",
    )

    # ── External API keys ────────────────────────────────────────────────────
    gemini_api_key: str = Field(
        ...,
        description="Google Gemini API key (from https://aistudio.google.com/app/apikeys)",
    )
    github_token: str = Field(
        default="",
        description="GitHub PAT for public-repo access (optional but recommended)",
    )

    # ── Supabase ──────────────────────────────────────────────────────────────
    # (Only needed if using Supabase auth; currently using Postgres auth)
    supabase_url: str = Field(
        default="",
        description="Supabase project URL (for future auth integration)",
    )
    supabase_key: str = Field(
        default="",
        description="Supabase anon key (for future auth integration)",
    )

    # ── JWT / Security ───────────────────────────────────────────────────────
    jwt_secret_key: str = Field(
        ...,
        min_length=32,
        description="Secret key for signing JWT tokens. Must be at least 32 characters.",
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT signing algorithm")
    jwt_expire_minutes: int = Field(
        default=30,
        description="Token expiry time in minutes",
    )

    # ── Server ────────────────────────────────────────────────────────────────
    port: int = Field(default=8000, description="Uvicorn listening port")
    environment: str = Field(
        default="development",
        description="Runtime environment: 'development' | 'staging' | 'production'",
    )
    allowed_origins: str = Field(
        default="http://localhost:3000",
        description="Comma-separated list of permitted CORS origins",
    )

    # ── Logging ───────────────────────────────────────────────────────────────
    log_level: str = Field(
        default="INFO",
        description="Python logging level: DEBUG | INFO | WARNING | ERROR",
    )

    # ── Rate Limiting ─────────────────────────────────────────────────────────
    rate_limit_per_minute: int = Field(
        default=100,
        description="Maximum API requests per minute per IP",
    )

    # ── Gemini Quota ──────────────────────────────────────────────────────────
    daily_gemini_tokens: int = Field(
        default=1_000_000,
        description="Daily Gemini API token budget per user",
    )

    # ── Password Hashing ─────────────────────────────────────────────────────
    bcrypt_rounds: int = Field(
        default=12,
        description="Number of bcrypt hashing rounds (higher = slower but safer)",
    )

    @property
    def cors_origins(self) -> list[str]:
        """Parse comma-separated ALLOWED_ORIGINS into a Python list."""
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore",
    }


# Singleton — import this everywhere instead of re-instantiating Settings()
settings = Settings()
