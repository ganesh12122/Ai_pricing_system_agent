# Database Reference

This document explains the full database schema, what each table is for, and how they connect.

---

## Overview

We use a single **PostgreSQL 16** instance with the **pgvector** extension.

> pgvector lets PostgreSQL store and search high-dimensional vectors (embeddings) using ANN (approximate nearest neighbor) algorithms.

```
Database: rag_chatbot
User:     rag_user
Tables:   5 (document_chunks, semantic_cache, chat_sessions, modules, pricing_rules)
```

---

## Tables

### 1. `document_chunks` — RAG Knowledge Base

Stores vectorized chunks of module documentation. This is what the chatbot "searches" to find relevant product information before answering.

```
id          UUID PRIMARY KEY
content     TEXT           — actual text of the chunk
metadata    JSONB          — {"module_name": "...", "source_file": "...", "chunk_index": 0}
embedding   vector(768)    — 768-dim vector from nomic-embed-text
created_at  TIMESTAMPTZ
updated_at  TIMESTAMPTZ
```

**Populated by**: `scripts/ingest.py`
**Read by**: n8n "RAG Search" node (similarity search via `<=>` operator)

**Indexes**:
- `idx_document_chunks_embedding` — IVFFlat index on `embedding` (fast cosine similarity)
- `idx_document_chunks_metadata` — GIN index on `metadata` (fast JSON filtering)

---

### 2. `semantic_cache` — Response Cache

Stores recently generated LLM responses so identical or very similar questions can be answered instantly without calling the LLM again.

```
id              UUID PRIMARY KEY
query_text      TEXT           — original user query text
query_embedding vector(768)    — embedding of the query
response_text   TEXT           — the cached LLM response
intent          VARCHAR(50)    — "product_pricing" or "general_doc"
hit_count       INTEGER        — how many times this cache entry was served
created_at      TIMESTAMPTZ
expires_at      TIMESTAMPTZ    — default: 7 days from creation
```

**How it works**: When a new query comes in, the system checks if any cached query has cosine similarity ≥ 0.92 with the new query. If yes, return the cached response immediately.

**Note**: Cache write-back (saving new responses into this table) is on the roadmap as Phase 2.4.

**Indexes**:
- `idx_semantic_cache_embedding` — IVFFlat for vector search
- `idx_semantic_cache_expires` — for periodic cleanup of expired entries

---

### 3. `chat_sessions` — Conversation History

Stores every user and assistant message, keyed by `user_id`.

```
id         UUID PRIMARY KEY
user_id    VARCHAR(255)   — from request body `userID` field; NULL for anonymous
role       VARCHAR(20)    — "user" or "assistant"
message    TEXT           — the actual message content
metadata   JSONB          — {"intent": "...", "cached": false, "model": "mistral:latest"}
created_at TIMESTAMPTZ
```

**How it works**: Every conversation turn inserts two rows — one for the user message and one for the assistant response. The next request fetches the last 10 rows for the same `user_id` and passes them to the LLM as chat history.

**Index**: `idx_chat_sessions_user_time` — on `(user_id, created_at DESC)` for fast history fetch.

---

### 4. `modules` — Product Catalog

Master list of available software modules/products.

```
id          VARCHAR(100) PRIMARY KEY  — e.g. "starter", "professional", "crm_addon"
name        VARCHAR(255)
description TEXT
features    JSONB                     — array of feature strings
category    VARCHAR(100)              — e.g. "plan", "addon"
is_active   BOOLEAN
created_at  TIMESTAMPTZ
updated_at  TIMESTAMPTZ
```

**Populated by**: `scripts/seed_db.py` (runs `db/seed/002_seed_data.sql`)
**Read by**: `pricing_api` `/pricing` and `/modules` endpoints

**Seeded modules**:

| id | name | category |
|----|------|----------|
| starter | Starter Plan | plan |
| professional | Professional Plan | plan |
| enterprise | Enterprise Plan | plan |
| crm_addon | CRM Add-on | addon |
| analytics_addon | Analytics Add-on | addon |
| payroll_addon | Payroll Add-on | addon |
| storage_addon | Storage Add-on | addon |

---

### 5. `pricing_rules` — Pricing Tiers

Stores pricing rules per module with user-count bands. Supports multi-tier pricing (different rates for different team sizes).

```
id              UUID PRIMARY KEY
module_id       VARCHAR(100)    — FK → modules.id
tier            VARCHAR(100)    — pricing tier name (e.g. "base", "growth", "enterprise")
user_count_min  INTEGER         — minimum users for this rule to apply
user_count_max  INTEGER         — maximum users (NULL = unlimited)
price_per_user  DECIMAL(10,2)
flat_fee        DECIMAL(10,2)   — fixed cost added on top of per-user pricing
currency        VARCHAR(10)     — default "USD"
billing_cycle   VARCHAR(20)     — default "monthly"
is_active       BOOLEAN
```

**How pricing works**: `pricing_api` looks up the matching rule where `user_count_min <= requested_count <= user_count_max`. `subtotal = (price_per_user × user_count) + flat_fee`.

**16 pricing rules seeded** covering all 7 modules across different user-count tiers.

---

## Relationships

```
modules (1) ──< pricing_rules (many)
```

`document_chunks`, `semantic_cache`, and `chat_sessions` are independent tables.

---

## Useful Queries

Check what's been ingested:
```sql
SELECT COUNT(*), metadata->>'source_file' AS source
FROM document_chunks
GROUP BY source
ORDER BY source;
```

Check conversation history for a user:
```sql
SELECT role, message, created_at
FROM chat_sessions
WHERE user_id = '1'
ORDER BY created_at ASC;
```

Check pricing for a module at a specific user count:
```sql
SELECT m.name, pr.tier, pr.price_per_user, pr.flat_fee
FROM modules m
JOIN pricing_rules pr ON m.id = pr.module_id
WHERE m.id = 'professional'
  AND pr.user_count_min <= 50
  AND (pr.user_count_max IS NULL OR pr.user_count_max >= 50)
  AND pr.is_active = TRUE;
```

Check semantic cache:
```sql
SELECT query_text, hit_count, expires_at
FROM semantic_cache
ORDER BY hit_count DESC;
```

Inspect empty cache:
```sql
SELECT COUNT(*) FROM semantic_cache WHERE expires_at > NOW();
```

---

## Migrations

Migrations live in `db/migrations/`.

- `001_init.sql` — full schema. Applied automatically on first container start.
- Future migrations: `002_*.sql`, `003_*.sql`, etc. Apply manually after deploy.

**Rule**: Never modify `001_init.sql` after first deploy. Always add new files.
