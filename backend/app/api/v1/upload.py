import hashlib
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.models.core import AppUser, Chunk, Document, DocumentType
from app.db.session import get_db
from app.enrichment.metadata import enrich_document_chunks
from app.ingestion.parsers import SUPPORTED_MIME_TYPES
from app.ingestion.workflow import parse_and_store_document
from app.publish.workflow import publish_document
from app.canonical.mapping import map_document_chunks
from app.vector.indexing import index_document_chunks
from app.schemas.documents import (
    ChunkMetadataPatch,
    ChunkResponse,
    DocumentDetailResponse,
    DocumentResponse,
    DocumentSectionResponse,
)

router = APIRouter(tags=["documents"])


def _get_document_or_404(db: Session, document_id: UUID) -> Document:
    document = db.query(Document).filter(Document.id == document_id).first()
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return document


@router.post("/documents/upload", response_model=DocumentDetailResponse)
async def upload_document(
    title: str = Form(...),
    document_type: DocumentType = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: AppUser = Depends(get_current_user),
) -> DocumentDetailResponse:
    mime_type = file.content_type or ""
    suffix = Path(file.filename or "upload.bin").suffix.lower()

    if mime_type not in SUPPORTED_MIME_TYPES and suffix not in {".pdf", ".docx"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF and DOCX files are supported")

    storage_dir = Path(settings.storage_root)
    storage_dir.mkdir(parents=True, exist_ok=True)

    output_path = storage_dir / f"{uuid4()}{suffix}"
    data = await file.read()
    output_path.write_bytes(data)

    normalized_mime = mime_type or ("application/pdf" if suffix == ".pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    source_hash = hashlib.sha256(data).hexdigest()

    document = Document(
        title=title,
        original_filename=file.filename or "unknown",
        document_type=document_type,
        mime_type=normalized_mime,
        file_path=str(output_path),
        source_hash=source_hash,
        uploaded_by="admin",
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    parse_and_store_document(db, document)
    db.refresh(document)

    return DocumentDetailResponse(
        id=document.id,
        title=document.title,
        document_type=document.document_type.value,
        original_filename=document.original_filename,
        parse_status=document.parse_status.value,
        uploaded_at=document.uploaded_at,
        mime_type=document.mime_type,
        file_path=document.file_path,
        parse_confidence=document.parse_confidence,
    )


@router.post("/documents/{document_id}/reparse")
def reparse_document(document_id: UUID, db: Session = Depends(get_db), _: AppUser = Depends(get_current_user)) -> dict:
    document = _get_document_or_404(db, document_id)
    result = parse_and_store_document(db, document)
    db.refresh(document)
    return {
        "document_id": str(document.id),
        "parse_status": document.parse_status.value,
        "sections": result["sections"],
        "chunks": result["chunks"],
        "enriched_chunks": result.get("enriched_chunks", 0),
        "canonical_chunks": result.get("canonical_chunks", 0),
    }


@router.post("/documents/{document_id}/publish")
def publish_document_endpoint(document_id: UUID, db: Session = Depends(get_db), _: AppUser = Depends(get_current_user)) -> dict:
    document = _get_document_or_404(db, document_id)
    published_count = publish_document(db, document)
    db.refresh(document)
    return {
        "document_id": str(document.id),
        "parse_status": document.parse_status.value,
        "published_chunks": published_count,
    }


@router.post("/documents/{document_id}/enrich")
def enrich_document(document_id: UUID, db: Session = Depends(get_db), _: AppUser = Depends(get_current_user)) -> dict:
    document = _get_document_or_404(db, document_id)
    enriched_count = enrich_document_chunks(db, document.id)
    return {"document_id": str(document.id), "enriched_chunks": enriched_count}


@router.post("/documents/{document_id}/map-canonical")
def map_document_canonical(document_id: UUID, db: Session = Depends(get_db), _: AppUser = Depends(get_current_user)) -> dict:
    document = _get_document_or_404(db, document_id)
    mapped_count = map_document_chunks(db, document.id)
    return {"document_id": str(document.id), "mapped_chunks": mapped_count}


@router.post("/documents/{document_id}/reindex")
def reindex_document(document_id: UUID, db: Session = Depends(get_db), _: AppUser = Depends(get_current_user)) -> dict:
    document = _get_document_or_404(db, document_id)
    stats = index_document_chunks(db, document)
    return {"document_id": str(document.id), **stats}


@router.get("/documents", response_model=list[DocumentResponse])
def list_documents(db: Session = Depends(get_db), _: AppUser = Depends(get_current_user)) -> list[DocumentResponse]:
    documents = db.query(Document).order_by(Document.uploaded_at.desc()).all()
    return [
        DocumentResponse(
            id=doc.id,
            title=doc.title,
            document_type=doc.document_type.value,
            original_filename=doc.original_filename,
            parse_status=doc.parse_status.value,
            uploaded_at=doc.uploaded_at,
        )
        for doc in documents
    ]


@router.get("/documents/{document_id}", response_model=DocumentDetailResponse)
def get_document(document_id: UUID, db: Session = Depends(get_db), _: AppUser = Depends(get_current_user)) -> DocumentDetailResponse:
    doc = _get_document_or_404(db, document_id)
    return DocumentDetailResponse(
        id=doc.id,
        title=doc.title,
        document_type=doc.document_type.value,
        original_filename=doc.original_filename,
        parse_status=doc.parse_status.value,
        uploaded_at=doc.uploaded_at,
        mime_type=doc.mime_type,
        file_path=doc.file_path,
        parse_confidence=doc.parse_confidence,
    )


@router.get("/documents/{document_id}/sections", response_model=list[DocumentSectionResponse])
def get_document_sections(document_id: UUID, db: Session = Depends(get_db), _: AppUser = Depends(get_current_user)) -> list[DocumentSectionResponse]:
    document = _get_document_or_404(db, document_id)
    sections = sorted(document.sections, key=lambda item: item.section_order)
    return [
        DocumentSectionResponse(
            id=section.id,
            document_id=section.document_id,
            heading=section.heading,
            heading_level=section.heading_level,
            section_order=section.section_order,
            raw_text=section.raw_text,
            section_type=section.section_type.value,
            page_start=section.page_start,
            page_end=section.page_end,
        )
        for section in sections
    ]


@router.get("/documents/{document_id}/chunks", response_model=list[ChunkResponse])
def get_document_chunks(document_id: UUID, db: Session = Depends(get_db), _: AppUser = Depends(get_current_user)) -> list[ChunkResponse]:
    _get_document_or_404(db, document_id)
    chunks = db.query(Chunk).filter(Chunk.document_id == document_id).order_by(Chunk.chunk_order.asc()).all()

    return [
        ChunkResponse(
            id=chunk.id,
            document_id=chunk.document_id,
            document_section_id=chunk.document_section_id,
            chunk_order=chunk.chunk_order,
            text=chunk.text,
            structural_path=chunk.structural_path,
            chunk_type=chunk.chunk_type.value,
            metadata_json=chunk.metadata_json,
            page_ref_start=chunk.page_ref_start,
            page_ref_end=chunk.page_ref_end,
            published=chunk.published,
        )
        for chunk in chunks
    ]


@router.get("/chunks/{chunk_id}", response_model=ChunkResponse)
def get_chunk(chunk_id: UUID, db: Session = Depends(get_db), _: AppUser = Depends(get_current_user)) -> ChunkResponse:
    chunk = db.query(Chunk).filter(Chunk.id == chunk_id).first()
    if chunk is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chunk not found")

    return ChunkResponse(
        id=chunk.id,
        document_id=chunk.document_id,
        document_section_id=chunk.document_section_id,
        chunk_order=chunk.chunk_order,
        text=chunk.text,
        structural_path=chunk.structural_path,
        chunk_type=chunk.chunk_type.value,
        metadata_json=chunk.metadata_json,
        page_ref_start=chunk.page_ref_start,
        page_ref_end=chunk.page_ref_end,
        published=chunk.published,
    )


@router.patch("/chunks/{chunk_id}/metadata", response_model=ChunkResponse)
def patch_chunk_metadata(
    chunk_id: UUID,
    payload: ChunkMetadataPatch,
    db: Session = Depends(get_db),
    _: AppUser = Depends(get_current_user),
) -> ChunkResponse:
    chunk = db.query(Chunk).filter(Chunk.id == chunk_id).first()
    if chunk is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chunk not found")

    chunk.metadata_json = payload.metadata_json
    db.add(chunk)
    db.commit()
    db.refresh(chunk)

    return ChunkResponse(
        id=chunk.id,
        document_id=chunk.document_id,
        document_section_id=chunk.document_section_id,
        chunk_order=chunk.chunk_order,
        text=chunk.text,
        structural_path=chunk.structural_path,
        chunk_type=chunk.chunk_type.value,
        metadata_json=chunk.metadata_json,
        page_ref_start=chunk.page_ref_start,
        page_ref_end=chunk.page_ref_end,
        published=chunk.published,
    )
