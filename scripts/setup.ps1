# =============================================================================
# RAG Sales Chatbot - Setup Script (Windows PowerShell)
# Run this once after `docker compose up -d` to initialize the system
# =============================================================================

Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "RAG Sales Chatbot - Initial Setup" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan

# Step 1: Wait for services
Write-Host "`n[1/5] Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Step 2: Pull Ollama models
Write-Host "`n[2/5] Pulling Ollama models (this may take several minutes)..." -ForegroundColor Yellow
docker exec rag_ollama ollama pull nomic-embed-text
Write-Host "  nomic-embed-text pulled" -ForegroundColor Green
docker exec rag_ollama ollama pull qwen2.5:7b
Write-Host "  qwen2.5:7b pulled" -ForegroundColor Green

# Step 3: Seed the database
Write-Host "`n[3/5] Seeding database with modules and pricing rules..." -ForegroundColor Yellow
pip install -q httpx asyncpg
python scripts/seed_db.py
Write-Host "  Database seeded" -ForegroundColor Green

# Step 4: Run ingestion
Write-Host "`n[4/5] Ingesting module documentation into pgvector..." -ForegroundColor Yellow
python scripts/ingest.py
Write-Host "  Documents ingested" -ForegroundColor Green

# Step 5: Verify
Write-Host "`n[5/5] Verifying setup..." -ForegroundColor Yellow
try { $r = Invoke-RestMethod http://localhost:8000/health; Write-Host "  chat_api: $($r.status)" -ForegroundColor Green } catch { Write-Host "  chat_api: not ready" -ForegroundColor Red }

Write-Host "`n==============================================" -ForegroundColor Cyan
Write-Host "Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host 'Test with:'
Write-Host '  curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d "{\"prompt\": \"What plans do you offer?\"}"'
Write-Host ""
Write-Host "n8n Dashboard: http://localhost:5678"
Write-Host "  Import workflows from n8n/workflows/"
Write-Host "==============================================" -ForegroundColor Cyan
