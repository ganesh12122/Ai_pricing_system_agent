# Changelog

All significant changes are documented here.
Format: `[version/phase] — date — description`

---

## [Phase 1 — Foundation] — April 2026

### Infrastructure
- Initialized project with Docker Compose stack
- PostgreSQL with pgvector extension (image: `pgvector/pgvector:pg16`)
- Schema: 5 tables — `document_chunks`, `semantic_cache`, `chat_sessions`, `modules`, `pricing_rules`
- IVFFlat indexes on embedding columns for fast vector similarity search
- Auto-applied via `db/migrations/001_init.sql` on first container start

### Services Created (all Python FastAPI)
- `chat_api` (port 8000) — Public gateway, validates + forwards to n8n
- `gateway_router` (port 8001) — Keyword/regex intent classifier
- `embedding_service` (port 8002) — Wraps Ollama nomic-embed-text API
- `llm_service` (port 8003) — Assembles context + calls Ollama mistral
- `pricing_api` (port 8004) — Exact pricing from DB via asyncpg

### Data
- Seeded 7 modules: starter, professional, enterprise, crm_addon, analytics_addon, payroll_addon, storage_addon
- Seeded 16 pricing rules with user-tier bands
- Created 7 module documentation markdown files
- Ingested docs into `document_chunks` via `scripts/ingest.py`

### n8n Orchestration
- `query_workflow_v2.json` — Full RAG query pipeline (15 nodes)
- `ingestion_workflow.json` — Document ingestion via n8n
- Networks: services joined to both `rag_network` and `aob-network` so n8n can reach them

### Testing
- `scripts/test_all.py` — 50 automated tests across 9 categories
- All 50 tests passing

---

## [Phase 1 — Bug Fixes] — April 2026

### n8n workflow fixes
- **Fixed**: pgvector `<=>` operator stripped by n8n Postgres node
  - Solution: moved SQL into Code nodes (`Build Cache Query`, `Build RAG Query`) as JavaScript template literals
- **Fixed**: `$1` parameterized queries not supported in n8n `executeQuery`
  - Solution: Code nodes build complete SQL strings
- **Fixed**: `.item` accessor caused "paired item unavailable" crash in `Prepare Save Data`
  - Solution: replaced all `.item` with `.first()` across all Code nodes; redesigned `Prepare Save Data` to read `$input.item.json` from direct predecessor
- **Fixed**: `Set LLM Response` not passing `userID` and `user_prompt` downstream
  - Solution: added both fields to the Set node output
- **Fixed**: Pricing data path `$json.data` → `$json` (pricing_api returns flat JSON)
- **Fixed**: `alwaysOutputData: true` added to Postgres nodes to handle empty query results
- **Fixed**: `Cache Hit?` IF node changed from strict to loose type validation

### Network fix
- All Python services added to `aob-network` (external) so n8n container can reach them via DNS names

### Documentation
- Full docs suite created in `docs/` directory
- Per-service docs created in each `services/*/docs/README.md`

---

## [Next — Phase 2 — Enhancements] — Planned

See [ROADMAP.md](ROADMAP.md) for the full plan.
