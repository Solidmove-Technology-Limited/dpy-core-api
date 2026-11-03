"""SolidMove chat endpoint: the path a client query actually takes.

Flow: authenticate, screen the prompt, call the configured model provider,
screen the completion, return it. If no provider is configured the endpoint
answers 503 rather than pretending to be an assistant, so the deployment
never reports a capability it does not have.
"""

import json
import os
import urllib.error
import urllib.request

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from app.moderation import screen_input, screen_output
from app.security import SecurityConfigError, decode_token_payload

router = APIRouter()

PROVIDER_URL = os.getenv("DPY_MODEL_URL", "https://api.openai.com/v1/chat/completions")
MODEL_NAME = os.getenv("DPY_MODEL", "gpt-4o-mini")
SYSTEM_PROMPT = (
    "You are SolidMove, a helpful assistant from SolidMove Technology Limited. "
    "Answer clearly and briefly. Never invent company policies, prices or legal "
    "commitments. If you are unsure, say so."
)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4_000)
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    reply: str
    conversation_id: str | None
    moderation: dict


def _require_subject(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="missing bearer token")
    try:
        claims = decode_token_payload(authorization.split(" ", 1)[1].strip())
    except SecurityConfigError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=401, detail="invalid or expired token")
    subject = claims.get("sub")
    if not subject:
        raise HTTPException(status_code=401, detail="token missing subject")
    return subject


def _call_model(prompt: str) -> str:
    api_key = os.getenv("DPY_MODEL_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="model provider not configured: set DPY_MODEL_API_KEY",
        )
    body = json.dumps({
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 800,
        "temperature": 0.4,
    }).encode()
    request = urllib.request.Request(
        PROVIDER_URL,
        data=body,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"provider error {exc.code}")
    except Exception:
        raise HTTPException(status_code=504, detail="provider timeout")
    try:
        return payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        raise HTTPException(status_code=502, detail="unexpected provider response")


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, authorization: str | None = Header(default=None)):
    subject = _require_subject(authorization)

    inbound = screen_input(payload.message)
    if not inbound.allowed:
        raise HTTPException(
            status_code=451,
            detail={"reason": "input rejected by content policy", "categories": inbound.categories},
        )

    completion = _call_model(inbound.text)

    outbound = screen_output(completion)
    if not outbound.allowed:
        raise HTTPException(
            status_code=451,
            detail={"reason": "response withheld by content policy", "categories": outbound.categories},
        )

    return ChatResponse(
        reply=outbound.text,
        conversation_id=payload.conversation_id,
        moderation={**inbound.as_dict(), "subject": subject, "output_redactions": outbound.redactions},
    )
