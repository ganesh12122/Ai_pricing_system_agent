# llm_service

## Purpose
Unified text generation service. Builds final LLM messages from system prompt, user prompt, context chunks, pricing data, and history.

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

## Local Run
```bash
uvicorn main:app --host 0.0.0.0 --port 8003 --reload
```
