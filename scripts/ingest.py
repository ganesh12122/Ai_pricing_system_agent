"""
RAG Sales Chatbot — Document Ingestion Script

Reads module documentation from db/seed/modules/, chunks them,
embeds via embedding_service, and inserts into pgvector.

Usage:
    python scripts/ingest.py

Requires:
    - embedding_service running at EMBEDDING_SERVICE_HOST
    - PostgreSQL running at DATABASE_URL
    - pip install httpx asyncpg
"""

import os
import sys
import glob
import asyncio
import httpx
import asyncpg
import json

EMBEDDING_SERVICE_HOST = os.getenv("EMBEDDING_SERVICE_HOST", "http://localhost:8002")
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://rag_user:change_me_in_production@localhost:5432/rag_chatbot",
)
MODULES_DIR = os.path.join(os.path.dirname(__file__), "..", "db", "seed", "modules")

CHUNK_SIZE = 500  # characters
CHUNK_OVERLAP = 100  # characters


def read_module_docs(modules_dir: str) -> list[dict]:
    """Read all .md files from the modules directory."""
    docs = []
    pattern = os.path.join(modules_dir, "*.md")
    for filepath in sorted(glob.glob(pattern)):
        filename = os.path.basename(filepath)
        module_name = filename.replace(".md", "").replace("_", " ").title()
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        docs.append({
            "content": content,
            "metadata": {
                "source_file": filename,
                "module_name": module_name,
            },
        })
        print(f"  Read: {filename} ({len(content)} chars)")
    return docs


def chunk_documents(docs: list[dict]) -> list[dict]:
    """Split documents into overlapping chunks."""
    chunks = []
    for doc in docs:
        content = doc["content"]
        metadata = doc["metadata"]

        if len(content) <= CHUNK_SIZE:
            chunks.append({"content": content, "metadata": metadata})
        else:
            start = 0
            chunk_index = 0
            while start < len(content):
                end = min(start + CHUNK_SIZE, len(content))

                # Try to break at sentence boundary
                chunk_text = content[start:end]
                if end < len(content):
                    last_period = chunk_text.rfind(".")
                    last_newline = chunk_text.rfind("\n")
                    break_point = max(last_period, last_newline)
                    if break_point > CHUNK_SIZE * 0.3:
                        chunk_text = chunk_text[: break_point + 1]
                        end = start + break_point + 1

                chunks.append({
                    "content": chunk_text.strip(),
                    "metadata": {**metadata, "chunk_index": chunk_index},
                })

                start = end - CHUNK_OVERLAP if end < len(content) else len(content)
                chunk_index += 1

    return [c for c in chunks if c["content"]]  # filter empty


async def embed_chunks(chunks: list[dict]) -> list[list[float]]:
    """Embed all chunks via embedding_service."""
    texts = [c["content"] for c in chunks]

    async with httpx.AsyncClient(timeout=300.0) as client:
        # Batch in groups of 20 to avoid overwhelming the service
        all_embeddings = []
        batch_size = 20
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            print(f"  Embedding batch {i // batch_size + 1} ({len(batch)} chunks)...")
            resp = await client.post(
                f"{EMBEDDING_SERVICE_HOST}/embed-batch",
                json={"texts": batch},
            )
            resp.raise_for_status()
            data = resp.json()
            all_embeddings.extend(data["embeddings"])

    return all_embeddings


async def store_chunks(chunks: list[dict], embeddings: list[list[float]]):
    """Store chunks and embeddings in pgvector."""
    conn = await asyncpg.connect(DATABASE_URL)

    try:
        # Clear existing chunks (full re-ingestion)
        await conn.execute("DELETE FROM document_chunks")
        print("  Cleared existing document_chunks")

        # Insert new chunks
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
            await conn.execute(
                """
                INSERT INTO document_chunks (content, metadata, embedding)
                VALUES ($1, $2::jsonb, $3::vector)
                """,
                chunk["content"],
                json.dumps(chunk["metadata"]),
                embedding_str,
            )

        print(f"  Inserted {len(chunks)} chunks into document_chunks")
    finally:
        await conn.close()


async def main():
    print("=" * 60)
    print("RAG Sales Chatbot — Document Ingestion")
    print("=" * 60)

    # Step 1: Read module docs
    print("\n[1/4] Reading module documentation...")
    docs = read_module_docs(MODULES_DIR)
    if not docs:
        print("ERROR: No .md files found in", MODULES_DIR)
        sys.exit(1)
    print(f"  Found {len(docs)} documents")

    # Step 2: Chunk documents
    print("\n[2/4] Chunking documents...")
    chunks = chunk_documents(docs)
    print(f"  Created {len(chunks)} chunks")

    # Step 3: Embed chunks
    print("\n[3/4] Embedding chunks via embedding_service...")
    embeddings = await embed_chunks(chunks)
    print(f"  Generated {len(embeddings)} embeddings (dim={len(embeddings[0])})")

    # Step 4: Store in pgvector
    print("\n[4/4] Storing in PostgreSQL (pgvector)...")
    await store_chunks(chunks, embeddings)

    print("\n" + "=" * 60)
    print(f"Ingestion complete: {len(chunks)} chunks indexed")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
