# Roadmap — Enhancement, Upgrade and Scale Plan

This roadmap covers the next development phases for the RAG Sales Chatbot system.
Each phase is designed to be completed independently. Prerequisites listed per phase.

---

## Current State (Phase 1 — Complete)

- 5 Python FastAPI microservices running in Docker
- n8n orchestration workflow (15 nodes, fully functional)
- PostgreSQL + pgvector for vectors, cache, history, and pricing
- Ollama (mistral + nomic-embed-text) for local LLM/embedding
- 7 modules seeded, 16 pricing rules, full RAG working
- Tests: 50/50 passing

---

## Phase 2 — Response Quality & Accuracy

> Goal: better answers, more accurate intent routing, richer context

### 2.1 Smarter Intent Classification
**Why**: The current keyword/regex classifier misses complex queries like "we're scaling from 50 to 200 next quarter, which plan grows with us?"
**How**:
- Add an ML classifier as an alternative mode in `gateway_router`
- Use a small sentence-transformers model (e.g., `all-MiniLM-L6-v2`) with a simple 2-class trained classifier
- Keep regex as fallback when model is < 0.65 confidence
- No n8n workflow changes needed (same API contract)

```
Priority: High
File: services/gateway_router/main.py
New dep: sentence-transformers
Effort: Medium
```

### 2.2 User Context Extraction
**Why**: The LLM currently receives the raw prompt. Sometimes users say something like "50 employees, need payroll and CRM" — the prompt contains structured facts we can pre-extract.
**How**:
- Add `POST /extract` in `gateway_router` that parses `user_count`, `mentioned_modules`, `industry` using regex + LLM
- n8n calls this after classify — passes structured facts into LLM payload
- Results in sharper, more specific recommendations

```
Priority: Medium
File: services/gateway_router/main.py
n8n: query_workflow_v2.json (add 1 extra HTTP node after Classify Intent)
Effort: Medium
```

### 2.3 Re-ranking Retrieved Context
**Why**: Top-5 by cosine similarity sometimes includes chunks that are related but not directly useful
**How**:
- Add a `POST /rerank` endpoint in `embedding_service`
- Use cross-encoder model (`cross-encoder/ms-marco-MiniLM-L-6-v2`) to re-rank top-10 → keep top-3
- Replace RAG Search result directly

```
Priority: Medium
File: services/embedding_service/main.py
n8n: Replace RAG Search → Add Rerank step
Effort: Medium
```

### 2.4 Semantic Cache Write-Back
**Why**: Cache never fills because the workflow currently has no write path for new LLM responses
**How**:
- Add a "Write Semantic Cache" Code + Postgres node after Save Chat History
- Store the query embedding + response into `semantic_cache` with 7-day TTL
- Required for cache to start saving time on repeated questions

```
Priority: High
File: n8n/workflows/query_workflow_v2.json
n8n: add after Save Chat History
Effort: Low
```

---

## Phase 3 — User Experience

> Goal: conversations feel more natural, fewer dead-ends

### 3.1 Streaming Responses
**Why**: LLM takes 5–15 seconds to generate. Users see nothing until it's done.
**How**:
- Modify `llm_service` POST /generate to support `stream=True` (SSE)
- Modify `chat_api` to proxy the SSE stream to callers
- n8n is bypassed for the LLM call in streaming mode — `chat_api` calls services directly
- Backend: `STREAM_RESPONSES=true` env flag to enable

```
Priority: Medium
File: services/llm_service/main.py, services/chat_api/main.py
Effort: High (requires architecture shift for this path)
```

### 3.2 Follow-up Question Generation
**Why**: When a user's message is vague, the assistant should ask a targeted clarifying question (team size, industry, priorities) rather than guessing
**How**:
- Add a check in "Assemble LLM Payload" Code node: if `retrieved_context` is empty OR `userID` has no history → inject clarification instructions into system prompt
- No new service needed

```
Priority: Medium
File: n8n/workflows/query_workflow_v2.json (Assemble LLM Payload code node)
Effort: Low
```

### 3.3 Module Comparison Mode
**Why**: Users often want side-by-side comparison ("starter vs professional for 20 users")
**How**:
- gateway_router detects comparison phrases ("vs", "compare", "difference between")
- Returns `intent: "comparison"` 
- n8n comparison branch: calls pricing_api for both modules, builds comparison table in LLM prompt

```
Priority: Medium
File: services/gateway_router/main.py, n8n workflow (new branch)
Effort: Medium
```

---

## Phase 4 — Scale & Reliability

> Goal: handle more users, better observability, easier deployments

### 4.1 Replace Ollama with vLLM (High Concurrency)
**Why**: Ollama is single-threaded per request. vLLM supports batched inference for 10x throughput.
**How**:
- Deploy vLLM as a Docker service pointing to same model
- Set `INFERENCE_BACKEND=vllm` in `.env`
- Zero code changes in services (already handled in `llm_service`)

```
Priority: High (when traffic > 10 concurrent)
File: docker-compose.yml, .env
Effort: Low
```

### 4.2 Structured Logging
**Why**: Currently all services use `print`. No way to query logs, trace requests, or alert on errors.
**How**:
- Add `structlog` to all services
- Each request logs: `request_id`, `service`, `endpoint`, `latency_ms`, `status`
- Forward to ELK stack or Loki

```
Priority: Medium
File: All services/*/main.py
New dep: structlog
Effort: Medium
```

### 4.3 Rate Limiting on chat_api
**Why**: No limit on how fast a single user or IP can send requests — risk of model abuse.
**How**:
- Add `slowapi` rate limiter to `chat_api`
- Default: 30 requests/minute per IP, 100/minute per authenticated userID

```
Priority: High
File: services/chat_api/main.py
New dep: slowapi
Effort: Low
```

### 4.4 Admin API for Module Management
**Why**: Currently updating a module requires editing SQL and re-running ingestion manually. A business team can't do this safely.
**How**:
- Add `POST /modules`, `PUT /modules/{id}`, `DELETE /modules/{id}` to `pricing_api`
- Add `POST /ingest/module` to `embedding_service` that takes markdown + module_id and auto-embeds
- Protected by API key header

```
Priority: Medium
Effort: High
```

### 4.5 Horizontal Scaling
**Why**: Single container per service becomes a bottleneck under load.
**How**:
- `gateway_router` and `embedding_service` are stateless — scale with `docker compose --scale`
- `pricing_api` is stateless — scalable with a connection pool via pgBouncer
- `chat_api` is stateless — put behind a load balancer (nginx or Traefik)
- `llm_service` scales with GPU availability

```
Priority: Low (Tier 3 scale)
File: docker-compose.yml
Effort: Medium
```

---

## Phase 5 — AI Platform Upgrades

> Goal: keep the AI quality current and extensible

### 5.1 Weekly Document Re-Ingestion
**Why**: If module docs change, old embeddings become stale.
**How**:
- n8n scheduled workflow: weekly trigger → ingestion_workflow.json
- Or: trigger ingestion webhook whenever a module doc is updated

### 5.2 Model Upgrade Path
**Why**: Better models keep improving.
- Current: `mistral:latest`
- Upgrade path: `qwen2.5:7b` → `llama3.1:8b` → `mistral-nemo:12b`
- Change only: `OLLAMA_MODEL` in `.env` and pull the model

### 5.3 Multimodal Input (Voice / File Upload)
- Transcribe audio → text (Whisper) then pass through existing pipeline
- Accept PDF → extract text → chunk → embed → ingest

---

## Phase Priorities (At a Glance)

| Item | Phase | Priority | Effort |
|------|-------|----------|--------|
| Semantic cache write-back | 2 | High | Low |
| Rate limiting on chat_api | 4 | High | Low |
| vLLM swap | 4 | High (on scale) | Low |
| Smarter intent classifier | 2 | High | Medium |
| Follow-up question generation | 3 | Medium | Low |
| Context re-ranking | 2 | Medium | Medium |
| User context extraction | 2 | Medium | Medium |
| Structured logging | 4 | Medium | Medium |
| Module comparison mode | 3 | Medium | Medium |
| Streaming responses | 3 | Medium | High |
| Admin API for modules | 4 | Medium | High |
| Horizontal scaling | 4 | Low | Medium |
