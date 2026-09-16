import argparse
import json
import os
import sys

from medievaia import db, homebrew, rag, srd
from medievaia.chunking import chunk_documents
from medievaia.config import OUTPUT_DIR
from medievaia.embeddings import embed_texts

PARSERS = {"srd": srd.parse_srd, "homebrew": homebrew.parse_homebrew}


def report(done, total):
    print(f"  embeddings {done}/{total}", end="\r", flush=True)


def command_ingest(args):
    documents = PARSERS[args.source]()
    if not documents:
        print(f"nenhum documento encontrado para '{args.source}'")
        return 1

    chunks = chunk_documents(documents)
    print(f"{args.source}: {len(documents)} documentos -> {len(chunks)} chunks")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    artifact = OUTPUT_DIR / f"{args.source}_chunks.json"
    artifact.write_text(
        json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"artefato de auditoria: {artifact}")

    if args.dry_run:
        return 0

    vectors = embed_texts([chunk["content"] for chunk in chunks], progress=report)
    for chunk, vector in zip(chunks, vectors):
        chunk["embedding"] = vector

    db.apply_schema()
    inserted = db.replace_source(args.source, chunks)
    print(f"\n{inserted} chunks carregados no PostgreSQL")
    return 0


def command_ask(args):
    text, passages = rag.answer(args.question, limit=args.limit, source_type=args.source)
    print(f"\nPergunta: {args.question}\n")
    print(text)
    print("\nTrechos usados:")
    for passage in passages:
        location = f"p.{passage['page']}" if passage["page"] else "s/p"
        print(
            f"  [{passage['source_type']}] {passage['title']}"
            f" ({passage['chapter']} > {passage['section']}, {location})"
            f" distancia={passage['distance']:.4f}"
        )
    return 0


def command_serve(args):
    import uvicorn

    print(f"MedievaIA em http://{args.host}:{args.port}")
    uvicorn.run("medievaia.api:app", host=args.host, port=args.port)
    return 0


def command_status(args):
    rows = db.counts()
    if not rows:
        print("base vazia: rode 'ingest srd' primeiro")
        return 0
    for source_type, source_name, total in rows:
        print(f"  {total:>6}  {source_type:<9} {source_name}")
    return 0


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(prog="medievaia")
    commands = parser.add_subparsers(dest="command", required=True)

    ingest = commands.add_parser("ingest", help="extrai, gera embeddings e carrega no banco")
    ingest.add_argument("source", choices=sorted(PARSERS))
    ingest.add_argument("--dry-run", action="store_true", help="so gera o JSON, sem OpenAI/banco")
    ingest.set_defaults(handler=command_ingest)

    ask = commands.add_parser("ask", help="pergunta em linguagem natural")
    ask.add_argument("question")
    ask.add_argument("--limit", type=int, default=5)
    ask.add_argument("--source", choices=sorted(PARSERS), help="restringe a origem")
    ask.set_defaults(handler=command_ask)

    status = commands.add_parser("status", help="mostra o que esta carregado no banco")
    status.set_defaults(handler=command_status)

    serve = commands.add_parser("serve", help="sobe a interface web")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=int(os.getenv("PORT", "8000")))
    serve.set_defaults(handler=command_serve)

    args = parser.parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
