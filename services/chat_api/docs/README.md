# chat_api

**Port**: 8000 | **Owner**: Backend team | **Caller**: Integration team (external)

## Purpose
Public entrypoint for the integration layer. Exposes `POST /chat`, validates payload, forwards requests to n8n webhook, and returns a normalized response.

## Position in Architecture
```
Integration Team / Frontend
        ↓  POST /chat
   [ chat_api :8000 ]   ← YOU ARE HERE
        ↓  POST /webhook/chat
   [ n8n :5678 ]
        ↓  (orchestrates internal services)
```

This is the **only service exposed externally**. All other services are internal to the Docker network.

## Responsibilities
- Accept user messages from external clients.
- Validate request schema (`prompt`, optional `userID`).
- Forward to n8n webhook (`N8N_WEBHOOK_URL`).
- Map upstream/network failures to API-friendly HTTP errors.

## Endpoints
- `POST /chat`
- `GET /health`

### POST /chat
Request:
```json
{
  "userID": "1",
  "prompt": "I need pricing for 50 users"
}
```

Response:
```json
{
  "response": "...assistant reply..."
}
```

Error mapping:
- n8n timeout -> `504`
- n8n non-2xx -> `502`
- transport/network error -> `503`

## Environment Variables
- `N8N_WEBHOOK_URL` (default: `http://n8n:5678/webhook/chat`)

## Dependencies
- FastAPI
- httpx
- pydantic

## Local Run
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Error Handling

| Scenario | HTTP Status | Message |
|----------|-------------|--------|
| Missing `prompt` field | 422 | Validation error detail |
| n8n timeout (>60s) | 504 | Request timed out |
| n8n returned non-2xx | 502 | Upstream error: {status} |
| Network issue | 503 | Service temporarily unavailable |

## Testing

```bash
# Smoke test
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"userID":"1","prompt":"What plans do you offer?"}'

# Health check
curl http://localhost:8000/health

# Swagger UI
open http://localhost:8000/docs
```

Included in `scripts/test_all.py` — tests health check and schema validation.

## Key Design Decisions

- **No business logic here.** Intent routing, embedding, pricing, and LLM are all downstream. This service only validates and proxies.
- **CORS is fully open** (`allow_origins=["*"]`) — integration team controls their domain restrictions at their layer.
- **60 second timeout** on n8n call — LLM can be slow, especially on first request with model cold start.

## Roadmap

See [ROADMAP.md](../../../../ROADMAP.md):
- Phase 3.1: Streaming responses (SSE proxy)
- Phase 4.3: Rate limiting (slowapi, 30 req/min per IP)
