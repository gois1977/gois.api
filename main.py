import os
import re
import time
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger("uvicorn.error")

BASE_DIR = Path(__file__).resolve().parent

# =====================================================================
# CONFIGURAÇÃO DE FORNECEDORES DE IA (FAILOVER)
# =====================================================================

GROQ_MODEL = os.environ.get("GROQ_MODEL", "").strip() or "openai/gpt-oss-120b"

PROVIDERS = [
    {
        "name": "OpenRouter",
        "env": "OPENROUTER_API_KEY",
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "model": "deepseek/deepseek-chat",
        "extra_headers": {
            "HTTP-Referer": "https://gois-api.onrender.com",
            "X-Title": "gois.api Personal Engine",
        },
    },
    {
        "name": "Groq",
        "env": "GROQ_API_KEY",
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "model": GROQ_MODEL,
        "extra_headers": {},
    },
    {
        "name": "Mistral",
        "env": "MISTRAL_API_KEY",
        "url": "https://api.mistral.ai/v1/chat/completions",
        "model": "mistral-small-latest",
        "extra_headers": {},
    },
]

RUNTIME_KEYS: dict = {}

def candidate_keys(provider: dict) -> list:
    keys = []
    for k in (RUNTIME_KEYS.get(provider["env"], ""), os.environ.get(provider["env"], "")):
        k = (k or "").strip()
        if k and k not in keys:
            keys.append(k)
    return keys

def flatten_content(content) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, dict):
                parts.append(str(part.get("text", "")))
            else:
                parts.append(str(part))
        return "\n".join(p for p in parts if p)
    return str(content)

def build_provider_request(p: dict, key: str, payload: dict, stream: bool = False, override_model: str = ""):
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        **p["extra_headers"],
    }
    body = {
        "model": override_model or p["model"],
        "messages": payload.get("messages", []),
        "temperature": payload.get("temperature", 0.6),
        "stream": stream,
    }
    if payload.get("max_tokens"):
        body["max_tokens"] = payload["max_tokens"]
        if p["name"] == "Groq" and str(body["model"]).startswith("openai/gpt-oss"):
            body["max_tokens"] = int(payload["max_tokens"]) + 2048
    return headers, body

async def make_llm_request(payload: dict, preferred_provider: str = "", override_model: str = ""):
    errors = []
    timeout = httpx.Timeout(65.0, connect=15.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        for p in PROVIDERS:
            keys = candidate_keys(p)
            if not keys:
                errors.append(f"{p['name']}: sem chave ({p['env']})")
                continue
            for key in keys:
                try:
                    headers, body = build_provider_request(p, key, payload, stream=False, override_model=override_model or p["model"])
                    resp = await client.post(p["url"], json=body, headers=headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        if isinstance(data, dict) and data.get("choices"):
                            data["model"] = f"{p['name']} · {p['model']}"
                            return data, []
                        errors.append(f"{p['name']}: resposta sem choices")
                    else:
                        errors.append(f"{p['name']}: HTTP {resp.status_code}")
                except Exception as e:
                    errors.append(f"{p['name']}: {type(e).__name__}")
    return None, errors

async def stream_llm_request(payload: dict):
    errors = []
    timeout = httpx.Timeout(120.0, connect=15.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        for p in PROVIDERS:
            keys = candidate_keys(p)
            if not keys:
                continue
            for key in keys:
                got_content = False
                try:
                    headers, body = build_provider_request(p, key, payload, stream=True)
                    async with client.stream("POST", p["url"], json=body, headers=headers) as resp:
                        if resp.status_code != 200:
                            continue
                        sent_model = False
                        async for line in resp.aiter_lines():
                            line = line.strip()
                            if not line or not line.startswith("data:"):
                                continue
                            data_str = line[5:].strip()
                            if not data_str:
                                continue
                            if data_str == "[DONE]":
                                if got_content:
                                    yield "data: [DONE]\n\n"
                                    return
                                break
                            try:
                                chunk = json.loads(data_str)
                            except Exception:
                                continue
                            if not isinstance(chunk, dict):
                                continue
                            if not sent_model:
                                chunk["model"] = f"{p['name']} · {p['model']}"
                                sent_model = True
                            choices = chunk.get("choices") or []
                            if choices and isinstance(choices[0], dict):
                                delta = choices[0].get("delta") or {}
                                if delta.get("content"):
                                    got_content = True
                            yield "data: " + json.dumps(chunk, ensure_ascii=False) + "\n\n"
                        if got_content:
                            yield "data: [DONE]\n\n"
                            return
                except Exception:
                    pass

    yield "data: " + json.dumps({"error": {"message": "Erro de Failover na gois.api."}}, ensure_ascii=False) + "\n\n"
    yield "data: [DONE]\n\n"

@asynccontextmanager
async def lifespan(_: FastAPI):
    yield

app = FastAPI(title="gois.api Personal Engine", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/v1/chat/completions")
@app.post("/chat/completions")
async def process_chat(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Corpo inválido.")
    
    messages = body.get("messages", []) or []
    formatted = []
    for m in messages:
        if isinstance(m, dict):
            role = m.get("role", "user")
            content = flatten_content(m.get("content"))
            if role and content:
                formatted.append({"role": role, "content": content})

    payload = {"messages": formatted}
    if isinstance(body.get("temperature"), (int, float)):
        payload["temperature"] = body["temperature"]
    if isinstance(body.get("max_tokens"), int):
        payload["max_tokens"] = body["max_tokens"]

    if body.get("stream"):
        return StreamingResponse(
            stream_llm_request(payload),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    data, errors = await make_llm_request(payload)
    if data is not None:
        return JSONResponse(content=data)

    raise HTTPException(status_code=502, detail="Erro: " + " | ".join(errors))

@app.get("/health")
async def health():
    return {"status": "online", "service": "gois.api"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "10000")))
