from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: UUID
    title: str
    document_type: str
    original_filename: str
    parse_status: str
    uploaded_at: datetime


class DocumentDetailResponse(DocumentResponse):
    mime_type: str
    file_path: str
    parse_confidence: float | None = None


class DocumentSectionResponse(BaseModel):
    id: UUID
    document_id: UUID
    heading: str
    heading_level: int
    section_order: int
    raw_text: str
    section_type: str
    page_start: int | None = None
    page_end: int | None = None


class ChunkResponse(BaseModel):
    id: UUID
    document_id: UUID
    document_section_id: UUID
    chunk_order: int
    text: str
    structural_path: str
    chunk_type: str
    metadata_json: dict
    page_ref_start: int | None = None
    page_ref_end: int | None = None
    published: bool = False


class ChunkMetadataPatch(BaseModel):
    metadata_json: dict
