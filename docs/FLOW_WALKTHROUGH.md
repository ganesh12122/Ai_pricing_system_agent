# End-to-End Flow Walkthrough

This document explains exactly what happens from user message to final answer.

## Example Input

```json
{
  "userID": "1",
  "prompt": "We are a software company with 50 people. Which plan should we choose?"
}
```

## Step-by-Step

1. User sends request to `chat_api` (`POST /chat`).
2. `chat_api` validates the request and forwards it to n8n webhook.
3. n8n calls `gateway_router` to classify intent:
- `product_pricing` for pricing/subscription questions
- `general_doc` for product knowledge questions
4. n8n calls `embedding_service` to generate embedding for user prompt.
5. n8n checks semantic cache in PostgreSQL:
- If a very similar previous question exists, reuse cached answer.
- Else continue.
6. n8n runs branch logic:
- Pricing branch: calls `pricing_api` for exact numbers.
- General branch: skips pricing and keeps pricing as null.
7. n8n runs RAG retrieval from `document_chunks` (top relevant chunks).
8. n8n fetches chat history for `userID` from `chat_sessions`.
9. n8n assembles payload for `llm_service` with:
- system prompt
- current user prompt
- retrieved context
- chat history
- pricing data (if available)
10. n8n calls `llm_service` to generate final response text.
11. n8n saves latest user and assistant messages into `chat_sessions`.
12. n8n returns final response back through `chat_api`.

## How conversation continuity works

- Continuity key: `userID`
- Every turn stores two messages in `chat_sessions`:
- one row for user message
- one row for assistant message
- Next request with same `userID` fetches latest history and includes it in LLM context.

## How pricing accuracy is enforced

- LLM never computes pricing from scratch.
- `pricing_api` computes pricing from DB rules.
- LLM is instructed to only communicate values from provided pricing context.

## Failure safety

- If LLM is unavailable: API returns service error.
- If pricing data is unavailable on general-doc questions: response still works without pricing section.
- If cache miss: workflow continues normally.
