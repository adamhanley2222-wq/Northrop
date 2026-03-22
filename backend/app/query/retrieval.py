from sqlalchemy.orm import Session
from uuid import UUID

from app.db.models.core import Chunk, Document, ParseStatus, ReportingPeriod
from app.query.filters import QueryFilters
from app.vector.indexing import semantic_search


def _matches_metadata_filter(chunk: Chunk, filters: QueryFilters) -> bool:
    metadata = chunk.metadata_json or {}

    def equals(key: str, value: str | None) -> bool:
        if not value:
            return True
        return str(metadata.get(key, "")).lower() == value.lower()

    return all(
        [
            equals("division_name", filters.division_name),
            equals("business_unit_name", filters.business_unit_name),
            equals("region_name", filters.region_name),
            equals("leader_name", filters.leader_name),
            equals("strategic_pillar_name", filters.strategic_pillar_name),
            equals("strategic_objective_name", filters.strategic_objective_name),
        ]
    )


def _matches_period(document: Document, filters: QueryFilters, db: Session) -> bool:
    if not filters.fiscal_year and not filters.quarter:
        return True
    if not document.reporting_period_id:
        return False
    period = db.query(ReportingPeriod).filter(ReportingPeriod.id == document.reporting_period_id).first()
    if period is None:
        return False
    if filters.fiscal_year and period.fiscal_year != filters.fiscal_year:
        return False
    if filters.quarter and period.quarter != filters.quarter:
        return False
    return True


def _text_score(question: str, chunk: Chunk) -> int:
    lowered = question.lower()
    score = 0
    text = chunk.text.lower()

    for token in lowered.split():
        if len(token) > 3 and token in text:
            score += 2

    metadata = chunk.metadata_json or {}
    for value in metadata.values():
        if isinstance(value, str) and value.lower() in lowered:
            score += 1

    return score


def _build_semantic_filter(filters: QueryFilters) -> dict | None:
    pinecone_filter: dict = {}
    for key in [
        "division_name",
        "business_unit_name",
        "region_name",
        "leader_name",
        "strategic_pillar_name",
        "strategic_objective_name",
    ]:
        value = getattr(filters, key)
        if value:
            pinecone_filter[key] = {"$eq": value}
    return pinecone_filter or None


def retrieve_relevant_chunks(
    db: Session,
    question: str,
    filters: QueryFilters,
    limit: int = 10,
) -> tuple[list[tuple[Chunk, Document]], dict]:
    base_rows = (
        db.query(Chunk, Document)
        .join(Document, Chunk.document_id == Document.id)
        .filter(Document.parse_status.in_([ParseStatus.parsed, ParseStatus.published]))
        .order_by(Document.uploaded_at.desc())
        .all()
    )

    candidate_map: dict[str, tuple[Chunk, Document, float]] = {}

    for chunk, document in base_rows:
        if filters.document_type and document.document_type.value != filters.document_type:
            continue
        if not _matches_period(document, filters, db):
            continue
        if not _matches_metadata_filter(chunk, filters):
            continue

        lexical_score = float(_text_score(question, chunk))
        if lexical_score > 0:
            candidate_map[str(chunk.id)] = (chunk, document, lexical_score)

    semantic_results = semantic_search(question, top_k=20, filters=_build_semantic_filter(filters))
    for item in semantic_results:
        chunk_id = item["id"]
        try:
            chunk_uuid = UUID(chunk_id)
        except Exception:
            continue
        chunk = db.query(Chunk).filter(Chunk.id == chunk_uuid).first()
        if chunk is None:
            continue
        document = db.query(Document).filter(Document.id == chunk.document_id).first()
        if document is None:
            continue
        if filters.document_type and document.document_type.value != filters.document_type:
            continue
        if not _matches_period(document, filters, db):
            continue
        if not _matches_metadata_filter(chunk, filters):
            continue

        semantic_score = float(item.get("score") or 0.0)
        existing = candidate_map.get(chunk_id)
        if existing:
            candidate_map[chunk_id] = (chunk, document, existing[2] + (semantic_score * 3))
        else:
            candidate_map[chunk_id] = (chunk, document, semantic_score * 3)

    ranked = sorted(candidate_map.values(), key=lambda item: item[2], reverse=True)
    selected = [(chunk, document) for chunk, document, _ in ranked[:limit]]

    debug = {
        "candidate_count": len(candidate_map),
        "semantic_match_count": len(semantic_results),
        "selected_count": len(selected),
        "top_chunk_ids": [str(chunk.id) for chunk, _ in selected[:5]],
    }
    return selected, debug
