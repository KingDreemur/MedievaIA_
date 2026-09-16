from openai import OpenAI

from medievaia import db
from medievaia.config import CHAT_MODEL, OPENAI_API_KEY
from medievaia.embeddings import embed_query

SYSTEM_PROMPT = """Voce e um assistente de regras de Dungeons & Dragons 5e.

Responda SOMENTE com base nos trechos fornecidos em CONTEXTO.
Se o contexto nao responder a pergunta, diga que nao encontrou a regra.
Nunca invente regras nem use conhecimento externo ao contexto.

Os trechos marcados como [SRD] sao regras oficiais.
Os trechos marcados como [HOMEBREW] sao regras da casa criadas pela mesa.
Quando uma regra da casa contradiz o SRD, aponte explicitamente a divergencia.

Cite a origem de cada afirmacao no formato (fonte, titulo, pagina).
Responda em portugues do Brasil."""

BASELINE_PROMPT = """Voce e um assistente de regras de Dungeons & Dragons 5e.
Responda a pergunta usando apenas o seu conhecimento geral, sem consultar
nenhum documento. Responda em portugues do Brasil."""

_client = None


def client():
    global _client
    if _client is None:
        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY ausente: configure o backend/.env")
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


def retrieve(question, limit=5, source_type=None):
    return db.search(embed_query(question), limit=limit, source_type=source_type)


def format_context(passages):
    blocks = []
    for passage in passages:
        marker = "HOMEBREW" if passage["source_type"] == "homebrew" else "SRD"
        location = f"pagina {passage['page']}" if passage["page"] else "sem pagina"
        blocks.append(
            f"[{marker}] fonte: {passage['source_name']} | {location}\n"
            f"capitulo: {passage['chapter']} > {passage['section']}\n"
            f"titulo: {passage['title']}\n\n{passage['content']}"
        )
    return "\n\n---\n\n".join(blocks)


def answer(question, limit=5, source_type=None):
    passages = retrieve(question, limit=limit, source_type=source_type)
    if not passages:
        return "Nenhum trecho encontrado na base.", passages

    response = client().chat.completions.create(
        model=CHAT_MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"CONTEXTO:\n{format_context(passages)}\n\nPERGUNTA: {question}",
            },
        ],
    )
    return response.choices[0].message.content, passages


def answer_without_retrieval(question):
    response = client().chat.completions.create(
        model=CHAT_MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": BASELINE_PROMPT},
            {"role": "user", "content": question},
        ],
    )
    return response.choices[0].message.content
