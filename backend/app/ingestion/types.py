from dataclasses import dataclass


@dataclass
class ParsedSection:
    heading: str
    heading_level: int
    text: str
    page_start: int | None = None
    page_end: int | None = None
