import re
from pathlib import Path

import pdfplumber
from docx import Document as DocxDocument

from app.ingestion.types import ParsedSection

SUPPORTED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}

HEADING_REGEX = re.compile(r"^(\d+(\.\d+)*)\s+.+")


def _looks_like_heading(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if HEADING_REGEX.match(stripped):
        return True
    if len(stripped) <= 100 and stripped.upper() == stripped and any(ch.isalpha() for ch in stripped):
        return True
    return False


def parse_pdf(file_path: Path) -> list[ParsedSection]:
    sections: list[ParsedSection] = []
    current_heading = "Document Content"
    current_lines: list[str] = []
    current_page_start: int | None = None
    current_page_end: int | None = None

    with pdfplumber.open(file_path) as pdf:
        for page_index, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            for line in text.splitlines():
                line = line.strip()
                if not line:
                    continue
                if _looks_like_heading(line):
                    if current_lines:
                        sections.append(
                            ParsedSection(
                                heading=current_heading,
                                heading_level=1,
                                text="\n".join(current_lines).strip(),
                                page_start=current_page_start,
                                page_end=current_page_end,
                            )
                        )
                    current_heading = line
                    current_lines = []
                    current_page_start = page_index
                    current_page_end = page_index
                else:
                    if current_page_start is None:
                        current_page_start = page_index
                    current_page_end = page_index
                    current_lines.append(line)

    if current_lines:
        sections.append(
            ParsedSection(
                heading=current_heading,
                heading_level=1,
                text="\n".join(current_lines).strip(),
                page_start=current_page_start,
                page_end=current_page_end,
            )
        )

    return [section for section in sections if section.text]


def parse_docx(file_path: Path) -> list[ParsedSection]:
    doc = DocxDocument(file_path)
    sections: list[ParsedSection] = []
    current_heading = "Document Content"
    current_lines: list[str] = []

    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        if not text:
            continue

        style_name = paragraph.style.name.lower() if paragraph.style and paragraph.style.name else ""
        is_heading = style_name.startswith("heading") or _looks_like_heading(text)

        if is_heading:
            if current_lines:
                sections.append(ParsedSection(heading=current_heading, heading_level=1, text="\n".join(current_lines).strip()))
            current_heading = text
            current_lines = []
        else:
            current_lines.append(text)

    if current_lines:
        sections.append(ParsedSection(heading=current_heading, heading_level=1, text="\n".join(current_lines).strip()))

    return [section for section in sections if section.text]


def parse_document(file_path: Path, mime_type: str) -> list[ParsedSection]:
    if mime_type == "application/pdf":
        return parse_pdf(file_path)
    if mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return parse_docx(file_path)

    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        return parse_pdf(file_path)
    if suffix == ".docx":
        return parse_docx(file_path)

    raise ValueError(f"Unsupported file type: {mime_type}")
