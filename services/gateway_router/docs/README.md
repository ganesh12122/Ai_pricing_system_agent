# gateway_router

**Port**: 8001 | **Owner**: Backend team | **Caller**: n8n workflow (internal)

## Purpose
Intent classification service used by n8n to route requests into pricing or general-document branches.

## Position in Architecture
```
n8n
  ↓  POST /classify
[ gateway_router :8001 ]   ← YOU ARE HERE
  ↓  { intent: "product_pricing" | "general_doc" }
n8n Switch node
  ↓                    ↓
Fetch Pricing    No Pricing (doc query)
```

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

## Adding New Keywords

Open `services/gateway_router/main.py` and add a regex to `PRICING_KEYWORDS`:
```python
r"\byour_new_keyword\b",
```
Test immediately — no restart needed if running with `--reload`.

## Error Handling

| Scenario | HTTP Status |
|----------|-------------|
| Empty message | 422 (validation) |
| Internal error | 500 |

This service has no external dependencies so it cannot 503/502.

## Testing

```bash
# Test pricing classification
curl -X POST http://localhost:8001/classify \
  -H "Content-Type: application/json" \
  -d '{"message": "how much for 50 users?"}'

# Expected: { "intent": "product_pricing", "confidence": 0.8, ... }

# Test general doc classification
curl -X POST http://localhost:8001/classify \
  -H "Content-Type: application/json" \
  -d '{"message": "tell me about CRM features"}'
# Expected: { "intent": "general_doc", ... }
```

Included in `scripts/test_all.py` — 9 classification test cases.

## Key Design Decisions

- **Keyword/regex over ML**: ~5ms vs ~2s latency. For a product-specific chatbot with a fixed domain vocabulary, regex handles 95%+ of cases.
- **No state**: fully stateless, fast to scale horizontally.
- **No n8n contract change on upgrade**: the `/classify` response shape is stable. ML can be added behind the same contract.

## Roadmap

See [ROADMAP.md](../../../../ROADMAP.md):
- Phase 2.1: ML classifier fallback (sentence-transformers)
- Phase 2.2: `/extract` endpoint for structured user context parsing
- Phase 3.3: Comparison intent detection
