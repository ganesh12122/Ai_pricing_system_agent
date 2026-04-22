# pricing_api

## Purpose
Returns exact pricing from PostgreSQL based on selected modules and user count. This is the source of truth for pricing values used by responses.

## Responsibilities
- Resolve module pricing tiers from DB rules.
- Compute subtotals and grand total deterministically.
- Return active module catalog.

## Endpoints
- `GET /pricing`
- `GET /modules`
- `GET /health`

### GET /pricing
Query params:
- `modules` (required): comma-separated module IDs
- `user_count` (optional, default `1`, minimum `1`)

Example:
`/pricing?modules=starter,professional&user_count=50`

Response:
```json
{
  "modules": [
    {
      "id": "starter",
      "name": "Starter",
      "tier": "base",
      "price_per_user": 7.0,
      "flat_fee": 0.0,
      "user_count": 50,
      "subtotal": 350.0
    }
  ],
  "grand_total": 350.0,
  "currency": "USD",
  "billing_cycle": "monthly"
}
```

Error cases:
- Missing/empty module list -> `400`
- Unknown module -> `404`

### GET /modules
Returns all active modules.

## Environment Variables
- `DATABASE_URL` (default points to local compose postgres service)

## Dependencies
- FastAPI
- asyncpg
- pydantic

## Local Run
```bash
uvicorn main:app --host 0.0.0.0 --port 8004 --reload
```

## Notes
- Connection pool is initialized on startup and closed on shutdown.
- Health endpoint performs a DB round-trip (`SELECT 1`).
