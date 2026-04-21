-- =============================================================================
-- RAG Sales Chatbot — Initial Database Schema
-- PostgreSQL + pgvector
-- =============================================================================

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- 1. document_chunks — RAG knowledge base (module docs, features, etc.)
-- =============================================================================
CREATE TABLE IF NOT EXISTS document_chunks (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content     TEXT NOT NULL,
    metadata    JSONB NOT NULL DEFAULT '{}',
    -- metadata example: {"module_name": "Professional Plan", "source_file": "plans.md", "chunk_index": 0}
    embedding   vector(768) NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for fast similarity search
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding
    ON document_chunks USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Index for metadata filtering
CREATE INDEX IF NOT EXISTS idx_document_chunks_metadata
    ON document_chunks USING GIN (metadata);

-- =============================================================================
-- 2. semantic_cache — prompt-answer pair cache to skip LLM on repeated queries
-- =============================================================================
CREATE TABLE IF NOT EXISTS semantic_cache (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query_text      TEXT NOT NULL,
    query_embedding vector(768) NOT NULL,
    response_text   TEXT NOT NULL,
    intent          VARCHAR(50),
    hit_count       INTEGER NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at      TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '7 days')
);

-- Index for fast cache similarity lookup
CREATE INDEX IF NOT EXISTS idx_semantic_cache_embedding
    ON semantic_cache USING ivfflat (query_embedding vector_cosine_ops)
    WITH (lists = 50);

-- Auto-cleanup expired cache entries (run via pg_cron or application)
CREATE INDEX IF NOT EXISTS idx_semantic_cache_expires
    ON semantic_cache (expires_at);

-- =============================================================================
-- 3. chat_sessions — conversation history keyed by userID
-- =============================================================================
CREATE TABLE IF NOT EXISTS chat_sessions (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     VARCHAR(255),  -- nullable for anonymous users
    role        VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
    message     TEXT NOT NULL,
    metadata    JSONB DEFAULT '{}',
    -- metadata example: {"intent": "product_pricing", "cached": false, "model": "qwen2.5:7b"}
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for fetching recent history by user
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_time
    ON chat_sessions (user_id, created_at DESC);

-- =============================================================================
-- 4. modules — product/service module catalog
-- =============================================================================
CREATE TABLE IF NOT EXISTS modules (
    id          VARCHAR(100) PRIMARY KEY,
    name        VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    features    JSONB NOT NULL DEFAULT '[]',
    -- features example: ["payroll processing", "tax filing", "employee self-service"]
    category    VARCHAR(100) NOT NULL,
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- 5. pricing_rules — pricing tiers and rules per module
-- =============================================================================
CREATE TABLE IF NOT EXISTS pricing_rules (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    module_id       VARCHAR(100) NOT NULL REFERENCES modules(id) ON DELETE CASCADE,
    tier            VARCHAR(100) NOT NULL,
    user_count_min  INTEGER NOT NULL DEFAULT 1,
    user_count_max  INTEGER,  -- NULL means unlimited
    price_per_user  DECIMAL(10,2) NOT NULL,
    flat_fee        DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    currency        VARCHAR(10) NOT NULL DEFAULT 'USD',
    billing_cycle   VARCHAR(20) NOT NULL DEFAULT 'monthly',
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for pricing lookups by module
CREATE INDEX IF NOT EXISTS idx_pricing_rules_module
    ON pricing_rules (module_id, is_active);

-- Unique constraint: one pricing rule per module+tier+user range
CREATE UNIQUE INDEX IF NOT EXISTS idx_pricing_rules_unique
    ON pricing_rules (module_id, tier, user_count_min, COALESCE(user_count_max, 999999));
