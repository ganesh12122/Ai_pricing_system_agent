# RAG Sales Chatbot

An AI-powered Sales Engineer chatbot using Retrieval-Augmented Generation (RAG). Built with **n8n** for orchestration and **Python FastAPI** microservices for compute.

> **New to this project?** Start with [docs/START_HERE.md](docs/START_HERE.md) — plain-English intro, no technical experience required.

## What it does

Users chat with an AI Sales Engineer that:
- Understands their business requirements
- Recommends the right software modules with reasons
- Provides **exact pricing from the database** (never invented by AI)
- Remembers conversation history per user

## Architecture

```
Integration Team → POST /chat → chat_api → n8n workflow → [gateway_router, embedding_service, pgvector, pricing_api, llm_service] → response
```

n8n acts as the **orchestration layer only**. All compute (intent classification, embedding, LLM inference, pricing) runs in independent Python FastAPI microservices.

## Quick Start

### Prerequisites

| Tool | Notes |
|------|-------|
| Docker & Docker Compose | For running services |
| [Ollama](https://ollama.com) | Installed on host machine, not containerized |
| n8n | Can use an existing container or start fresh — see [docs/DEVELOPMENT_GUIDE.md](docs/DEVELOPMENT_GUIDE.md) |
| Python 3.11+ | For running seed/ingest/test scripts |
| Git | — |

### Step 1 — Clone and configure

```bash
git clone <repo-url>
cd RAG_CHATBOT
cp .env.example .env
```

### Step 2 — Pull Ollama models (on host)

```bash
ollama pull mistral:latest
ollama pull nomic-embed-text
```

### Step 3 — Start services

```bash
docker compose up -d
```

Starts: PostgreSQL (pgvector), chat_api, gateway_router, embedding_service, llm_service, pricing_api.

### Step 4 — Seed data and ingest docs

```bash
python scripts/seed_db.py     # modules + pricing rules
python scripts/ingest.py      # embed module docs into pgvector
```

### Step 5 — Import n8n workflow

See [docs/N8N_WORKFLOWS.md](docs/N8N_WORKFLOWS.md) for step-by-step import instructions.

### Step 6 — Run tests

```bash
python scripts/test_all.py    # all 50 tests should pass
```

### Step 7 — Smoke test

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"userID":"1","prompt":"What plans do you offer?"}'
```

## Project Structure

```
RAG_CHATBOT/
├── CONTRIBUTING.md               # How to contribute
├── CHANGELOG.md                  # What's been built and changed
├── ROADMAP.md                    # Enhancement and scale plan
├── docs/
│   ├── README.md                 # Documentation hub and reading order
│   ├── START_HERE.md             # Non-technical overview
│   ├── FLOW_WALKTHROUGH.md       # Step-by-step request lifecycle
│   ├── DEVELOPMENT_GUIDE.md      # Full local dev setup guide
│   ├── N8N_WORKFLOWS.md          # n8n import guide + node reference
│   ├── DATABASE.md               # Schema reference + useful queries
│   ├── architecture.md           # System architecture & diagrams
│   ├── api-contracts.md          # Request/response specs per service
│   ├── system-prompt.md          # AI Sales Engineer persona
│   └── RUNBOOK.md                # Operations and troubleshooting
├── services/
│   ├── chat_api/                 # Public gateway — POST /chat :8000
│   ├── gateway_router/           # Intent classification :8001
│   ├── embedding_service/        # Text → vector (nomic-embed-text) :8002
│   ├── llm_service/              # LLM inference (Ollama/vLLM/OpenAI) :8003
│   └── pricing_api/              # Exact pricing from DB :8004
│       (each has docs/ subfolder with service-level documentation)
├── n8n/workflows/                # Exported n8n workflow JSONs
├── db/
│   ├── migrations/001_init.sql   # Full schema (auto-applied)
│   └── seed/                     # Seed SQL + module markdown docs
├── scripts/
│   ├── seed_db.py                # Populate modules + pricing rules
│   ├── ingest.py                 # Embed docs into pgvector
│   └── test_all.py               # 50-test automated test suite
├── docker-compose.yml
├── .env.example
└── README.md
```

## Services

| Service | Port | Purpose |
|---------|------|---------|
| chat_api | 8000 | **Only public endpoint** — integration team calls this |
| gateway_router | 8001 | Intent classification (internal only) |
| embedding_service | 8002 | Text → vector via Ollama (internal only) |
| llm_service | 8003 | LLM response generation (internal only) |
| pricing_api | 8004 | Exact pricing from DB (internal only) |
| n8n | 5678 | Workflow orchestration |
| PostgreSQL | 5432 | Database (vectors, cache, history, pricing) |
| Ollama | 11434 | LLM + embedding model server (host machine) |

## API

The integration team only needs one endpoint:

```
POST http://localhost:8000/chat

Request:  { "userID": "optional", "prompt": "your message" }
Response: { "response": "..." }
```

Full specs: [docs/api-contracts.md](docs/api-contracts.md)

## Tech Stack

| Component | Technology | License |
|-----------|-----------|---------|
| Orchestration | n8n (self-hosted) | Fair-Code |
| LLM | Mistral via Ollama | Apache 2.0 |
| Embeddings | nomic-embed-text via Ollama | Apache 2.0 |
| Vector DB | PostgreSQL + pgvector | PostgreSQL |
| Services | Python 3.11 FastAPI | MIT |
| Containers | Docker Compose | Apache 2.0 |

## Documentation

| Document | Audience | Description |
|----------|----------|-------------|
| [docs/README.md](docs/README.md) | Everyone | Navigation hub |
| [docs/START_HERE.md](docs/START_HERE.md) | Non-technical | Plain-English overview |
| [docs/FLOW_WALKTHROUGH.md](docs/FLOW_WALKTHROUGH.md) | Everyone | Request lifecycle walkthrough |
| [docs/DEVELOPMENT_GUIDE.md](docs/DEVELOPMENT_GUIDE.md) | Developers | Full setup from zero |
| [docs/N8N_WORKFLOWS.md](docs/N8N_WORKFLOWS.md) | Developers | n8n import + node reference |
| [docs/DATABASE.md](docs/DATABASE.md) | Developers | Schema + useful queries |
| [docs/architecture.md](docs/architecture.md) | Developers | Architecture diagrams |
| [docs/api-contracts.md](docs/api-contracts.md) | Integration team | API specs |
| [docs/RUNBOOK.md](docs/RUNBOOK.md) | Operations | Run and troubleshoot |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contributors | How to contribute |
| [ROADMAP.md](ROADMAP.md) | Everyone | Enhancement and scale plan |
| [CHANGELOG.md](CHANGELOG.md) | Everyone | What has been built |

## Service Documentation

Each service has its own doc:
[chat_api](services/chat_api/docs/README.md) · [gateway_router](services/gateway_router/docs/README.md) · [embedding_service](services/embedding_service/docs/README.md) · [llm_service](services/llm_service/docs/README.md) · [pricing_api](services/pricing_api/docs/README.md)
