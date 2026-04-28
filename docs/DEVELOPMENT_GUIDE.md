# Development Guide

This guide sets up a working local development environment from zero.

---

## Prerequisites

- Docker Desktop (Windows/Mac) or Docker Engine (Linux)
- Python 3.11+
- [Ollama](https://ollama.com) installed on your host machine
- Git

---

## 1. Clone and Configure

```bash
git clone <your-repo-url>
cd RAG_CHATBOT
cp .env.example .env
```

You do not need to change `.env` values for local development. Defaults work out of the box.

---

## 2. Pull Ollama Models

Run these on your host machine (not inside Docker):
```bash
ollama pull mistral:latest
ollama pull nomic-embed-text
```

Verify:
```bash
ollama list
```
You should see both models listed.

---

## 3. Set Up n8n

You need an n8n container connected to a Docker network. Two options:

**Option A — Use an existing n8n container**

If you already have n8n running on network `aob-network`, the compose file will join that network automatically. Skip this step.

**Option B — Start n8n fresh**

```bash
docker network create aob-network
docker run -d \
  --name n8n \
  --network aob-network \
  -p 5678:5678 \
  -e GENERIC_TIMEZONE="Asia/Kolkata" \
  -v n8n_data:/home/node/.n8n \
  n8nio/n8n:latest
```

Open `http://localhost:5678` and complete the first-time setup wizard.

---

## 4. Start All Services

```bash
docker compose up -d
```

This starts: PostgreSQL (pgvector), chat_api, gateway_router, embedding_service, llm_service, pricing_api.

Watch logs:
```bash
docker compose logs -f
```

Wait until all containers are healthy (check `docker compose ps`).

---

## 5. Seed the Database

Apply seed data (modules + pricing rules):
```bash
python scripts/seed_db.py
```

Ingest module documentation into pgvector:
```bash
pip install -r scripts/requirements.txt
python scripts/ingest.py
```

---

## 6. Import n8n Workflows

1. Open n8n at `http://localhost:5678`
2. Create a Postgres credential named "RAG Postgres" (see [docs/N8N_WORKFLOWS.md](N8N_WORKFLOWS.md))
3. Import `n8n/workflows/query_workflow_v2.json`
4. Assign "RAG Postgres" to all Postgres nodes in the workflow
5. Activate the workflow

---

## 7. Verify Everything Works

Run the full test suite:
```bash
python scripts/test_all.py
```

All 50 tests should pass.

Quick smoke test:
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"userID":"test1","prompt":"What plans do you offer?"}'
```

---

## Running a Single Service Locally (without Docker)

Useful when you're actively developing one service.

```bash
cd services/chat_api
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Replace `chat_api` with any service name and port accordingly.

You may need to set environment variables manually. Copy from `.env.example` and export them:
```bash
export N8N_WEBHOOK_URL=http://localhost:5678/webhook/chat
```

---

## Service Port Reference

| Service | Port |
|---------|------|
| chat_api | 8000 |
| gateway_router | 8001 |
| embedding_service | 8002 |
| llm_service | 8003 |
| pricing_api | 8004 |
| PostgreSQL | 5432 |
| n8n | 5678 |
| Ollama | 11434 |

All Swagger UI docs available at `http://localhost:<port>/docs`.

---

## Connecting to the Database (DBeaver or psql)

| Field | Value |
|-------|-------|
| Host | `localhost` |
| Port | `5432` |
| Database | `rag_chatbot` |
| User | `rag_user` |
| Password | `change_me_in_production` |

Via command line:
```bash
docker exec -it rag_postgres psql -U rag_user -d rag_chatbot
```

---

## Rebuilding a Service After Code Changes

```bash
docker compose build chat_api
docker compose up -d chat_api
```

Or rebuild everything:
```bash
docker compose up -d --build
```

---

## Resetting the Database (clean slate)

```bash
docker compose down -v          # removes postgres volume
docker compose up -d postgres   # recreates schema from 001_init.sql
python scripts/seed_db.py
python scripts/ingest.py
```

---

## Where to Look for Errors

| Problem | Where to look |
|---------|--------------|
| Chatbot returns 502/503 | `docker compose logs chat_api` |
| n8n workflow failing | n8n UI → Executions tab |
| LLM not responding | `docker compose logs llm_service` and `ollama list` |
| Embeddings failing | `docker compose logs embedding_service` |
| Pricing returning 404 | `docker compose logs pricing_api` — check module IDs |
| Database issues | `docker compose logs postgres` |
