# embedding_service

**Port**: 8002 | **Owner**: Backend team | **Caller**: n8n workflow + ingestion scripts (internal)

## Purpose
Generates vector embeddings from text using Ollama embeddings API. Used by n8n for query embeddings and by `scripts/ingest.py` for document ingestion.

## Position in Architecture
```
n8n / scripts/ingest.py
  ↓  POST /embed or /embed-batch
[ embedding_service :8002 ]   ← YOU ARE HERE
  ↓  POST /api/embeddings
[ Ollama :11434 (host machine) ]
  ↓  768-dim float array
 back to caller
```

## Responsibilities
- Convert a single text string into embedding vector.
- Convert a batch of strings into embedding vectors.
- Expose model and embedding dimensions for observability.

## Endpoints
- `POST /embed`
- `POST /embed-batch`
- `GET /health`

### POST /embed
Request:
```json
{
  "text": "Need a plan for a 50-person software team"
}
```

Response:
```json
{
  "embedding": [0.0123, -0.004, 0.9912],
  "model": "nomic-embed-text",
  "dimensions": 768
}
```

### POST /embed-batch
Request:
```json
{
  "texts": ["text one", "text two"]
}
```

Response:
```json
{
  "embeddings": [[0.1, 0.2], [0.3, 0.4]],
  "model": "nomic-embed-text",
  "dimensions": 768,
  "count": 2
}
```

## Environment Variables
- `OLLAMA_HOST` (default: `http://ollama:11434`)
- `EMBEDDING_MODEL` (default: `nomic-embed-text`)

## Error Handling
- Ollama unavailable -> `503`
- Ollama non-2xx -> `502`

## Dependencies
- FastAPI
- httpx
- pydantic

## Local Run
```bash
uvicorn main:app --host 0.0.0.0 --port 8002 --reload
```

## Testing

```bash
# Single embedding
curl -X POST http://localhost:8002/embed \
  -H "Content-Type: application/json" \
  -d '{"text": "what plans do you offer?"}'
# Expected: {"embedding": [...768 floats], "model": "nomic-embed-text", "dimensions": 768}

# Health
curl http://localhost:8002/health
# Expected: {"status": "healthy", "service": "embedding_service", "model": "nomic-embed-text"}
```

Included in `scripts/test_all.py` — tests single embed, batch embed, dimensions, consistency.

## Key Design Decisions

- **nomic-embed-text**: 768 dimensions, 8k context, Apache 2.0 license. Runs via Ollama — same process that runs the LLM.
- **Stateless**: safe to scale horizontally. Bottleneck is Ollama throughput.
- **Batch endpoint**: `scripts/ingest.py` uses `/embed-batch` to process all chunks serially (Ollama doesn't support true parallel embedding requests).

## Roadmap

See [ROADMAP.md](../../../../ROADMAP.md):
- Phase 2.3: `/rerank` endpoint using cross-encoder for context re-ranking
