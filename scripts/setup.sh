#!/bin/bash
# =============================================================================
# RAG Sales Chatbot — Setup Script
# Run this once after `docker compose up -d` to initialize the system
# =============================================================================

set -e

echo "=============================================="
echo "RAG Sales Chatbot — Initial Setup"
echo "=============================================="

# Step 1: Wait for services to be healthy
echo ""
echo "[1/5] Waiting for services to start..."
sleep 10

# Step 2: Pull Ollama models
echo ""
echo "[2/5] Pulling Ollama models (this may take several minutes)..."
docker exec rag_ollama ollama pull nomic-embed-text
echo "  ✓ nomic-embed-text pulled"
docker exec rag_ollama ollama pull qwen2.5:7b
echo "  ✓ qwen2.5:7b pulled"

# Step 3: Seed the database
echo ""
echo "[3/5] Seeding database with modules and pricing rules..."
pip install -q httpx asyncpg
python scripts/seed_db.py
echo "  ✓ Database seeded"

# Step 4: Run ingestion (embed module docs into pgvector)
echo ""
echo "[4/5] Ingesting module documentation into pgvector..."
python scripts/ingest.py
echo "  ✓ Documents ingested"

# Step 5: Verify
echo ""
echo "[5/5] Verifying setup..."
echo ""

# Test chat_api health
echo -n "  chat_api: "
curl -sf http://localhost:8000/health | python -c "import sys,json; print(json.load(sys.stdin)['status'])" 2>/dev/null || echo "not ready"

# Test gateway_router health (internal, through docker)
echo -n "  gateway_router: "
docker exec rag_gateway_router curl -sf http://localhost:8001/health | python -c "import sys,json; print(json.load(sys.stdin)['status'])" 2>/dev/null || echo "not ready"

# Test embedding_service health
echo -n "  embedding_service: "
docker exec rag_embedding_service curl -sf http://localhost:8002/health | python -c "import sys,json; print(json.load(sys.stdin)['status'])" 2>/dev/null || echo "not ready"

# Test llm_service health
echo -n "  llm_service: "
docker exec rag_llm_service curl -sf http://localhost:8003/health | python -c "import sys,json; print(json.load(sys.stdin)['status'])" 2>/dev/null || echo "not ready"

# Test pricing_api health
echo -n "  pricing_api: "
docker exec rag_pricing_api curl -sf http://localhost:8004/health | python -c "import sys,json; print(json.load(sys.stdin)['status'])" 2>/dev/null || echo "not ready"

echo ""
echo "=============================================="
echo "Setup complete!"
echo ""
echo "Test with:"
echo '  curl -X POST http://localhost:8000/chat \'
echo '    -H "Content-Type: application/json" \'
echo '    -d '"'"'{"prompt": "What plans do you offer?"}'"'"''
echo ""
echo "n8n Dashboard: http://localhost:5678"
echo "  Import workflows from n8n/workflows/"
echo "=============================================="
