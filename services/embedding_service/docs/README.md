# embedding_service

## Purpose
Generates vector embeddings from text using Ollama embeddings API. Used by n8n for query embeddings and ingestion embeddings.

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
