# llm_service

**Port**: 8003 | **Owner**: Backend team | **Caller**: n8n workflow (internal)

## Purpose
Unified text generation service. Builds final LLM messages from system prompt, user prompt, context chunks, pricing data, and history.

## Position in Architecture
```
n8n "Call LLM" node
  ↓  POST /generate  (full assembled payload)
[ llm_service :8003 ]   ← YOU ARE HERE
  ↓  POST /api/chat
[ Ollama :11434 (host machine) ]
  ↓  generated text
 back to n8n → user
```

## Responsibilities
- Assemble model input messages.
- Inject retrieved documentation context into system prompt.
- Inject exact pricing data into system prompt.
- Route generation call to configured backend (`ollama`, `openai`, `vllm`).
- Return standardized response with token usage.

## Endpoints
- `POST /generate`
- `GET /health`

### POST /generate
Request:
```json
{
  "user_prompt": "Suggest module plan for 50 users",
  "system_prompt": "You are a sales engineer...",
  "chat_history": [
    {"role": "user", "content": "hi"},
    {"role": "assistant", "content": "hello"}
  ],
  "retrieved_context": [
    {
      "content": "Starter includes...",
      "metadata": {"source_file": "starter.md"},
      "similarity": 0.94
    }
  ],
  "pricing_data": {
    "grand_total": 375.0,
    "currency": "USD",
    "billing_cycle": "monthly"
  }
}
```

Response:
```json
{
  "response": "Based on your team size...",
  "model": "mistral:latest",
  "tokens_used": {
    "prompt": 120,
    "completion": 180,
    "total": 300
  }
}
```

## Environment Variables
- `INFERENCE_BACKEND` (`ollama` | `openai` | `vllm`)
- `OLLAMA_HOST` (default: `http://ollama:11434`)
- `OLLAMA_MODEL` (example: `mistral:latest`)
- `OPENAI_API_KEY` (required for `openai`/`vllm` mode)
- `OPENAI_BASE_URL` (optional for OpenAI-compatible endpoints)

## Error Handling
- Upstream LLM unavailable -> `503`
- Upstream non-2xx -> `502`
- Unknown backend -> `500`

## Dependencies
- FastAPI
- httpx
- pydantic
- openai

## How Context Is Injected

The `_build_messages()` function assembles messages in this order:

1. **System message** — base persona prompt + retrieved doc chunks (appended) + pricing data (appended)
2. **Chat history messages** — previous turns for the user, oldest first
3. **User message** — current prompt

This order is intentional: system context before history, history before current message.

## Switching Backends

Change `INFERENCE_BACKEND` in `.env`:
- `ollama` — calls `OLLAMA_HOST/api/chat` with `OLLAMA_MODEL`
- `openai` — calls OpenAI API (needs `OPENAI_API_KEY`)
- `vllm` — calls a vLLM instance at `OPENAI_BASE_URL` using OpenAI-compatible API

Zero code changes needed, only env vars.

## Testing

```bash
# Direct LLM test
curl -X POST http://localhost:8003/generate \
  -H "Content-Type: application/json" \
  -d '{"user_prompt": "Say hello in one sentence.", "system_prompt": "You are a helpful assistant."}'

# Health
curl http://localhost:8003/health
# Expected: {"status":"healthy","service":"llm_service","backend":"ollama","model":"mistral:latest"}
```

Included in `scripts/test_all.py` — tests generation, token usage, response non-emptiness.

## Key Design Decisions

- **Pricing injected into system prompt, not user message**: prevents the LLM from treating it as conversational input.
- **Pricing with IMPORTANT constraint**: the prompt explicitly says "Do not recalculate" to prevent math hallucinations.
- **Backend abstraction**: `INFERENCE_BACKEND` flag future-proofs the service — move from Ollama to vLLM or cloud with one env var.

## Local Run
```bash
uvicorn main:app --host 0.0.0.0 --port 8003 --reload
```

## Roadmap

See [ROADMAP.md](../../../../ROADMAP.md):
- Phase 3.1: Streaming responses (SSE)
- Phase 4.1: vLLM swap for high concurrency
- Phase 5.2: Model upgrade path
