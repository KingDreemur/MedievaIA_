import re

import pymupdf

from medievaia.config import SRD_PDF

SOURCE_NAME = "SRD 5.2.1"
RUNNING_HEADER = "System Reference Document"
MIN_CONTENT_CHARS = 20

CHAPTER_TYPES = {
    "Playing the Game": "rule",
    "Character Creation": "rule",
    "Classes": "class",
    "Character Origins": "origin",
    "Feats": "feat",
    "Equipment": "equipment",
    "Spells": "spell",
    "Rules Glossary": "rule",
    "Gameplay Toolbox": "rule",
    "Magic Items": "magic_item",
    "Monsters": "monster",
    "Animals": "monster",
}

HEADING_LEVELS = ((20, 0), (16, 1), (13, 2))


def chapter_type(chapter):
    for prefix, kind in CHAPTER_TYPES.items():
        if chapter.startswith(prefix):
            return kind
    return "rule"


def heading_level(size):
    for minimum, level in HEADING_LEVELS:
        if size >= minimum:
            return level
    return 3


def is_heading_span(span):
    font = span["font"]
    if "SC700" in font:
        return True
    if not font.startswith("GillSans"):
        return False
    if "SemiBold" not in font and "Bold" not in font:
        return False
    return span["size"] >= 10.5


def chapter_ranges(document):
    starts = [
        (page, title)
        for level, title, page in document.get_toc()
        if level == 2
    ]
    ranges = []
    for index, (page, title) in enumerate(starts):
        end = starts[index + 1][0] - 1 if index + 1 < len(starts) else document.page_count
        ranges.append((page, end, title))
    return ranges


def chapter_at(ranges, page):
    for start, end, title in ranges:
        if start <= page <= end:
            return title
    return None


TYPOGRAPHIC = {
    "‘": "'", "’": "'", "“": '"', "”": '"',
    "−": "-", "–": "-", "—": "-", " ": " ",
}


def page_lines(page):
    for index, block in enumerate(page.get_text("dict")["blocks"]):
        for line in block.get("lines", []):
            spans = [span for span in line["spans"] if span["text"].strip()]
            if spans:
                yield index, spans


def line_text(spans):
    text = "".join(span["text"] for span in spans)
    for source, target in TYPOGRAPHIC.items():
        text = text.replace(source, target)
    return re.sub(r"\s+", " ", text).strip()


def join_lines(lines):
    paragraph = ""
    for text in lines:
        if not paragraph:
            paragraph = text
        elif paragraph.endswith("-") and text[:1].islower():
            paragraph = paragraph[:-1] + text
        else:
            paragraph = f"{paragraph} {text}"
    return paragraph


def is_noise(text):
    return not text or text.isdigit() or text.startswith(RUNNING_HEADER)


def parse_srd(pdf_path=SRD_PDF):
    # ponytail: tabelas de atributos de monstros saem achatadas ("Str21+5 +5");
    # usar page.find_tables() se a precisao numerica virar requisito.
    document = pymupdf.open(pdf_path)
    ranges = chapter_ranges(document)

    documents = []
    stack = {}
    paragraphs = {}
    current = None

    def flush():
        nonlocal paragraphs
        content = "\n".join(
            join_lines(lines) for lines in paragraphs.values() if lines
        ).strip()
        paragraphs = {}
        if not current or len(content) < MIN_CONTENT_CHARS:
            return
        documents.append({**current, "content": content})

    previous_chapter = None
    for number, page in enumerate(document, start=1):
        chapter = chapter_at(ranges, number)
        if not chapter:
            continue

        if chapter != previous_chapter:
            flush()
            stack = {}
            current = None
            previous_chapter = chapter

        for block, spans in page_lines(page):
            text = line_text(spans)
            if is_noise(text):
                continue

            if all(is_heading_span(span) for span in spans):
                flush()
                level = heading_level(max(span["size"] for span in spans))
                stack = {depth: title for depth, title in stack.items() if depth < level}
                stack[level] = text
                current = {
                    "source_type": "srd",
                    "source_name": SOURCE_NAME,
                    "page": number,
                    "chapter": chapter,
                    "section": stack.get(1) or chapter,
                    "title": text,
                    "type": chapter_type(chapter),
                }
                continue

            if current:
                paragraphs.setdefault((number, block), []).append(text)

    flush()
    return documents
