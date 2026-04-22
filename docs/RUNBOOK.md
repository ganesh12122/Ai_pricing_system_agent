# Runbook (Operate and Troubleshoot)

## Goal

Quick operational guide for bringing up services, validating health, and debugging common failures.

## Startup Checklist

1. Start backend services:
```bash
docker compose up -d
```

2. Ensure Ollama is running on host and models exist:
```bash
ollama list
```
Expected models include:
- `mistral:latest`
- `nomic-embed-text`

3. Ensure n8n container is running and connected to `aob-network`.

4. Verify health endpoints:
- `http://localhost:8000/health`
- `http://localhost:8001/health`
- `http://localhost:8002/health`
- `http://localhost:8003/health`
- `http://localhost:8004/health`

## Data Preparation

1. Seed pricing/module data if needed:
```bash
python scripts/seed_db.py
```

2. Ingest document chunks and vectors:
```bash
python scripts/ingest.py
```

## Smoke Test

```bash
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d "{\"userID\":\"1\",\"prompt\":\"Suggest a plan for 50 users\"}"
```

## Common Issues

### 1) n8n cannot call internal services
Symptoms:
- n8n HTTP nodes timeout

Checks:
- Services must share the same Docker network as n8n (`aob-network`)
- Service URLs inside n8n should use container DNS names like `http://gateway_router:8001/...`

### 2) No RAG results
Symptoms:
- Retrieval nodes return empty rows

Checks:
- Run `python scripts/ingest.py`
- Confirm `document_chunks` has data

### 3) No conversation continuity
Symptoms:
- Assistant forgets prior messages

Checks:
- Ensure requests include stable `userID`
- Confirm rows are inserted in `chat_sessions`

### 4) Pricing seems incorrect
Checks:
- Validate `pricing_rules` table data
- Test `pricing_api` directly:
```bash
curl "http://localhost:8004/pricing?modules=starter,professional&user_count=50"
```

### 5) DBeaver cannot connect
Use:
- Host: `localhost`
- Port: `5432`
- Database: `rag_chatbot`
- User: `rag_user`
- Password: `change_me_in_production`

## Ownership Map

- Public API behavior: `chat_api`
- Intent routing: `gateway_router`
- Embeddings: `embedding_service`
- Final generation: `llm_service`
- Pricing correctness: `pricing_api`
- Orchestration and state transitions: `n8n/workflows`
