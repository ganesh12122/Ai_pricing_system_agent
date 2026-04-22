# gateway_router

## Purpose
Intent classification service used by n8n to route requests into pricing or general-document branches.

## Responsibilities
- Lightweight keyword/regex-based intent detection.
- Return intent label with confidence score.

## Endpoints
- `POST /classify`
- `GET /health`

### POST /classify
Request:
```json
{
  "message": "what is the price for enterprise plan?",
  "chat_history": []
}
```

Response:
```json
{
  "intent": "product_pricing",
  "confidence": 0.9,
  "matched_keywords": ["price", "plan"]
}
```

Possible intents:
- `product_pricing`
- `general_doc`

## Classification Logic
- Compiled regex pattern from a pricing keyword list.
- If one or more matches are found -> `product_pricing`.
- Otherwise -> `general_doc`.

## Dependencies
- FastAPI
- pydantic

## Local Run
```bash
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

## Notes
- Current approach is deterministic and fast.
- This can be replaced later with an ML classifier without changing n8n contract.
