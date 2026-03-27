from sqlalchemy.orm import Session

from app.db.models.core import Chunk, Document, ParseStatus
from app.vector.indexing import index_document_chunks


def publish_document(db: Session, document: Document) -> int:
    chunks = db.query(Chunk).filter(Chunk.document_id == document.id).all()
    for chunk in chunks:
        chunk.published = True
        db.add(chunk)

    document.parse_status = ParseStatus.published
    db.add(document)
    db.commit()
    index_document_chunks(db, document)

    return len(chunks)
