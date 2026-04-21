import os
import json
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

app = FastAPI(title="LLM Service", version="1.0.0")

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
INFERENCE_BACKEND = os.getenv("INFERENCE_BACKEND", "ollama")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "")


class ChatMessage(BaseModel):
    role: str
    content: str


class ContextChunk(BaseModel):
    content: str
    metadata: Optional[dict] = None
    similarity: Optional[float] = None


class GenerateRequest(BaseModel):
    user_prompt: str = Field(..., min_length=1)
    system_prompt: str = Field(..., min_length=1)
    chat_history: Optional[list[ChatMessage]] = None
    retrieved_context: Optional[list[ContextChunk]] = None
    pricing_data: Optional[dict] = None


class TokenUsage(BaseModel):
    prompt: int = 0
    completion: int = 0
    total: int = 0


class GenerateResponse(BaseModel):
    response: str
    model: str
    tokens_used: TokenUsage


def _build_messages(request: GenerateRequest) -> list[dict]:
    """Assemble the full message list for the LLM."""
    messages = []

    # System prompt with injected context
    system_content = request.system_prompt

    # Inject retrieved context
    if request.retrieved_context:
        context_parts = []
        for chunk in request.retrieved_context:
            source = chunk.metadata.get("source_file", "unknown") if chunk.metadata else "unknown"
            context_parts.append(f"---\n{chunk.content}\nSource: {source}\n---")
        system_content += "\n\n## Relevant Documentation\n" + "\n".join(context_parts)

    # Inject pricing data
    if request.pricing_data:
        pricing_str = json.dumps(request.pricing_data, indent=2)
        system_content += (
            f"\n\n## Exact Pricing Data\n"
            f"```json\n{pricing_str}\n```\n"
            f"IMPORTANT: Use these exact numbers. Do not recalculate."
        )

    messages.append({"role": "system", "content": system_content})

    # Chat history
    if request.chat_history:
        for msg in request.chat_history:
            messages.append({"role": msg.role, "content": msg.content})

    # Current user message
    messages.append({"role": "user", "content": request.user_prompt})

    return messages


async def _generate_ollama(messages: list[dict]) -> tuple[str, TokenUsage]:
    """Generate response via Ollama API."""
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{OLLAMA_HOST}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "messages": messages,
                "stream": False,
            },
        )
        resp.raise_for_status()
        data = resp.json()

    response_text = data.get("message", {}).get("content", "")
    tokens = TokenUsage(
        prompt=data.get("prompt_eval_count", 0),
        completion=data.get("eval_count", 0),
        total=data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
    )
    return response_text, tokens


async def _generate_openai(messages: list[dict]) -> tuple[str, TokenUsage]:
    """Generate response via OpenAI-compatible API (OpenAI, vLLM, Groq, etc.)."""
    from openai import AsyncOpenAI

    client = AsyncOpenAI(
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_BASE_URL if OPENAI_BASE_URL else None,
    )

    resp = await client.chat.completions.create(
        model=OLLAMA_MODEL,
        messages=messages,
    )

    response_text = resp.choices[0].message.content or ""
    tokens = TokenUsage(
        prompt=resp.usage.prompt_tokens if resp.usage else 0,
        completion=resp.usage.completion_tokens if resp.usage else 0,
        total=resp.usage.total_tokens if resp.usage else 0,
    )
    return response_text, tokens


@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    messages = _build_messages(request)

    try:
        if INFERENCE_BACKEND == "ollama":
            response_text, tokens = await _generate_ollama(messages)
        elif INFERENCE_BACKEND in ("openai", "vllm"):
            response_text, tokens = await _generate_openai(messages)
        else:
            raise HTTPException(status_code=500, detail=f"Unknown backend: {INFERENCE_BACKEND}")
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="LLM service unavailable")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"LLM error: {e.response.status_code}")

    return GenerateResponse(
        response=response_text,
        model=OLLAMA_MODEL,
        tokens_used=tokens,
    )


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "llm_service",
        "backend": INFERENCE_BACKEND,
        "model": OLLAMA_MODEL,
    }
