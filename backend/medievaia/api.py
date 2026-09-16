import os
import time
from collections import defaultdict, deque
from pathlib import Path

import psycopg2
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from medievaia import db, rag

PAGE = Path(__file__).resolve().parent / "web" / "index.html"

RATE_LIMIT = int(os.getenv("RATE_LIMIT_PER_HOUR", "30"))
RATE_WINDOW = 3600

app = FastAPI(title="MedievaIA", description="Assistente de regras de D&D com RAG")

# ponytail: contagem em memoria, suficiente para uma instancia unica no plano
# gratuito; com varias replicas isso precisa virar Redis ou tabela no banco.
_acessos = defaultdict(deque)


def checar_limite(request: Request):
    if RATE_LIMIT <= 0:
        return
    identificador = request.client.host if request.client else "desconhecido"
    agora = time.monotonic()
    historico = _acessos[identificador]
    while historico and agora - historico[0] > RATE_WINDOW:
        historico.popleft()
    if len(historico) >= RATE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail=f"Limite de {RATE_LIMIT} perguntas por hora atingido. Tente mais tarde.",
        )
    historico.append(agora)


class Pergunta(BaseModel):
    question: str = Field(min_length=3, max_length=500)
    source: str | None = Field(default=None, pattern="^(srd|homebrew)$")
    limit: int = Field(default=5, ge=1, le=20)


class Trecho(BaseModel):
    source_type: str
    source_name: str
    page: int | None
    chapter: str
    section: str
    title: str
    type: str
    content: str
    distance: float


class Resposta(BaseModel):
    answer: str
    passages: list[Trecho]


class Baseline(BaseModel):
    answer: str


@app.get("/", include_in_schema=False)
def pagina():
    return FileResponse(PAGE)


@app.get("/api/status")
def status():
    try:
        db.apply_schema()
        return {
            "sources": [
                {"source_type": tipo, "source_name": nome, "chunks": total}
                for tipo, nome, total in db.counts()
            ],
            "composition": [
                {"type": tipo, "chunks": total} for tipo, total in db.composition()
            ],
        }
    except psycopg2.Error as erro:
        raise HTTPException(status_code=503, detail=f"Banco indisponivel: {erro}")


@app.get("/health", include_in_schema=False)
def saude():
    return {"status": "ok"}


@app.post("/api/ask", response_model=Resposta)
def perguntar(pergunta: Pergunta, request: Request):
    checar_limite(request)
    try:
        texto, trechos = rag.answer(
            pergunta.question, limit=pergunta.limit, source_type=pergunta.source
        )
    except psycopg2.Error as erro:
        raise HTTPException(status_code=503, detail=f"Banco indisponivel: {erro}")
    except RuntimeError as erro:
        raise HTTPException(status_code=503, detail=str(erro))

    return Resposta(answer=texto, passages=[Trecho(**trecho) for trecho in trechos])


@app.post("/api/baseline", response_model=Baseline)
def perguntar_sem_rag(pergunta: Pergunta, request: Request):
    checar_limite(request)
    try:
        return Baseline(answer=rag.answer_without_retrieval(pergunta.question))
    except RuntimeError as erro:
        raise HTTPException(status_code=503, detail=str(erro))
