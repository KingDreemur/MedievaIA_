# MedievaIA

Assistente de regras de Dungeons & Dragons baseado em RAG (*Retrieval-Augmented
Generation*) sobre o System Reference Document 5.2.1, com suporte a regras da
casa (*homebrews*) mantidas separadas do conteúdo oficial.

## Estrutura

```
data/
  srd/          PDF do SRD 5.2.1 (fonte oficial)
  homebrew/     regras da casa em .md ou .txt
docs/
  TCC.md                 conteúdo acadêmico (estrutura ABNT)
  MedievaIA_TCC.docx     documento final
backend/
  medievaia/
    config.py       variáveis de ambiente e caminhos
    srd.py          PDF -> documentos estruturados
    homebrew.py     .md/.txt -> documentos estruturados
    chunking.py     divisão respeitando limites de seção
    embeddings.py   geração de embeddings em lote (OpenAI)
    db.py           PostgreSQL + pgvector
    rag.py          recuperação + geração da resposta
    cli.py          interface de linha de comando
  database/schema.sql
  tests/
  output/         artefatos de auditoria gerados pela ingestão
```

## Instalação

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate            # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env              # preencha OPENAI_API_KEY e DB_PASSWORD
```

Requer um PostgreSQL com a extensão `pgvector`. Há duas formas de apontar para
ele no `.env`:

- **Nuvem** (Neon, Supabase): cole a connection string em `DATABASE_URL`.
- **Local**: preencha `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` e `DB_PORT`.

`DATABASE_URL` tem prioridade quando preenchida. O esquema e a extensão são
aplicados automaticamente na primeira ingestão.

## Uso

```bash
python -m medievaia.cli ingest srd --dry-run   # só gera o JSON de auditoria
python -m medievaia.cli ingest srd             # + embeddings + carga no banco
python -m medievaia.cli ingest homebrew
python -m medievaia.cli status
python -m medievaia.cli ask "Como funciona o ataque furtivo do ladino?"
python -m medievaia.cli ask "Como funciona um crítico?" --source homebrew
python -m medievaia.cli serve                  # interface web em localhost:8000
```

### Interface web

`serve` sobe a API e a página numa única porta, sem etapa de build. A
documentação interativa da API fica em `/docs` (gerada pelo FastAPI).

| Rota | Função |
|---|---|
| `GET /` | interface de perguntas |
| `POST /api/ask` | pergunta e resposta com os trechos citados |
| `GET /api/status` | o que está carregado na base |

A ingestão é idempotente: reexecutar `ingest srd` substitui as linhas daquela
origem em vez de duplicá-las.

Para adicionar regras da casa, coloque arquivos `.md` ou `.txt` em
`data/homebrew/` e rode `ingest homebrew`. Os títulos Markdown (`#`, `##`)
viram a hierarquia de capítulo e seção.

## Testes

```bash
pip install -r requirements-dev.txt
python -m pytest
```

## Hospedagem

A aplicação é publicada como container. O `Dockerfile` na raiz sobe apenas a API
e a interface — a ingestão **não** roda no servidor: ela é executada uma vez a
partir da máquina local, apontando para o mesmo banco na nuvem.

### Render (plano gratuito)

1. *New* → *Web Service* → conecte o repositório. O `render.yaml` já define
   runtime, health check e as variáveis.
2. Em *Environment*, preencha `OPENAI_API_KEY` e `DATABASE_URL`. Ambas estão
   marcadas como `sync: false`, ou seja, **nunca são gravadas no repositório**.
3. Localmente, com o mesmo `DATABASE_URL` no `.env`, rode a ingestão:
   ```bash
   python -m medievaia.cli ingest srd
   python -m medievaia.cli ingest homebrew
   ```

O plano gratuito suspende o serviço após 15 minutos sem acesso, e o próximo
acesso leva cerca de 50 segundos para responder. Para uma demonstração ao vivo,
abra a URL alguns minutos antes ou execute localmente com `serve`.

### Proteções ativas

| Proteção | Onde |
|---|---|
| Segredos fora do repositório | `.gitignore`, `sync: false` no `render.yaml` |
| Limite de requisições por IP | `RATE_LIMIT_PER_HOUR`, padrão 30/hora |
| Validação de entrada | `pydantic`: pergunta de 3 a 500 caracteres, `limit` até 20 |
| Verificação de saúde | `GET /health` |

Como o endpoint consome a API da OpenAI a cada pergunta, defina também um limite
de gastos em *Billing → Limits* no painel da OpenAI.
