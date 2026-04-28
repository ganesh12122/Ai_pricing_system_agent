# Contributing Guide

Welcome to the RAG Sales Chatbot project. This guide helps you get oriented quickly so you can contribute without breaking anything.

---

## Before You Start

Read these docs in order:
1. [docs/START_HERE.md](docs/START_HERE.md) — What the project does
2. [docs/FLOW_WALKTHROUGH.md](docs/FLOW_WALKTHROUGH.md) — End-to-end request lifecycle
3. [docs/DEVELOPMENT_GUIDE.md](docs/DEVELOPMENT_GUIDE.md) — How to run it locally
4. [docs/architecture.md](docs/architecture.md) — Technical architecture

---

## Project Structure

```
RAG_CHATBOT/
├── services/           # Five independent Python FastAPI microservices
│   ├── chat_api/       # Public entrypoint — do not add business logic here
│   ├── gateway_router/ # Intent classification
│   ├── embedding_service/ # Vector embedding
│   ├── llm_service/    # LLM inference
│   └── pricing_api/    # Exact pricing from DB
├── n8n/workflows/      # n8n orchestration workflow JSON exports
├── db/
│   ├── migrations/     # SQL schema (applied on first Postgres start)
│   └── seed/           # Seed data + module markdown docs
├── scripts/            # Ingestion, seeding, and testing scripts
└── docs/               # All project documentation
```

---

## Which file to touch for which change

| Goal | Where to look |
|------|--------------|
| Change how intent is classified | `services/gateway_router/main.py` |
| Change LLM model or backend | `.env` `OLLAMA_MODEL` / `INFERENCE_BACKEND` + `services/llm_service/main.py` |
| Change system prompt | `services/llm_service/main.py` (system prompt assembled in `_build_messages`) or the n8n Code node "Assemble LLM Payload" |
| Add a new module / product | `db/seed/002_seed_data.sql` + new `.md` file in `db/seed/modules/` then re-run `scripts/ingest.py` |
| Change pricing rules | `db/seed/002_seed_data.sql` then re-run `scripts/seed_db.py` |
| Change the RAG workflow steps | `n8n/workflows/query_workflow_v2.json` — import fresh into n8n after edits |
| Change DB schema | Add a new migration file `db/migrations/002_*.sql` — never modify `001_init.sql` after first deploy |
| Change public API shape | `services/chat_api/main.py` + update `docs/api-contracts.md` |

---

## Coding Style

- Language: Python 3.11+
- Framework: FastAPI
- Validation: Pydantic v2 models for all request/response shapes
- HTTP client: `httpx` (async)
- DB client: `asyncpg` (async)
- All endpoints must have a `GET /health` that returns `{"status": "healthy"}`
- No blocking calls inside async route handlers

---

## Branching Convention

```
main         — production-ready code only
feature/*    — new features (example: feature/streaming-responses)
fix/*        — bug fixes (example: fix/cache-query-empty-result)
chore/*      — non-functional work (docs, deps, config)
```

---

## Testing

Run the full test suite after any change:
```bash
python scripts/test_all.py
```

All 50 tests should pass before merging. Add new tests for any new endpoint or behavior you introduce.

---

## Making DB Schema Changes

1. Never edit `001_init.sql` after first deploy — it runs only on fresh Postgres init.
2. Create `db/migrations/002_your_change.sql`, `003_...`, etc.
3. Apply manually: `docker exec -i rag_postgres psql -U rag_user -d rag_chatbot < db/migrations/002_your_change.sql`
4. Document the change in [CHANGELOG.md](CHANGELOG.md).

---

## Adding Module Documentation (for RAG)

1. Create `db/seed/modules/your_module_name.md` following the format of existing files.
2. Run ingestion to embed and store it:
   ```bash
   python scripts/ingest.py
   ```
3. Test retrieval by asking the chatbot about the module.

---

## Updating n8n Workflows

1. Edit the JSON file in `n8n/workflows/`.
2. In n8n UI: delete the old workflow → import the updated JSON.
3. Re-assign Postgres credentials in each DB node (n8n stores credential IDs locally).
4. Activate the workflow and test end-to-end.

---

## Questions

If something is unclear, check [docs/README.md](docs/README.md) for the full documentation map.
