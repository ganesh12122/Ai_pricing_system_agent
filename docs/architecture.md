# Architecture — RAG Sales Chatbot

## Overview

This system is a **Retrieval-Augmented Generation (RAG)** chatbot that acts as an **AI Sales Engineer**. It analyzes user requirements, recommends software modules, and provides accurate pricing — all through a conversational interface.

**n8n** serves as the **orchestration layer only**. All compute-heavy operations (intent classification, embedding, LLM inference, pricing logic) run in independent **Python FastAPI microservices** that can be scaled, replaced, or upgraded independently.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Integration Team (Website/App)                   │
│                         POST /chat                                  │
│                    { userID?, prompt }                               │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     chat_api (FastAPI :8000)                         │
│              Thin proxy — validation, CORS, rate limiting           │
│              Forwards request to n8n webhook                        │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     n8n Workflow Engine (:5678)                      │
│                     ORCHESTRATION ONLY                               │
│                                                                     │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐        │
│  │ Webhook  │──▶│HTTP Req. │──▶│ IF/Switch│──▶│HTTP Req. │        │
│  │ Trigger  │   │ Nodes    │   │ Nodes    │   │ Nodes    │        │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘        │
│       │              │              │              │                 │
│       │         Calls Python   Routes by      Calls Python          │
│       │         services       intent         services              │
└───────┼──────────────┼──────────────┼──────────────┼────────────────┘
        │              │              │              │
        ▼              ▼              ▼              ▼
┌──────────────────────────────────────────────────────────────┐
│                    Python Microservices                        │
│                                                               │
│  ┌─────────────────┐  ┌─────────────────┐                    │
│  │ gateway_router   │  │ embedding_svc   │                    │
│  │ :8001            │  │ :8002           │                    │
│  │ POST /classify   │  │ POST /embed     │                    │
│  │ keyword/regex    │  │ POST /embed-batch│                   │
│  │ intent routing   │  │ nomic-embed-text│                    │
│  └─────────────────┘  └─────────────────┘                    │
│                                                               │
│  ┌─────────────────┐  ┌─────────────────┐                    │
│  │ llm_service      │  │ pricing_api     │                    │
│  │ :8003            │  │ :8004           │                    │
│  │ POST /generate   │  │ GET /pricing    │                    │
│  │ Ollama/vLLM/     │  │ exact prices    │                    │
│  │ OpenAI backend   │  │ from PostgreSQL │                    │
│  └─────────────────┘  └─────────────────┘                    │
└──────────────────────────────────────────────────────────────┘
        │              │              │              │
        ▼              ▼              ▼              ▼
┌──────────────────────────────────────────────────────────────┐
│                    Data Layer                                  │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐     │
│  │           PostgreSQL + pgvector (:5432)               │     │
│  │                                                       │     │
│  │  ┌──────────────┐  ┌──────────────┐                  │     │
│  │  │document_chunks│  │semantic_cache │                  │     │
│  │  │(RAG vectors) │  │(prompt→answer)│                  │     │
│  │  └──────────────┘  └──────────────┘                  │     │
│  │                                                       │     │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │     │
│  │  │chat_sessions │  │   modules     │  │pricing_rules│ │     │
│  │  │(history)     │  │(product info) │  │(live prices)│ │     │
│  │  └──────────────┘  └──────────────┘  └────────────┘ │     │
│  └─────────────────────────────────────────────────────┘     │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐     │
│  │              Ollama (:11434)                          │     │
│  │              LLM: qwen2.5:7b                         │     │
│  │              Embeddings: nomic-embed-text             │     │
│  └─────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────┘
```

---

## Request Flow (Query Workflow)

```
1. User sends POST /chat { userID?, prompt }
       │
2. chat_api validates → forwards to n8n webhook
       │
3. n8n: HTTP → gateway_router /classify → intent (product_pricing | general_doc)
       │
4. n8n: HTTP → embedding_service /embed → query vector
       │
5. n8n: Postgres → semantic_cache similarity search
       │
6. IF similarity > 0.92 → return cached response (skip LLM) ──→ step 12
       │
7. SWITCH on intent:
       ├─ product_pricing → HTTP → pricing_api /pricing → exact price JSON
       └─ general_doc → pricing = null
       │
8. n8n: Postgres → document_chunks similarity search (top-5 relevant chunks)
       │
9. n8n: Postgres → chat_sessions (last 10 messages for this userID)
       │
10. n8n: Code Node → assemble LLM payload:
        { user_prompt, system_prompt, chat_history, retrieved_context, pricing_data }
       │
11. n8n: HTTP → llm_service /generate → response text
       │
12. n8n: Postgres → INSERT chat_sessions (save conversation)
       │
13. n8n: Postgres → UPSERT semantic_cache (cache for future)
       │
14. n8n: Webhook Response → { response } → chat_api → user
```

---

## Ingestion Flow (Document Indexing)

```
1. Trigger: Manual or webhook on doc update
       │
2. Read module documentation from db/seed/ (Markdown/JSON)
       │
3. Split into chunks (overlapping, ~500 tokens each)
       │
4. HTTP → embedding_service /embed-batch → vectors for each chunk
       │
5. Postgres → UPSERT document_chunks (content + embedding + metadata)
```

---

## Technology Stack

| Component          | Technology                  | License      | Purpose                              |
|--------------------|-----------------------------|--------------|--------------------------------------|
| Orchestration      | n8n (self-hosted)           | Fair-Code    | Workflow orchestration only          |
| LLM                | Qwen 2.5 7B via Ollama     | Apache 2.0   | Response generation                  |
| Embeddings         | nomic-embed-text via Ollama | Apache 2.0   | Text → vector conversion             |
| Vector Database    | PostgreSQL + pgvector       | PostgreSQL   | Vectors, cache, sessions, pricing    |
| Microservices      | Python FastAPI              | MIT          | All compute services                 |
| Containerization   | Docker + Docker Compose     | Apache 2.0   | Deployment & orchestration           |

---

## Service Ports

| Service            | Internal Port | External Port |
|--------------------|---------------|---------------|
| chat_api           | 8000          | 8000          |
| gateway_router     | 8001          | —             |
| embedding_service  | 8002          | —             |
| llm_service        | 8003          | —             |
| pricing_api        | 8004          | —             |
| n8n                | 5678          | 5678          |
| PostgreSQL         | 5432          | 5432          |
| Ollama             | 11434         | 11434         |

> Only `chat_api` (8000) is exposed to the integration team. All other services are internal to the Docker network.

---

## Design Decisions

1. **n8n = orchestration only**: Visual debugging, easy to modify flow, but all heavy compute in Python services. This means we can scale individual services independently.

2. **Keyword-based intent routing**: No LLM call for classification (~5ms vs ~3-5s). Simple keyword matching handles 95%+ of cases for a product-focused chatbot.

3. **Semantic cache**: Repeated similar questions (cosine similarity > 0.92) return cached responses instantly, reducing LLM load by 40-60%.

4. **Pricing API isolation**: LLM NEVER computes prices. The pricing_api returns exact numbers from the database. The LLM only communicates those numbers to the user. This eliminates math hallucination entirely.

5. **Single PostgreSQL instance**: pgvector extension gives us vector DB capabilities without deploying a separate service (no Qdrant/Milvus needed).

6. **Ollama as default, swappable**: `INFERENCE_BACKEND` env var switches between ollama/vllm/openai with zero code changes in the n8n workflow.

---

## Scaling Path

| Stage | Users   | Architecture                                    |
|-------|---------|-------------------------------------------------|
| MVP   | 1-20    | Current setup (single server, Ollama)           |
| Tier 2| 20-100  | Add semantic cache + Redis, tune cache threshold|
| Tier 3| 100-500 | Swap Ollama → vLLM or cloud API (Groq/OpenAI)  |
| Tier 4| 500+    | FastAPI direct calls (bypass n8n), SSE streaming|
