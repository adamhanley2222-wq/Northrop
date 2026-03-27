from datetime import datetime
import re
from dataclasses import replace
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.core import AppUser, QueryRecord, QuerySession
from app.query.filters import filters_to_dict, resolve_filters
from app.query.intent import classify_intent
from app.query.retrieval import retrieve_relevant_chunks
from app.query.synthesis import build_structured_answer

QUARTER_PATTERN = re.compile(r"\bq([1-4])\b", re.IGNORECASE)


def get_or_create_session(db: Session, session_id: str | None, user: AppUser | None) -> QuerySession:
    if session_id:
        existing = db.query(QuerySession).filter(QuerySession.id == UUID(session_id)).first()
        if existing:
            existing.updated_at = datetime.utcnow()
            db.add(existing)
            db.commit()
            db.refresh(existing)
            return existing

    session = QuerySession(user_id=user.id if user else None, session_label="Executive query session")
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def run_query_pipeline(
    db: Session,
    question: str,
    filter_input: dict | None,
    session_id: str | None,
    user: AppUser | None,
) -> tuple[dict, QuerySession, QueryRecord]:
    intent = classify_intent(question)
    filters = resolve_filters(db, question, filter_input)
    retrieved, retrieval_debug = retrieve_relevant_chunks(db, question, filters)
    comparison_periods_debug: dict | None = None

    if intent == "comparison":
        requested_quarters = sorted({int(match.group(1)) for match in QUARTER_PATTERN.finditer(question)})
        if len(requested_quarters) >= 2:
            per_period: dict[str, dict] = {}
            combined: list[tuple] = []
            for quarter in requested_quarters[:2]:
                period_filters = replace(filters, quarter=quarter, document_type="quarterly_report")
                period_results, period_debug = retrieve_relevant_chunks(db, question, period_filters, limit=6)
                per_period[f"Q{quarter}"] = {
                    "retrieved_chunks": len(period_results),
                    "top_chunk_ids": [str(chunk.id) for chunk, _ in period_results[:3]],
                    "debug": period_debug,
                }
                combined.extend(period_results)

            dedup_map = {str(chunk.id): (chunk, doc) for chunk, doc in combined}
            retrieved = list(dedup_map.values())
            comparison_periods_debug = per_period
    response = build_structured_answer(question, intent, retrieved)
    if comparison_periods_debug:
        response["comparison_view"] = {
            "periods": comparison_periods_debug,
            "material_changes": ["Review differences in per-period retrieved evidence counts and top chunk sets."],
            "continuity": "Themes appearing across both periods indicate continuity.",
            "unresolved_issues": "Risk-related chunks that persist across periods should be escalated.",
        }

    session = get_or_create_session(db, session_id, user)
    record = QueryRecord(
        session_id=session.id,
        user_id=user.id if user else None,
        question=question,
        intent=intent,
        filters_json=filters_to_dict(filters),
        response_json=response,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    response["intent"] = intent
    response["query_record_id"] = str(record.id)
    response["session_id"] = str(session.id)
    response["debug"] = {
        "intent": intent,
        "matched_filters": filters_to_dict(filters),
        "retrieval": {**retrieval_debug, "final_selected_count": len(retrieved)},
        "comparison_periods": comparison_periods_debug,
    }
    return response, session, record
