from openai import OpenAI

from medievaia.config import EMBEDDING_MODEL, OPENAI_API_KEY

BATCH_SIZE = 100

_client = None


def client():
    global _client
    if _client is None:
        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY ausente: configure o backend/.env")
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


def embed_texts(texts, progress=None):
    vectors = []
    for start in range(0, len(texts), BATCH_SIZE):
        batch = texts[start:start + BATCH_SIZE]
        response = client().embeddings.create(model=EMBEDDING_MODEL, input=batch)
        vectors.extend(item.embedding for item in response.data)
        if progress:
            progress(len(vectors), len(texts))
    return vectors


def embed_query(text):
    return embed_texts([text])[0]
