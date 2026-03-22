from app.ingestion.types import ParsedSection


def chunk_section_text(section: ParsedSection, max_chars: int = 1200) -> list[str]:
    parts: list[str] = []
    paragraphs = [p.strip() for p in section.text.split("\n") if p.strip()]

    if not paragraphs:
        return []

    buffer = ""
    for paragraph in paragraphs:
        candidate = paragraph if not buffer else f"{buffer}\n{paragraph}"
        if len(candidate) <= max_chars:
            buffer = candidate
        else:
            if buffer:
                parts.append(buffer)
            if len(paragraph) <= max_chars:
                buffer = paragraph
            else:
                start = 0
                while start < len(paragraph):
                    end = min(start + max_chars, len(paragraph))
                    parts.append(paragraph[start:end])
                    start = end
                buffer = ""

    if buffer:
        parts.append(buffer)

    return parts
