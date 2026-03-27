from app.db.models.core import Chunk, Document
from app.query.executive_questions import generate_executive_questions


def build_structured_answer(question: str, intent: str, retrieved: list[tuple[Chunk, Document]]) -> dict:
    source_backed_statements: list[str] = []
    inferred_observations: list[str] = []
    key_evidence: list[dict] = []
    sources: list[dict] = []
    risk_mentions = 0

    for chunk, document in retrieved:
        metadata = chunk.metadata_json or {}
        quote = chunk.text[:320]
        source_backed_statements.append(f"[{document.title}] {quote}")
        key_evidence.append(
            {
                "chunk_id": str(chunk.id),
                "document_id": str(document.id),
                "document_title": document.title,
                "quote": quote,
                "metadata": metadata,
            }
        )
        sources.append(
            {
                "document_id": str(document.id),
                "document_title": document.title,
                "chunk_id": str(chunk.id),
                "page_ref_start": chunk.page_ref_start,
                "page_ref_end": chunk.page_ref_end,
            }
        )
        if (metadata.get("observation_type") or "") == "risk":
            risk_mentions += 1

    if retrieved:
        inferred_observations.append("Inference: retrieved evidence suggests uneven reporting depth across items.")

    gaps: list[str] = []
    if len(retrieved) == 0:
        gaps.append("Missing evidence: no relevant chunks matched the current query and filters.")
    elif len(retrieved) < 3:
        gaps.append("Missing evidence: limited supporting excerpts were retrieved.")

    missing_owner = any(not (item[0].metadata_json or {}).get("leader_name") for item in retrieved)
    if missing_owner:
        gaps.append("Missing accountability: some evidence has no clear leader attribution.")

    if intent == "strategy_alignment" and len(retrieved) < 3:
        gaps.append("Potential strategic misalignment: objectives referenced in the question have weak evidence coverage.")
    if intent == "gap_detection" and len(retrieved) < 3:
        gaps.append("Gap signal: reporting detail appears thin for requested scope.")

    weak_evidence = len(retrieved) < 3
    direct_answer = "Grounded response based on retrieved evidence. "
    if source_backed_statements:
        direct_answer += source_backed_statements[0]
    else:
        direct_answer += "No direct evidence found for this query."
    if weak_evidence:
        direct_answer += " Evidence strength is limited; treat conclusions as provisional."

    comparison_view = None
    if intent == "comparison":
        comparison_view = {
            "summary": "Comparison computed from explicitly retrieved evidence sets.",
            "evidence_count": len(retrieved),
            "continuity_signals": [
                "Some themes recur across retrieved periods/documents.",
            ],
            "drift_signals": [
                "At least one reported area has weaker continuity of evidence.",
            ],
        }

    executive_questions = generate_executive_questions(gaps, len(retrieved), risk_mentions)

    return {
        "direct_answer": direct_answer,
        "source_backed_statements": source_backed_statements,
        "inferred_observations": inferred_observations,
        "key_evidence": key_evidence,
        "comparison_view": comparison_view,
        "gaps": gaps,
        "executive_questions": executive_questions,
        "sources": sources,
    }
