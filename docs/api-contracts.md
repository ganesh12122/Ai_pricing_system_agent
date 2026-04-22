# API Contracts — RAG Sales Chatbot

For non-technical readers, start with:
- [START_HERE.md](START_HERE.md)
- [FLOW_WALKTHROUGH.md](FLOW_WALKTHROUGH.md)

All internal services communicate via HTTP REST. This document defines the exact request/response contracts for each service.

---

## 1. chat_api — Public Gateway

**Base URL:** `http://localhost:8000`

### POST `/chat`

The only endpoint exposed to the integration team.

**Request:**
```json
{
  "userID": "user_abc123",
  "prompt": "which subscription plan will be best for my need"
}
```

| Field    | Type   | Required | Description                                                                 |
|----------|--------|----------|-----------------------------------------------------------------------------|
| `userID` | string | No       | Stable UID for conversation continuity. If omitted, anonymous one-off query |
| `prompt` | string | Yes      | The user's message                                                          |

**Response (200):**
```json
{
  "response": "Based on your requirements, I'd recommend the Professional plan..."
}
```

**Error Response (422):**
```json
{
  "detail": [
    {
      "loc": ["body", "prompt"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**Error Response (503):**
```json
{
  "detail": "Service temporarily unavailable. Please try again."
}
```

---

## 2. gateway_router — Intent Classification

**Base URL:** `http://gateway_router:8001` (internal only)

### POST `/classify`

**Request:**
```json
{
  "message": "how much does the enterprise plan cost for 50 users?",
  "chat_history": [
    {"role": "user", "content": "tell me about your plans"},
    {"role": "assistant", "content": "We offer several subscription tiers..."}
  ]
}
```

| Field          | Type   | Required | Description                     |
|----------------|--------|----------|---------------------------------|
| `message`      | string | Yes      | Current user message            |
| `chat_history` | array  | No       | Recent conversation for context |

**Response (200):**
```json
{
  "intent": "product_pricing",
  "confidence": 0.95,
  "matched_keywords": ["how much", "cost", "plan", "users"]
}
```

| Field              | Type   | Description                                         |
|--------------------|--------|-----------------------------------------------------|
| `intent`           | string | `product_pricing` or `general_doc`                  |
| `confidence`       | float  | 0.0–1.0 confidence score                           |
| `matched_keywords` | array  | Keywords that triggered the classification          |

### GET `/health`

**Response (200):**
```json
{
  "status": "healthy",
  "service": "gateway_router"
}
```

---

## 3. embedding_service — Vector Embedding

**Base URL:** `http://embedding_service:8002` (internal only)

### POST `/embed`

Embed a single text string.

**Request:**
```json
{
  "text": "which subscription plan is best for small business?"
}
```

**Response (200):**
```json
{
  "embedding": [0.0234, -0.0891, 0.0456, ...],
  "model": "nomic-embed-text",
  "dimensions": 768
}
```

### POST `/embed-batch`

Embed multiple texts (for ingestion).

**Request:**
```json
{
  "texts": [
    "Module A handles payroll processing...",
    "Module B provides CRM capabilities..."
  ]
}
```

**Response (200):**
```json
{
  "embeddings": [
    [0.0234, -0.0891, ...],
    [0.0567, -0.0123, ...]
  ],
  "model": "nomic-embed-text",
  "dimensions": 768,
  "count": 2
}
```

### GET `/health`

**Response (200):**
```json
{
  "status": "healthy",
  "service": "embedding_service",
  "model": "nomic-embed-text"
}
```

---

## 4. llm_service — LLM Inference

**Base URL:** `http://llm_service:8003` (internal only)

### POST `/generate`

**Request:**
```json
{
  "user_prompt": "which plan is best for a small business with 15 employees?",
  "system_prompt": "You are a sales advisor...",
  "chat_history": [
    {"role": "user", "content": "hi, I need help choosing a plan"},
    {"role": "assistant", "content": "I'd be happy to help..."}
  ],
  "retrieved_context": [
    {
      "content": "The Professional plan includes payroll, HR, and CRM modules...",
      "metadata": {"module": "Professional Plan", "source": "plans.md"},
      "similarity": 0.89
    }
  ],
  "pricing_data": {
    "modules": [
      {
        "name": "Professional Plan",
        "price_per_user": 25.00,
        "flat_fee": 0,
        "user_count": 15,
        "total": 375.00
      }
    ],
    "grand_total": 375.00,
    "currency": "USD",
    "billing_cycle": "monthly"
  }
}
```

| Field               | Type   | Required | Description                                      |
|---------------------|--------|----------|--------------------------------------------------|
| `user_prompt`       | string | Yes      | The user's current message                       |
| `system_prompt`     | string | Yes      | System prompt defining AI persona/constraints    |
| `chat_history`      | array  | No       | Recent conversation messages                     |
| `retrieved_context` | array  | No       | RAG-retrieved document chunks with similarity    |
| `pricing_data`      | object | No       | Exact pricing from pricing_api (null if general) |

**Response (200):**
```json
{
  "response": "Based on your needs as a small business with 15 employees, I'd recommend our Professional Plan at $25.00 per user per month, totaling $375.00/month. Here's why this plan fits your needs...",
  "model": "mistral:latest",
  "tokens_used": {
    "prompt": 850,
    "completion": 245,
    "total": 1095
  }
}
```

### GET `/health`

**Response (200):**
```json
{
  "status": "healthy",
  "service": "llm_service",
  "backend": "ollama",
  "model": "mistral:latest"
}
```

---

## 5. pricing_api — Pricing Calculation

**Base URL:** `http://pricing_api:8004` (internal only)

### GET `/pricing`

**Query Parameters:**

| Param        | Type   | Required | Description                        |
|--------------|--------|----------|------------------------------------|
| `modules`    | string | Yes      | Comma-separated module names/IDs   |
| `user_count` | int    | No       | Number of users (default: 1)       |

**Example:** `GET /pricing?modules=professional,crm_addon&user_count=15`

**Response (200):**
```json
{
  "modules": [
    {
      "id": "professional",
      "name": "Professional Plan",
      "tier": "professional",
      "price_per_user": 25.00,
      "flat_fee": 0,
      "user_count": 15,
      "subtotal": 375.00
    },
    {
      "id": "crm_addon",
      "name": "CRM Add-on",
      "tier": "addon",
      "price_per_user": 5.00,
      "flat_fee": 0,
      "user_count": 15,
      "subtotal": 75.00
    }
  ],
  "grand_total": 450.00,
  "currency": "USD",
  "billing_cycle": "monthly"
}
```

**Error Response (404):**
```json
{
  "detail": "Module 'unknown_plan' not found"
}
```

### GET `/modules`

List all available modules.

**Response (200):**
```json
{
  "modules": [
    {
      "id": "starter",
      "name": "Starter Plan",
      "description": "Basic features for individuals",
      "category": "plan"
    },
    {
      "id": "professional",
      "name": "Professional Plan",
      "description": "Full suite for small businesses",
      "category": "plan"
    }
  ]
}
```

### GET `/health`

**Response (200):**
```json
{
  "status": "healthy",
  "service": "pricing_api"
}
```

---

## n8n Webhook (Internal — called by chat_api only)

### POST `http://n8n:5678/webhook/chat`

**Request:** Same as chat_api `/chat` — forwarded directly.

```json
{
  "userID": "user_abc123",
  "prompt": "which plan do you recommend?"
}
```

**Response:**
```json
{
  "response": "I'd recommend..."
}
```

---

## Common Patterns

### Health Check Convention

Every service exposes `GET /health` returning:
```json
{
  "status": "healthy",
  "service": "<service_name>"
}
```

### Error Response Convention

All services return errors as:
```json
{
  "detail": "Human-readable error message"
}
```

With appropriate HTTP status codes:
- `400` — Bad request / validation error
- `404` — Resource not found
- `422` — Unprocessable entity
- `500` — Internal server error
- `503` — Upstream service unavailable
