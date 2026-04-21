"""
RAG Sales Chatbot — Aggressive Automated Test Suite

Tests all microservices independently + integration flows.
Run with: python scripts/test_all.py

Requirements: pip install httpx asyncpg
"""

import asyncio
import json
import sys
import time
import httpx

# Service URLs (host-side ports)
CHAT_API = "http://localhost:8000"
GATEWAY_ROUTER = "http://localhost:8001"
EMBEDDING_SERVICE = "http://localhost:8002"
LLM_SERVICE = "http://localhost:8003"
PRICING_API = "http://localhost:8004"
OLLAMA = "http://localhost:11434"

PASS = 0
FAIL = 0
ERRORS = []


def result(name: str, passed: bool, detail: str = ""):
    global PASS, FAIL
    if passed:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        ERRORS.append(f"{name}: {detail}")
        print(f"  [FAIL] {name} — {detail}")


async def test_health_checks():
    """Test all service health endpoints."""
    print("\n=== 1. Health Checks ===")
    services = {
        "chat_api": CHAT_API,
        "gateway_router": GATEWAY_ROUTER,
        "embedding_service": EMBEDDING_SERVICE,
        "llm_service": LLM_SERVICE,
        "pricing_api": PRICING_API,
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        for name, url in services.items():
            try:
                resp = await client.get(f"{url}/health")
                data = resp.json()
                result(
                    f"{name} /health",
                    resp.status_code == 200 and data.get("status") == "healthy",
                    f"status={resp.status_code}, body={data}",
                )
            except Exception as e:
                result(f"{name} /health", False, str(e))


async def test_ollama_local():
    """Test local Ollama is reachable and has required models."""
    print("\n=== 2. Local Ollama ===")
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(f"{OLLAMA}/api/tags")
            data = resp.json()
            models = [m["name"] for m in data.get("models", [])]
            result("Ollama reachable", resp.status_code == 200)
            result("mistral model available", any("mistral" in m for m in models), f"models: {models}")
            result("nomic-embed-text available", any("nomic-embed" in m for m in models), f"models: {models}")
        except Exception as e:
            result("Ollama reachable", False, str(e))


async def test_gateway_router():
    """Test intent classification with various queries."""
    print("\n=== 3. Gateway Router — Intent Classification ===")
    test_cases = [
        ("How much does the professional plan cost?", "product_pricing"),
        ("What is the price for 50 users?", "product_pricing"),
        ("I want to subscribe to the enterprise plan", "product_pricing"),
        ("Can you help me buy a plan?", "product_pricing"),
        ("What modules do you offer?", "product_pricing"),
        ("Tell me about your company", "general_doc"),
        ("How does payroll processing work?", "general_doc"),
        ("What security features do you have?", "general_doc"),
        ("Explain the CRM capabilities", "general_doc"),
    ]
    async with httpx.AsyncClient(timeout=10.0) as client:
        for message, expected_intent in test_cases:
            try:
                resp = await client.post(
                    f"{GATEWAY_ROUTER}/classify",
                    json={"message": message},
                )
                data = resp.json()
                actual_intent = data.get("intent")
                result(
                    f"classify '{message[:40]}...' → {expected_intent}",
                    actual_intent == expected_intent,
                    f"got {actual_intent} (confidence={data.get('confidence')})",
                )
            except Exception as e:
                result(f"classify '{message[:40]}...'", False, str(e))


async def test_embedding_service():
    """Test single and batch embedding."""
    print("\n=== 4. Embedding Service ===")
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Single embed
        try:
            resp = await client.post(
                f"{EMBEDDING_SERVICE}/embed",
                json={"text": "What subscription plans do you offer?"},
            )
            data = resp.json()
            emb = data.get("embedding", [])
            result("single embed", resp.status_code == 200 and len(emb) > 0, f"dim={len(emb)}")
            result("embedding dimensions", len(emb) == 768, f"got {len(emb)}, expected 768")
            result("embedding model correct", data.get("model") == "nomic-embed-text", f"model={data.get('model')}")
        except Exception as e:
            result("single embed", False, str(e))

        # Batch embed
        try:
            resp = await client.post(
                f"{EMBEDDING_SERVICE}/embed-batch",
                json={"texts": ["hello world", "pricing plans", "CRM features"]},
            )
            data = resp.json()
            result(
                "batch embed (3 texts)",
                resp.status_code == 200 and data.get("count") == 3,
                f"count={data.get('count')}",
            )
        except Exception as e:
            result("batch embed", False, str(e))

        # Empty text validation
        try:
            resp = await client.post(f"{EMBEDDING_SERVICE}/embed", json={"text": ""})
            result("empty text rejected", resp.status_code == 422)
        except Exception as e:
            result("empty text rejected", False, str(e))


async def test_llm_service():
    """Test LLM generation with different payloads."""
    print("\n=== 5. LLM Service ===")
    async with httpx.AsyncClient(timeout=120.0) as client:
        # Basic generation
        try:
            t0 = time.time()
            resp = await client.post(
                f"{LLM_SERVICE}/generate",
                json={
                    "user_prompt": "Hello, what plans do you offer?",
                    "system_prompt": "You are a helpful sales advisor. Be brief.",
                    "chat_history": [],
                    "retrieved_context": [],
                    "pricing_data": None,
                },
            )
            latency = time.time() - t0
            data = resp.json()
            result(
                f"basic generation ({latency:.1f}s)",
                resp.status_code == 200 and len(data.get("response", "")) > 10,
                f"response_len={len(data.get('response', ''))}",
            )
            result("model is mistral", "mistral" in data.get("model", ""), f"model={data.get('model')}")
            result("tokens reported", data.get("tokens_used", {}).get("total", 0) > 0)
        except Exception as e:
            result("basic generation", False, str(e))

        # Generation with context
        try:
            resp = await client.post(
                f"{LLM_SERVICE}/generate",
                json={
                    "user_prompt": "What plan is best for a team of 15?",
                    "system_prompt": "You are a sales advisor. ONLY use pricing in context. Be brief.",
                    "chat_history": [
                        {"role": "user", "content": "Hi"},
                        {"role": "assistant", "content": "Hello! How can I help?"},
                    ],
                    "retrieved_context": [
                        {
                            "content": "Professional Plan: Designed for small to medium businesses. Includes HR, payroll, CRM.",
                            "metadata": {"source_file": "professional_plan.md"},
                            "similarity": 0.89,
                        }
                    ],
                    "pricing_data": {
                        "modules": [{"name": "Professional Plan", "price_per_user": 21.99, "user_count": 15, "subtotal": 329.85}],
                        "grand_total": 329.85,
                        "currency": "USD",
                        "billing_cycle": "monthly",
                    },
                },
            )
            data = resp.json()
            response_text = data.get("response", "")
            result(
                "generation with context + pricing",
                resp.status_code == 200 and len(response_text) > 20,
                f"len={len(response_text)}",
            )
            # Check if response mentions the price (should use exact pricing)
            result(
                "response references pricing data",
                "329" in response_text or "21.99" in response_text or "Professional" in response_text,
                f"response: {response_text[:100]}...",
            )
        except Exception as e:
            result("generation with context", False, str(e))


async def test_pricing_api():
    """Test pricing API with database queries."""
    print("\n=== 6. Pricing API ===")
    async with httpx.AsyncClient(timeout=10.0) as client:
        # List modules
        try:
            resp = await client.get(f"{PRICING_API}/modules")
            data = resp.json()
            modules = data.get("modules", [])
            result(
                "list modules",
                resp.status_code == 200 and len(modules) >= 7,
                f"count={len(modules)}",
            )
        except Exception as e:
            result("list modules", False, str(e))

        # Get pricing for single module
        try:
            resp = await client.get(f"{PRICING_API}/pricing", params={"modules": "professional", "user_count": 15})
            data = resp.json()
            result(
                "pricing: professional, 15 users",
                resp.status_code == 200 and data.get("grand_total") == 329.85,
                f"total={data.get('grand_total')}",
            )
            result("currency is USD", data.get("currency") == "USD")
            result("billing is monthly", data.get("billing_cycle") == "monthly")
        except Exception as e:
            result("pricing: professional", False, str(e))

        # Get pricing for multiple modules
        try:
            resp = await client.get(
                f"{PRICING_API}/pricing",
                params={"modules": "professional,crm_addon", "user_count": 15},
            )
            data = resp.json()
            expected_total = (15 * 21.99) + (15 * 7.99)  # 329.85 + 119.85 = 449.70
            result(
                "pricing: professional + crm_addon",
                resp.status_code == 200 and abs(data.get("grand_total", 0) - expected_total) < 0.01,
                f"total={data.get('grand_total')}, expected={expected_total}",
            )
        except Exception as e:
            result("pricing: multi-module", False, str(e))

        # Pricing tier boundaries
        try:
            resp = await client.get(f"{PRICING_API}/pricing", params={"modules": "starter", "user_count": 1})
            data = resp.json()
            result(
                "starter 1 user = $9.99",
                data.get("grand_total") == 9.99,
                f"total={data.get('grand_total')}",
            )

            resp = await client.get(f"{PRICING_API}/pricing", params={"modules": "starter", "user_count": 5})
            data = resp.json()
            result(
                "starter 5 users = $44.95",
                abs(data.get("grand_total", 0) - 44.95) < 0.01,
                f"total={data.get('grand_total')}",
            )
        except Exception as e:
            result("pricing tiers", False, str(e))

        # Enterprise with flat fee
        try:
            resp = await client.get(f"{PRICING_API}/pricing", params={"modules": "enterprise", "user_count": 75})
            data = resp.json()
            expected = (75 * 49.99) + 500  # 3749.25 + 500 = 4249.25
            result(
                "enterprise 75 users (with platform fee)",
                abs(data.get("grand_total", 0) - expected) < 0.01,
                f"total={data.get('grand_total')}, expected={expected}",
            )
        except Exception as e:
            result("enterprise pricing", False, str(e))

        # Invalid module
        try:
            resp = await client.get(f"{PRICING_API}/pricing", params={"modules": "nonexistent", "user_count": 1})
            result("invalid module returns 404", resp.status_code == 404)
        except Exception as e:
            result("invalid module", False, str(e))


async def test_chat_api():
    """Test the public-facing chat endpoint."""
    print("\n=== 7. Chat API (Public Gateway) ===")
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Health check
        try:
            resp = await client.get(f"{CHAT_API}/health")
            result("chat_api /health", resp.status_code == 200)
        except Exception as e:
            result("chat_api /health", False, str(e))

        # Validation: missing prompt
        try:
            resp = await client.post(f"{CHAT_API}/chat", json={"userID": "test"})
            result("missing prompt → 422", resp.status_code == 422)
        except Exception as e:
            result("validation: missing prompt", False, str(e))

        # Validation: empty prompt
        try:
            resp = await client.post(f"{CHAT_API}/chat", json={"prompt": ""})
            result("empty prompt → 422", resp.status_code == 422)
        except Exception as e:
            result("validation: empty prompt", False, str(e))


async def test_postgres_schema():
    """Test that all tables exist with correct schema."""
    print("\n=== 8. PostgreSQL Schema ===")
    try:
        import asyncpg
    except ImportError:
        result("asyncpg installed", False, "pip install asyncpg")
        return

    try:
        conn = await asyncpg.connect(
            "postgresql://rag_user:change_me_in_production@localhost:5432/rag_chatbot"
        )
        try:
            # Check tables exist
            tables = await conn.fetch(
                "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
            )
            table_names = [t["tablename"] for t in tables]
            for expected in ["document_chunks", "semantic_cache", "chat_sessions", "modules", "pricing_rules"]:
                result(f"table '{expected}' exists", expected in table_names, f"tables: {table_names}")

            # Check pgvector extension
            ext = await conn.fetchval("SELECT COUNT(*) FROM pg_extension WHERE extname = 'vector'")
            result("pgvector extension enabled", ext > 0)

            # Check seed data loaded
            module_count = await conn.fetchval("SELECT COUNT(*) FROM modules")
            result(f"modules seeded ({module_count})", module_count >= 7, f"count={module_count}")

            pricing_count = await conn.fetchval("SELECT COUNT(*) FROM pricing_rules")
            result(f"pricing_rules seeded ({pricing_count})", pricing_count >= 13, f"count={pricing_count}")
        finally:
            await conn.close()
    except Exception as e:
        result("PostgreSQL connection", False, str(e))


async def test_embedding_consistency():
    """Test that same text produces same embedding (deterministic)."""
    print("\n=== 9. Embedding Consistency ===")
    async with httpx.AsyncClient(timeout=30.0) as client:
        text = "What is the best plan for small businesses?"
        try:
            resp1 = await client.post(f"{EMBEDDING_SERVICE}/embed", json={"text": text})
            resp2 = await client.post(f"{EMBEDDING_SERVICE}/embed", json={"text": text})
            emb1 = resp1.json()["embedding"]
            emb2 = resp2.json()["embedding"]

            # Compute cosine similarity
            dot = sum(a * b for a, b in zip(emb1, emb2))
            norm1 = sum(a * a for a in emb1) ** 0.5
            norm2 = sum(b * b for b in emb2) ** 0.5
            similarity = dot / (norm1 * norm2) if norm1 * norm2 > 0 else 0

            result(
                f"same text → same embedding (similarity={similarity:.6f})",
                similarity > 0.999,
                f"similarity={similarity}",
            )
        except Exception as e:
            result("embedding consistency", False, str(e))

        # Test similar texts produce similar embeddings
        try:
            resp_a = await client.post(f"{EMBEDDING_SERVICE}/embed", json={"text": "How much does the professional plan cost?"})
            resp_b = await client.post(f"{EMBEDDING_SERVICE}/embed", json={"text": "What is the price of the pro plan?"})
            resp_c = await client.post(f"{EMBEDDING_SERVICE}/embed", json={"text": "Tell me about elephants in Africa"})

            emb_a = resp_a.json()["embedding"]
            emb_b = resp_b.json()["embedding"]
            emb_c = resp_c.json()["embedding"]

            def cosine_sim(x, y):
                d = sum(a * b for a, b in zip(x, y))
                n1 = sum(a * a for a in x) ** 0.5
                n2 = sum(b * b for b in y) ** 0.5
                return d / (n1 * n2) if n1 * n2 > 0 else 0

            sim_ab = cosine_sim(emb_a, emb_b)
            sim_ac = cosine_sim(emb_a, emb_c)

            result(
                f"similar queries are close (sim={sim_ab:.3f})",
                sim_ab > 0.7,
                f"sim={sim_ab}",
            )
            result(
                f"unrelated query is distant (sim={sim_ac:.3f})",
                sim_ac < sim_ab,
                f"sim_related={sim_ab}, sim_unrelated={sim_ac}",
            )
        except Exception as e:
            result("embedding similarity", False, str(e))


async def main():
    print("=" * 60)
    print("RAG SALES CHATBOT — AGGRESSIVE TEST SUITE")
    print("=" * 60)

    t0 = time.time()

    await test_health_checks()
    await test_ollama_local()
    await test_gateway_router()
    await test_embedding_service()
    await test_pricing_api()
    await test_postgres_schema()
    await test_embedding_consistency()
    await test_llm_service()
    await test_chat_api()

    elapsed = time.time() - t0

    print("\n" + "=" * 60)
    print(f"RESULTS: {PASS} passed, {FAIL} failed ({elapsed:.1f}s)")
    print("=" * 60)

    if ERRORS:
        print("\nFAILURES:")
        for e in ERRORS:
            print(f"  - {e}")

    sys.exit(1 if FAIL > 0 else 0)


if __name__ == "__main__":
    asyncio.run(main())
