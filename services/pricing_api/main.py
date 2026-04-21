import os
from decimal import Decimal
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
import asyncpg

app = FastAPI(title="Pricing API", version="1.0.0")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://rag_user:change_me_in_production@postgres:5432/rag_chatbot",
)

pool: Optional[asyncpg.Pool] = None


@app.on_event("startup")
async def startup():
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)


@app.on_event("shutdown")
async def shutdown():
    if pool:
        await pool.close()


class ModulePrice(BaseModel):
    id: str
    name: str
    tier: str
    price_per_user: float
    flat_fee: float
    user_count: int
    subtotal: float


class PricingResponse(BaseModel):
    modules: list[ModulePrice]
    grand_total: float
    currency: str
    billing_cycle: str


class ModuleInfo(BaseModel):
    id: str
    name: str
    description: str
    category: str


class ModulesListResponse(BaseModel):
    modules: list[ModuleInfo]


@app.get("/pricing", response_model=PricingResponse)
async def get_pricing(
    modules: str = Query(..., description="Comma-separated module IDs"),
    user_count: int = Query(1, ge=1, description="Number of users"),
):
    module_ids = [m.strip() for m in modules.split(",") if m.strip()]
    if not module_ids:
        raise HTTPException(status_code=400, detail="At least one module ID is required")

    results = []
    grand_total = Decimal("0.00")

    async with pool.acquire() as conn:
        for mod_id in module_ids:
            row = await conn.fetchrow(
                """
                SELECT m.id, m.name, pr.tier, pr.price_per_user, pr.flat_fee,
                       pr.currency, pr.billing_cycle
                FROM modules m
                JOIN pricing_rules pr ON m.id = pr.module_id
                WHERE m.id = $1
                  AND m.is_active = TRUE
                  AND pr.is_active = TRUE
                  AND pr.user_count_min <= $2
                  AND (pr.user_count_max IS NULL OR pr.user_count_max >= $2)
                ORDER BY pr.price_per_user ASC
                LIMIT 1
                """,
                mod_id,
                user_count,
            )
            if not row:
                raise HTTPException(status_code=404, detail=f"Module '{mod_id}' not found")

            subtotal = (row["price_per_user"] * user_count) + row["flat_fee"]
            grand_total += subtotal

            results.append(
                ModulePrice(
                    id=row["id"],
                    name=row["name"],
                    tier=row["tier"],
                    price_per_user=float(row["price_per_user"]),
                    flat_fee=float(row["flat_fee"]),
                    user_count=user_count,
                    subtotal=float(subtotal),
                )
            )

    currency = "USD"
    billing_cycle = "monthly"
    if results:
        # Use currency/billing from first result (assumed consistent)
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT currency, billing_cycle FROM pricing_rules WHERE module_id = $1 AND is_active = TRUE LIMIT 1",
                module_ids[0],
            )
            if row:
                currency = row["currency"]
                billing_cycle = row["billing_cycle"]

    return PricingResponse(
        modules=results,
        grand_total=float(grand_total),
        currency=currency,
        billing_cycle=billing_cycle,
    )


@app.get("/modules", response_model=ModulesListResponse)
async def list_modules():
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, name, description, category FROM modules WHERE is_active = TRUE ORDER BY name"
        )
    return ModulesListResponse(
        modules=[
            ModuleInfo(
                id=row["id"],
                name=row["name"],
                description=row["description"],
                category=row["category"],
            )
            for row in rows
        ]
    )


@app.get("/health")
async def health():
    try:
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return {"status": "healthy", "service": "pricing_api"}
    except Exception:
        raise HTTPException(status_code=503, detail="Database connection failed")
