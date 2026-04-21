"""
RAG Sales Chatbot — Seed Database Script

Runs the seed SQL to populate modules and pricing_rules tables.

Usage:
    python scripts/seed_db.py
"""

import os
import asyncio
import asyncpg

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://rag_user:change_me_in_production@localhost:5432/rag_chatbot",
)
SEED_FILE = os.path.join(os.path.dirname(__file__), "..", "db", "seed", "002_seed_data.sql")


async def main():
    print("Seeding database...")

    with open(SEED_FILE, "r", encoding="utf-8") as f:
        sql = f.read()

    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute(sql)
        print("Seed data inserted successfully.")

        # Verify
        module_count = await conn.fetchval("SELECT COUNT(*) FROM modules")
        pricing_count = await conn.fetchval("SELECT COUNT(*) FROM pricing_rules")
        print(f"  Modules: {module_count}")
        print(f"  Pricing rules: {pricing_count}")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
