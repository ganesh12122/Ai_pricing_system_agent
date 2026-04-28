# n8n Workflows Guide

This document explains the n8n workflows: what they do, how to import them, how to configure them, and what each node does.

---

## Overview

n8n acts as the **orchestration layer only**. It does not implement business logic — it connects the Python microservices together in the correct order.

Two workflows exist:
- `query_workflow_v2.json` — handles every incoming chat request
- `ingestion_workflow.json` — indexes document chunks into pgvector

---

## Setup (Fresh n8n Install)

### Step 1 — Create Postgres Credential in n8n

1. Open n8n → Settings → Credentials → New Credential → PostgreSQL
2. Fill in:
   - Host: `rag_postgres` (container name, if n8n is on same Docker network) OR `localhost`
   - Port: `5432`
   - Database: `rag_chatbot`
   - User: `rag_user`
   - Password: `change_me_in_production`
3. Save as **"RAG Postgres"**

> n8n stores credential IDs locally. Every time you import a workflow, you must re-assign the credential in each Postgres node.

### Step 2 — Import Query Workflow

1. n8n → Workflows → Import From File → select `n8n/workflows/query_workflow_v2.json`
2. Open the imported workflow.
3. For every node with a Postgres icon, click it → Credentials → select "RAG Postgres".

   Nodes that need credentials:
   - Check Semantic Cache
   - Increment Cache Hit
   - RAG Search
   - Fetch Chat History
   - Save Chat History

4. Activate the workflow (toggle top-right).

### Step 3 — Import Ingestion Workflow (optional)

1. Import `n8n/workflows/ingestion_workflow.json`.
2. Assign Postgres credentials to the `Upsert to pgvector` node.

---

## Query Workflow — Node-by-Node Reference

### 1. Webhook
- Trigger: `POST http://n8n:5678/webhook/chat`
- Input: `{ "userID": "1", "prompt": "..." }`
- Passes raw request body downstream.

### 2. Classify Intent
- Calls: `POST http://gateway_router:8001/classify`
- Input: `{ message: prompt, chat_history: [] }`
- Output: `{ intent: "product_pricing" | "general_doc", confidence, matched_keywords }`

### 3. Embed Query
- Calls: `POST http://embedding_service:8002/embed`
- Input: `{ text: prompt }`
- Output: `{ embedding: [768 floats], model, dimensions }`

### 4. Build Cache Query (Code node)
- Builds a complete SQL string for semantic cache lookup.
- Uses `.first()` to read embedding from "Embed Query" node.
- Output: `{ query: "SELECT ... FROM semantic_cache WHERE ..." }`
- Reason this is a Code node: n8n's Postgres node strips the `<=>` pgvector operator from SQL. Building SQL in JavaScript avoids this.

### 5. Check Semantic Cache (Postgres)
- Executes the SQL from Build Cache Query.
- `alwaysOutputData: true` ensures workflow continues even if cache is empty.
- Output: zero or one row with `{ id, query_text, response_text, similarity }`

### 6. Cache Hit? (IF node)
- Condition: `similarity >= 0.92`
- True branch → Use Cached Response
- False branch → Switch Intent

### 7. Use Cached Response (Set node)
- True branch only.
- Extracts `response_text` from cache row.

### 8. Increment Cache Hit (Postgres)
- True branch only.
- Updates `hit_count` for the matched cache row.
- → Prepare Save Data

### 9. Switch Intent (Switch node)
- False branch (cache miss) only.
- Routes by intent:
  - `product_pricing` → Fetch Pricing
  - `general_doc` → No Pricing (Doc Query)
  - fallback → No Pricing (Doc Query)

### 10. Fetch Pricing (HTTP Request)
- `product_pricing` branch only.
- Calls: `GET http://pricing_api:8004/pricing?modules=starter,professional,enterprise&user_count=1`
- Note: in the current workflow this uses default modules. Phase 2.2 (User Context Extraction) will make this dynamic.

### 11. Set Pricing Data / No Pricing (Set nodes)
- Set Pricing Data: `pricing_data = JSON.stringify($json)` (full pricing JSON)
- No Pricing: `pricing_data = "null"`

### 12. Build RAG Query (Code node)
- Builds a complete SQL string for vector similarity search in `document_chunks`.
- Uses `.first()` to read embedding from "Embed Query" node.
- Returns top-5 chunks by cosine similarity.
- Same reason as Build Cache Query — Code node avoids `<=>` stripping.

### 13. RAG Search (Postgres)
- Executes the SQL from Build RAG Query.
- `alwaysOutputData: true` — workflow continues even if no chunks found.
- Output: up to 5 rows with `{ content, metadata, similarity }`

### 14. Fetch Chat History (Postgres)
- Fetches last 10 messages for `userID` from `chat_sessions`.
- `alwaysOutputData: true` — anonymous/new users have no history.

### 15. Assemble LLM Payload (Code node)
- Core assembly step.
- Reads from: Webhook, Embed Query, RAG Search, Fetch Chat History, Set Pricing Data / No Pricing.
- All reads use `.first()` or `.all()` — never `.item` (avoids paired-item crash).
- Builds final payload: `{ user_prompt, system_prompt, chat_history, retrieved_context, pricing_data }`

### 16. Call LLM (HTTP Request)
- Calls: `POST http://llm_service:8003/generate`
- Input: assembled payload from previous node.
- 120 second timeout (LLM can be slow).

### 17. Set LLM Response (Set node)
- Extracts `response`, and also passes through `user_prompt` and `userID` for downstream use.
- This is the critical bridging node so Prepare Save Data can read from `$input.item.json`.

### 18. Prepare Save Data (Code node)
- Reads `$input.item.json` (direct predecessor only — no distant node references).
- Escapes single quotes in all strings for safe SQL.
- Builds INSERT SQL string.
- Output: `{ saveQuery, response }`

### 19. Save Chat History (Postgres)
- Executes the INSERT from Prepare Save Data.
- Saves both user and assistant messages.

### 20. Final Response (Set node)
- Last node in workflow.
- Returns `{ response }` as the webhook response body.

---

## Ingestion Workflow

### Trigger
Manual trigger (click "Execute" in n8n) or webhook.

### Flow
1. Read markdown docs from `db/seed/modules/` (done via Python ingestion script, not n8n today).
2. Chunk documents.
3. Call `POST /embed-batch` on embedding_service.
4. Upsert into `document_chunks` via Postgres node.

> Note: It is simpler and more reliable to run `python scripts/ingest.py` directly. The n8n ingestion workflow is kept for teams who want a UI-triggered ingestion pipeline.

---

## Common n8n Issues

### Error: "Paired item unavailable"
- Cause: Code node is using `$('NodeName').item` which requires unbroken paired-item tracking.
- Fix: Change `.item` to `.first()` anywhere you are referencing a non-adjacent node in a Code node.

### Postgres node strips `<=>` operator
- Cause: n8n sanitizes SQL and removes unknown operators.
- Fix: Build the full SQL string in a Code node and pass it as `{{ $json.query }}`.

### Workflow runs but cache never populates
- Cause: Semantic cache write-back is not yet implemented (Phase 2.4).
- Result: Every request goes to the LLM. This is expected current behavior.

### Credential ID mismatch after import
- Cause: Credential IDs are local to each n8n instance.
- Fix: After importing workflow, open each Postgres node and re-select "RAG Postgres" credential.
