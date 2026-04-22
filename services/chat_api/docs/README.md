# chat_api

## Purpose
Public entrypoint for the integration layer. Exposes `POST /chat`, validates payload, forwards requests to n8n webhook, and returns a normalized response.

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

## Notes
- CORS is fully open (`*`) for integration flexibility.
- This service intentionally does not contain business logic.
