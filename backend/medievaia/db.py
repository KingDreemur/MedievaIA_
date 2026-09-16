import psycopg2
from psycopg2.extras import RealDictCursor, execute_values

from medievaia.config import DATABASE_URL, DB_DSN, SCHEMA_FILE

COLUMNS = (
    "source_type", "source_name", "page",
    "chapter", "section", "title", "type", "content", "embedding",
)


def connect():
    try:
        return psycopg2.connect(DATABASE_URL) if DATABASE_URL else psycopg2.connect(**DB_DSN)
    except UnicodeDecodeError as error:
        # Erro de conexao chega antes da negociacao de encoding: num servidor
        # com mensagens em portugues os acentos vem em cp1252 e mascaram a
        # causa real (senha errada, banco inexistente) com um erro de unicode.
        raise psycopg2.OperationalError(
            error.object.decode("latin-1", "replace").strip()
        ) from None


def apply_schema():
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute(SCHEMA_FILE.read_text(encoding="utf-8"))


def replace_source(source_type, chunks, batch_size=200):
    rows = [
        tuple(
            str(chunk["embedding"]) if column == "embedding" else chunk.get(column)
            for column in COLUMNS
        )
        for chunk in chunks
    ]
    # Uma transacao unica com todos os vetores derruba a conexao em bancos de
    # plano gratuito; cada lote vai no seu proprio commit.
    connection = connect()
    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM chunks WHERE source_type = %s", (source_type,))
        connection.commit()

        for start in range(0, len(rows), batch_size):
            with connection.cursor() as cursor:
                execute_values(
                    cursor,
                    f"INSERT INTO chunks ({', '.join(COLUMNS)}) VALUES %s",
                    rows[start:start + batch_size],
                    template="(" + ", ".join(["%s"] * 8) + ", %s::vector)",
                )
            connection.commit()
    finally:
        connection.close()
    return len(rows)


def search(embedding, limit=5, source_type=None):
    filters = "WHERE source_type = %s" if source_type else ""
    parameters = [str(embedding)]
    if source_type:
        parameters.append(source_type)
    parameters.append(limit)

    with connect() as connection, connection.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            f"""
            SELECT source_type, source_name, page, chapter, section, title, type, content,
                   embedding <=> %s::vector AS distance
            FROM chunks
            {filters}
            ORDER BY distance
            LIMIT %s
            """,
            parameters,
        )
        return cursor.fetchall()


def composition():
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute(
            "SELECT type, COUNT(*) FROM chunks GROUP BY type ORDER BY COUNT(*) DESC"
        )
        return cursor.fetchall()


def counts():
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute(
            "SELECT source_type, source_name, COUNT(*) FROM chunks"
            " GROUP BY source_type, source_name ORDER BY source_type, source_name"
        )
        return cursor.fetchall()
