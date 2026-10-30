from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(
    title="gois.v1 API",
    description="API própria para gerenciar e executar o modelo gois.v1 sem limites de terceiros.",
    version="1.0.0"
)

# Permitir conexões externas (CORS) para o teu frontend comunicar sem bloqueios
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Estruturas de Dados
class PromptRequest(BaseModel):
    prompt: str
    max_tokens: Optional[int] = 150
    temperature: Optional[float] = 0.7

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: Optional[str] = "gois.v1"
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 500

# Rota Raiz (Evita erros 404 nos pings do Render)
@app.get("/")
def home():
    return {
        "status": "online",
        "model": "gois.v1",
        "message": "API própria rodando com sucesso no Render!"
    }

@app.head("/")
def home_head():
    return {"status": "online"}

# Rota de Geração Simples
@app.post("/v1/generate")
def generate_text(request: PromptRequest):
    try:
        prompt_recebido = request.prompt
        resposta_modelo = f"[gois.v1 processado]: Você disse '{prompt_recebido}'. Resposta gerada com sucesso sem rate limits!"
        return {
            "success": True,
            "prompt": prompt_recebido,
            "response": resposta_modelo
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Rota de Chat Compatível (Resolve os erros em /v1/chat/completions)
@app.post("/v1/chat/completions")
def chat_completions(request: ChatCompletionRequest):
    try:
        # Extrair a última mensagem do utilizador
        ultima_msg = request.messages[-1].content if request.messages else "Olá"
        
        # --- AQUI ENTRA A LÓGICA DO TEU GOIS.V1 ---
        resposta_texto = f"gois.v1 processado com sucesso: Recebi a tua mensagem '{ultima_msg}' a partir do endpoint de chat."

        # Formato de resposta compatível com clientes de chat
        return {
            "id": "chat-gois-v1",
            "object": "chat.completion",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": resposta_texto
                    },
                    "finish_reason": "stop"
                }
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
