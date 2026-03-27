from typing import Any

from openai import OpenAI
from pinecone import Pinecone
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models.core import Chunk, Document


def _openai_client() -> OpenAI | None:
    if not settings.openai_api_key:
        return None
    return OpenAI(api_key=settings.openai_api_key)


def _pinecone_index():
    if not settings.pinecone_api_key:
        return None
    client = Pinecone(api_key=settings.pinecone_api_key)
    return client.Index(settings.pinecone_index_name)


def _embed_text(text: str) -> list[float]:
    client = _openai_client()
    if client is None:
        # Deterministic local fallback for development without OpenAI.
        vector = [0.0] * settings.embedding_dimension
        for idx, token in enumerate(text.split()[: settings.embedding_dimension]):
            vector[idx] = float((sum(ord(ch) for ch in token) % 1000) / 1000)
        return vector

    response = client.embeddings.create(model=settings.openai_embedding_model, input=text[:8000])
    return response.data[0].embedding


def delete_document_vectors(document_id: str) -> None:
    index = _pinecone_index()
    if index is None:
        return
    index.delete(
        namespace=settings.pinecone_namespace,
        filter={"document_id": {"$eq": document_id}},
    )


def index_document_chunks(db: Session, document: Document) -> dict[str, int]:
    chunks = db.query(Chunk).filter(Chunk.document_id == document.id, Chunk.published.is_(True)).all()

    index = _pinecone_index()
    upserted = 0

    if index is not None:
        delete_document_vectors(str(document.id))

    for chunk in chunks:
        vector_id = str(chunk.id)
        vector_values = _embed_text(chunk.text)

        if index is not None:
            metadata: dict[str, Any] = {
                "document_id": str(chunk.document_id),
                "chunk_id": str(chunk.id),
                "document_section_id": str(chunk.document_section_id),
                "text": chunk.text[:1200],
                "page_ref_start": chunk.page_ref_start,
                "page_ref_end": chunk.page_ref_end,
            }
            metadata.update(chunk.metadata_json or {})
            index.upsert(
                vectors=[{"id": vector_id, "values": vector_values, "metadata": metadata}],
                namespace=settings.pinecone_namespace,
            )

        chunk.embedding_id = vector_id
        db.add(chunk)
        upserted += 1

    db.commit()
    return {"published_chunks": len(chunks), "vectors_upserted": upserted}


def semantic_search(question: str, top_k: int = 20, filters: dict | None = None) -> list[dict]:
    if not settings.enable_semantic_retrieval:
        return []
    index = _pinecone_index()
    if index is None:
        return []

    query_vector = _embed_text(question)
    response = index.query(
        vector=query_vector,
        top_k=top_k,
        include_metadata=True,
        namespace=settings.pinecone_namespace,
        filter=filters,
    )
    return [
        {
            "id": match["id"] if isinstance(match, dict) else match.id,
            "score": match["score"] if isinstance(match, dict) else match.score,
            "metadata": match.get("metadata", {}) if isinstance(match, dict) else (match.metadata or {}),
        }
        for match in response.get("matches", [])
    ]
