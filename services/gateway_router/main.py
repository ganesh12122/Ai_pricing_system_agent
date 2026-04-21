import re
from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Optional

app = FastAPI(title="Gateway Router", version="1.0.0")

# Keywords that indicate a product/pricing query
PRICING_KEYWORDS = [
    r"\bpric(?:e|es|ing)\b",
    r"\bcost(?:s)?\b",
    r"\bhow\s+much\b",
    r"\bsubscri(?:be|ption|ptions)\b",
    r"\bmodule(?:s)?\b",
    r"\bplan(?:s)?\b",
    r"\bbuy\b",
    r"\bpurchas(?:e|ing)\b",
    r"\btier(?:s)?\b",
    r"\bpackage(?:s)?\b",
    r"\bquote\b",
    r"\bbudget\b",
    r"\bpay(?:ment)?\b",
    r"\bfee(?:s)?\b",
    r"\bdiscount\b",
    r"\boffer(?:s)?\b",
    r"\buser(?:s)?\s*(?:count|number|seat)?\b.*\b(?:price|cost|plan)\b",
]

PRICING_PATTERN = re.compile("|".join(PRICING_KEYWORDS), re.IGNORECASE)


class ClassifyRequest(BaseModel):
    message: str = Field(..., min_length=1)
    chat_history: Optional[list] = None


class ClassifyResponse(BaseModel):
    intent: str
    confidence: float
    matched_keywords: list[str]


@app.post("/classify", response_model=ClassifyResponse)
async def classify(request: ClassifyRequest):
    message = request.message.lower()
    matches = PRICING_PATTERN.findall(message)

    if matches:
        # Deduplicate and clean matched keywords
        unique_matches = list(set(m.strip() for m in matches if m.strip()))
        confidence = min(0.95, 0.6 + 0.1 * len(unique_matches))
        return ClassifyResponse(
            intent="product_pricing",
            confidence=confidence,
            matched_keywords=unique_matches,
        )

    return ClassifyResponse(
        intent="general_doc",
        confidence=0.8,
        matched_keywords=[],
    )


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "gateway_router"}
