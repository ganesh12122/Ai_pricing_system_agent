# RAG Sales Chatbot

An AI-powered Sales Engineer chatbot using Retrieval-Augmented Generation (RAG). Built with **n8n** for orchestration and **Python FastAPI** microservices for compute.

## Architecture

```
Integration Team → POST /chat → chat_api → n8n webhook → [gateway_router, embedding_service, pgvector, pricing_api, llm_service] → response
```

n8n acts as the orchestration layer only. All heavy compute (intent classification, embedding, LLM inference, pricing) runs in independent Python FastAPI services.

See [docs/architecture.md](docs/architecture.md) for full architecture diagrams.

## Quick Start

### Prerequisites

- Docker & Docker Compose
- NVIDIA GPU + drivers (for Ollama)
- Git

### 1. Clone & Configure

```bash
git clone https://github.com/ganesh12122/Ai_pricing_system_agent.git
cd Ai_pricing_system_agent
cp .env.example .env
# Edit .env with your credentials
```

### 2. Start All Services

```bash
docker compose up -d
```

This starts: PostgreSQL (pgvector), Ollama, n8n, chat_api, gateway_router, embedding_service, llm_service, pricing_api.

### 3. Pull Ollama Models

```bash
docker exec rag_ollama ollama pull qwen2.5:7b
docker exec rag_ollama ollama pull nomic-embed-text
```

### 4. Test

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What subscription plans do you offer?"}'
```

## Project Structure

```
RAG_CHATBOT/
├── docs/                         # Documentation
│   ├── architecture.md           # System architecture & diagrams
│   ├── api-contracts.md          # API specifications per service
│   ├── system-prompt.md          # AI Sales Engineer system prompt
│   ├── project_plan_shared_by_team.MD  # Management requirements
│   └── reviced_plan_from_teammate.md   # Teammate's workflow plan
├── services/
│   ├── chat_api/                 # Public gateway — POST /chat
│   ├── gateway_router/           # Intent classification (keyword-based)
│   ├── embedding_service/        # Text → vector (nomic-embed-text)
│   ├── llm_service/              # LLM inference (Ollama/vLLM/OpenAI)
│   └── pricing_api/              # Exact pricing from database
├── n8n/
│   └── workflows/                # Exported n8n workflow JSONs
├── db/
│   ├── migrations/               # SQL schema migrations
│   └── seed/                     # Module documentation & seed data
├── docker-compose.yml            # Full stack orchestration
├── .env.example                  # Environment variable template
└── README.md
```

## Services

| Service           | Port | Purpose                                       |
|-------------------|------|-----------------------------------------------|
| chat_api          | 8000 | Public API gateway (only exposed endpoint)    |
| gateway_router    | 8001 | Intent classification (keyword/regex)         |
| embedding_service | 8002 | Text embedding via Ollama                     |
| llm_service       | 8003 | LLM response generation                      |
| pricing_api       | 8004 | Exact pricing calculation from DB             |
| n8n               | 5678 | Workflow orchestration                        |
| PostgreSQL        | 5432 | Database (pgvector, cache, sessions, pricing) |
| Ollama            | 11434| LLM & embedding model server                 |

## API

### POST `/chat`

```json
// Request
{
  "userID": "optional_uid",
  "prompt": "which plan is best for my small business?"
}

// Response
{
  "response": "Based on your needs, I'd recommend..."
}
```

See [docs/api-contracts.md](docs/api-contracts.md) for all service APIs.

## Tech Stack

| Component     | Technology              | License    |
|---------------|-------------------------|------------|
| Orchestration | n8n                     | Fair-Code  |
| LLM           | Qwen 2.5 7B (Ollama)   | Apache 2.0 |
| Embeddings    | nomic-embed-text        | Apache 2.0 |
| Vector DB     | PostgreSQL + pgvector   | PostgreSQL |
| Services      | Python FastAPI          | MIT        |
| Containers    | Docker Compose          | Apache 2.0 |

## Documentation

- [Architecture](docs/architecture.md) — System design, data flow, scaling path
- [API Contracts](docs/api-contracts.md) — Request/response specs for all services
- [System Prompt](docs/system-prompt.md) — AI Sales Engineer persona & constraints
