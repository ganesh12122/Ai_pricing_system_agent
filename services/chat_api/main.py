import os
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional

app = FastAPI(title="RAG Chat API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "http://n8n:5678/webhook/chat")


class ChatRequest(BaseModel):
    userID: Optional[str] = Field(None, description="Optional user ID for conversation continuity")
    prompt: str = Field(..., min_length=1, max_length=5000, description="User message")


class ChatResponse(BaseModel):
    response: str


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    payload = {"prompt": request.prompt}
    if request.userID:
        payload["userID"] = request.userID

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(N8N_WEBHOOK_URL, json=payload)
            resp.raise_for_status()
            data = resp.json()
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Request timed out. Please try again.")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Upstream error: {e.response.status_code}")
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Service temporarily unavailable. Please try again.")

    return ChatResponse(response=data.get("response", ""))


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "chat_api"}
