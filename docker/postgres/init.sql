-- docker/postgres/init.sql
-- Runs once when the Postgres container is first created.
-- Installs the pgvector extension for vector similarity search.

-- pgvector (768-dim Gemini embeddings)
CREATE EXTENSION IF NOT EXISTS vector;

-- pg_trgm (for fuzzy text search, used by future full-text search features)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Log completion
DO $$ BEGIN
  RAISE NOTICE 'Agentic CRM: PostgreSQL extensions initialized successfully';
END $$;
