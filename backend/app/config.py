"""Application settings and database target resolution."""

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application-wide settings loaded from environment variables."""

    active_db_provider: str = Field(
        default="local",
        description="Active database target: local or supabase",
    )
    database_url: str = Field(
        default="",
        description="Explicit database URL override. If set, it wins over provider-specific URLs.",
    )
    local_database_url: str = Field(
        default="postgresql://crm_user:crm_password@postgres:5432/agentic_crm",
        description="Local PostgreSQL connection string used by Docker development.",
    )
    supabase_database_url: str = Field(
        default="",
        description="Supabase PostgreSQL connection string used for staged cutover.",
    )

    redis_url: str = Field(default="redis://redis:6379")
    chroma_host: str = Field(default="chroma")
    chroma_port: int = Field(default=8000)

    gemini_api_key: str = Field(default="")
    github_token: str = Field(default="")
    brave_search_api_key: str = Field(default="")

    supabase_url: str = Field(default="")
    supabase_key: str = Field(default="")
    supabase_service_role_key: str = Field(default="")

    jwt_secret_key: str = Field(..., min_length=32)
    jwt_algorithm: str = Field(default="HS256")
    jwt_expire_minutes: int = Field(default=30)

    port: int = Field(default=8000)
    environment: str = Field(default="development")
    allowed_origins: str = Field(default="http://localhost:3000")
    log_level: str = Field(default="INFO")
    debug_trace_enabled: bool = Field(default=True)
    crawl_provider: str = Field(default="crawl4ai")
    crawl_browser_type: str = Field(default="chromium")
    crawl_headless: bool = Field(default=True)
    crawl_text_mode: bool = Field(default=True)
    crawl_light_mode: bool = Field(default=False)
    crawl_http_fallback_enabled: bool = Field(default=True)
    crawl_respect_robots_txt: bool = Field(default=True)
    crawl_verbose: bool = Field(default=False)
    crawl_user_agent: str = Field(default="AgenticCRMResearchBot/1.0")
    crawl_word_count_threshold: int = Field(default=10)
    crawl_wait_for: str = Field(default="")
    rate_limit_per_minute: int = Field(default=100)
    daily_gemini_tokens: int = Field(default=1_000_000)
    bcrypt_rounds: int = Field(default=12)

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    @property
    def normalized_db_provider(self) -> str:
        provider = self.active_db_provider.strip().lower()
        return provider if provider in {"local", "supabase"} else "local"

    @property
    def sqlalchemy_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        if self.normalized_db_provider == "supabase" and self.supabase_database_url:
            return self.supabase_database_url
        return self.local_database_url

    @property
    def standby_supabase_database_url(self) -> str:
        if self.normalized_db_provider == "supabase":
            return ""
        return self.supabase_database_url

    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore",
    }


settings = Settings()
