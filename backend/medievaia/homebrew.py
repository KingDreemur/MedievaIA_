import re

from medievaia.config import HOMEBREW_DIR

EXTENSIONS = (".md", ".txt")
HEADING = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
MIN_CONTENT_CHARS = 20


def parse_file(path):
    documents = []
    stack = {}
    title = path.stem
    buffer = []

    def flush():
        content = "\n".join(buffer).strip()
        buffer.clear()
        if len(content) < MIN_CONTENT_CHARS:
            return
        documents.append(
            {
                "source_type": "homebrew",
                "source_name": path.stem,
                "page": None,
                "chapter": stack.get(1, path.stem),
                "section": stack.get(2, stack.get(1, path.stem)),
                "title": title,
                "type": "homebrew",
                "content": content,
            }
        )

    for line in path.read_text(encoding="utf-8").splitlines():
        match = HEADING.match(line)
        if not match:
            buffer.append(line)
            continue
        flush()
        level = len(match.group(1))
        title = match.group(2)
        stack = {depth: value for depth, value in stack.items() if depth < level}
        stack[level] = title

    flush()
    return documents


def parse_homebrew(directory=HOMEBREW_DIR):
    if not directory.exists():
        return []
    documents = []
    for path in sorted(directory.iterdir()):
        if path.suffix.lower() in EXTENSIONS:
            documents.extend(parse_file(path))
    return documents
