MAX_CHARS = 1500
OVERLAP_CHARS = 200


def split_content(content, max_chars=MAX_CHARS, overlap=OVERLAP_CHARS):
    if len(content) <= max_chars:
        return [content]

    chunks = []
    current = ""
    for paragraph in content.split("\n"):
        if not paragraph.strip():
            continue
        if len(current) + len(paragraph) + 1 <= max_chars:
            current = f"{current}\n{paragraph}" if current else paragraph
            continue
        if current:
            chunks.append(current)
            current = current[-overlap:] + "\n" + paragraph if overlap else paragraph
        else:
            current = paragraph
        while len(current) > max_chars:
            chunks.append(current[:max_chars])
            current = current[max_chars - overlap:]
    if current.strip():
        chunks.append(current)
    return chunks


def chunk_documents(documents):
    chunks = []
    for document in documents:
        parts = split_content(document["content"])
        for position, content in enumerate(parts, start=1):
            chunk = dict(document)
            chunk["content"] = content
            chunk["part"] = position
            chunk["parts"] = len(parts)
            chunks.append(chunk)
    return chunks
