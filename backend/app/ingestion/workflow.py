from pathlib import Path

from sqlalchemy.orm import Session

from app.db.models.core import Chunk, ChunkType, Document, DocumentSection, ParseStatus, SectionType
from app.enrichment.metadata import enrich_document_chunks
from app.ingestion.chunking import chunk_section_text
from app.ingestion.parsers import parse_document
from app.canonical.mapping import map_document_chunks
from app.vector.indexing import delete_document_vectors


def _replace_document_content(db: Session, document_id) -> None:
    db.query(Chunk).filter(Chunk.document_id == document_id).delete()
    db.query(DocumentSection).filter(DocumentSection.document_id == document_id).delete()


def parse_and_store_document(db: Session, document: Document) -> dict[str, int]:
    document.parse_status = ParseStatus.pending
    db.add(document)
    db.commit()
    db.refresh(document)

    _replace_document_content(db, document.id)
    delete_document_vectors(str(document.id))

    sections_added = 0
    chunks_added = 0

    try:
        parsed_sections = parse_document(Path(document.file_path), document.mime_type)
        if not parsed_sections:
            document.parse_status = ParseStatus.review_required
            document.parse_confidence = 0.3
            db.add(document)
            db.commit()
            return {"sections": 0, "chunks": 0}

        for index, parsed in enumerate(parsed_sections, start=1):
            section = DocumentSection(
                document_id=document.id,
                heading=parsed.heading[:512],
                heading_level=parsed.heading_level,
                section_order=index,
                page_start=parsed.page_start,
                page_end=parsed.page_end,
                raw_text=parsed.text[:20000],
                section_type=SectionType.narrative,
                extraction_confidence=0.8,
            )
            db.add(section)
            db.flush()
            sections_added += 1

            chunk_texts = chunk_section_text(parsed)
            for chunk_index, chunk_text in enumerate(chunk_texts, start=1):
                chunk = Chunk(
                    document_id=document.id,
                    document_section_id=section.id,
                    chunk_order=chunk_index,
                    text=chunk_text,
                    token_count=max(1, len(chunk_text.split())),
                    page_ref_start=parsed.page_start,
                    page_ref_end=parsed.page_end,
                    structural_path=f"{section.heading}",
                    chunk_type=ChunkType.narrative,
                    metadata_json={"source": "phase2_parser", "section_order": index, "chunk_order": chunk_index},
                    published=False,
                )
                db.add(chunk)
                chunks_added += 1

        enriched_count = enrich_document_chunks(db, document.id)
        canonical_count = map_document_chunks(db, document.id)
        document.parse_status = ParseStatus.parsed
        document.parse_confidence = 0.85
        db.add(document)
        db.commit()
    except Exception:
        document.parse_status = ParseStatus.failed
        document.parse_confidence = 0.0
        db.add(document)
        db.commit()
        raise

    return {"sections": sections_added, "chunks": chunks_added, "enriched_chunks": enriched_count, "canonical_chunks": canonical_count}
