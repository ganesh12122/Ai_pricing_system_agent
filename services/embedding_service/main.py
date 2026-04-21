import os
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Embedding Service", version="1.0.0")

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")


class EmbedRequest(BaseModel):
    text: str = Field(..., min_length=1)


class EmbedResponse(BaseModel):
    embedding: list[float]
    model: str
    dimensions: int


class EmbedBatchRequest(BaseModel):
    texts: list[str] = Field(..., min_length=1)


class EmbedBatchResponse(BaseModel):
    embeddings: list[list[float]]
    model: str
    dimensions: int
    count: int


async def _get_embedding(client: httpx.AsyncClient, text: str) -> list[float]:
    resp = await client.post(
        f"{OLLAMA_HOST}/api/embeddings",
        json={"model": EMBEDDING_MODEL, "prompt": text},
    )
    resp.raise_for_status()
    return resp.json()["embedding"]


@app.post("/embed", response_model=EmbedResponse)
async def embed(request: EmbedRequest):
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            embedding = await _get_embedding(client, request.text)
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Ollama embedding service unavailable")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Ollama error: {e.response.status_code}")

    return EmbedResponse(
        embedding=embedding,
        model=EMBEDDING_MODEL,
        dimensions=len(embedding),
    )


@app.post("/embed-batch", response_model=EmbedBatchResponse)
async def embed_batch(request: EmbedBatchRequest):
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            embeddings = []
            for text in request.texts:
                emb = await _get_embedding(client, text)
                embeddings.append(emb)
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Ollama embedding service unavailable")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Ollama error: {e.response.status_code}")

    dimensions = len(embeddings[0]) if embeddings else 0
    return EmbedBatchResponse(
        embeddings=embeddings,
        model=EMBEDDING_MODEL,
        dimensions=dimensions,
        count=len(embeddings),
    )


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "embedding_service", "model": EMBEDDING_MODEL}
