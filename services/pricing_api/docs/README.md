# pricing_api

**Port**: 8004 | **Owner**: Backend team | **Caller**: n8n workflow (internal)

## Purpose
Returns exact pricing from PostgreSQL based on selected modules and user count. This is the **single source of truth** for all pricing. The LLM never calculates — it only communicates numbers returned by this service.

## Position in Architecture
```
n8n "Fetch Pricing" node (product_pricing branch only)
  ↓  GET /pricing?modules=...&user_count=...
[ pricing_api :8004 ]   ← YOU ARE HERE
  ↓  asyncpg pool → PostgreSQL
  ↓  {modules, grand_total, currency, billing_cycle}
n8n → injected into LLM system prompt as "Exact Pricing Data"
```

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

## How Tier-Based Pricing Works

For each module, `pricing_rules` table may have multiple rows with different `user_count_min/max` bands. The query selects the one matching row where:

```
user_count_min <= requested_user_count <= user_count_max
```

Example: Module "professional" may have:
- 1-10 users → $15/user
- 11-50 users → $12/user
- 51+ users → $9/user

`subtotal = (price_per_user × user_count) + flat_fee`

## Adding New Pricing Rules

Edit `db/seed/002_seed_data.sql` and run:
```bash
python scripts/seed_db.py
```

Or insert directly:
```sql
INSERT INTO pricing_rules (module_id, tier, user_count_min, user_count_max, price_per_user, flat_fee)
VALUES ('starter', 'growth', 11, 50, 5.00, 0.00);
```

## Testing

```bash
# Get pricing for starter + professional, 50 users
curl "http://localhost:8004/pricing?modules=starter,professional&user_count=50"

# List all modules
curl http://localhost:8004/modules

# Health (tests DB round-trip)
curl http://localhost:8004/health
```

Included in `scripts/test_all.py` — tests pricing calculation, module listing, edge cases.

## Key Design Decisions

- **Pricing isolation**: The LLM service receives exact dollar values and is instructed not to recalculate. This eliminates math hallucinations entirely.
- **asyncpg connection pool**: min_size=2, max_size=10. Safe for concurrent requests.
- **Health check hits DB**: if PostgreSQL is down, the service correctly returns 503.

## Notes
- Connection pool is initialized on startup (`@app.on_event("startup")`) and closed on shutdown.
- Health endpoint performs a DB round-trip (`SELECT 1`) to validate connectivity.

## Roadmap

See [ROADMAP.md](../../../../ROADMAP.md):
- Phase 4.4: Admin API for module management (`POST /modules`, `PUT /modules/{id}`)
