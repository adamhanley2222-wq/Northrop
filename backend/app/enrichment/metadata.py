from sqlalchemy.orm import Session

from app.db.models.core import BusinessUnit, Chunk, Division, Leader, Region, StrategicObjective, StrategicPillar
from app.services import get_openai_client


def _find_match(text: str, candidates: list[str]) -> str | None:
    lowered = text.lower()
    for candidate in candidates:
        if candidate and candidate.lower() in lowered:
            return candidate
    return None


def _detect_observation_type(text: str) -> str:
    lowered = text.lower()
    if any(word in lowered for word in ["risk", "issue", "blocker", "threat"]):
        return "risk"
    if any(word in lowered for word in ["opportunity", "upside", "potential"]):
        return "opportunity"
    if any(word in lowered for word in ["action", "owner", "next step", "due"]):
        return "action"
    if any(word in lowered for word in ["kpi", "metric", "%", "target", "performance"]):
        return "performance"
    return "observation"


def _detect_status(text: str) -> str:
    lowered = text.lower()
    if any(word in lowered for word in ["behind", "delayed", "late"]):
        return "delayed"
    if any(word in lowered for word in ["risk", "at risk", "challenge"]):
        return "at_risk"
    if any(word in lowered for word in ["complete", "achieved", "on track"]):
        return "on_track"
    return "unknown"


def _detect_trend(text: str) -> str:
    lowered = text.lower()
    if any(word in lowered for word in ["increase", "improved", "grew", "up"]):
        return "up"
    if any(word in lowered for word in ["decrease", "declined", "down", "reduced"]):
        return "down"
    return "flat"


def _detect_risk_severity(text: str) -> str:
    lowered = text.lower()
    if any(word in lowered for word in ["critical", "severe", "high"]):
        return "high"
    if any(word in lowered for word in ["moderate", "medium"]):
        return "medium"
    return "low"


def enrich_chunk_metadata(db: Session, chunk: Chunk) -> dict:
    text = chunk.text

    divisions = [row.name for row in db.query(Division).filter(Division.active.is_(True)).all()]
    business_units = [row.name for row in db.query(BusinessUnit).filter(BusinessUnit.active.is_(True)).all()]
    regions = [row.name for row in db.query(Region).filter(Region.active.is_(True)).all()]
    leaders = [row.full_name for row in db.query(Leader).filter(Leader.active.is_(True)).all()]
    pillars = [row.name for row in db.query(StrategicPillar).all()]
    objectives = [row.title for row in db.query(StrategicObjective).filter(StrategicObjective.active.is_(True)).all()]

    signal_strength = 0
    observation_type = _detect_observation_type(text)
    if observation_type != "observation":
        signal_strength += 1
    status = _detect_status(text)
    if status != "unknown":
        signal_strength += 1
    trend = _detect_trend(text)
    if trend != "flat":
        signal_strength += 1
    risk_severity = _detect_risk_severity(text)
    if "risk" in text.lower():
        signal_strength += 1

    confidence = min(0.95, 0.35 + (signal_strength * 0.15))

    metadata = dict(chunk.metadata_json or {})
    metadata.update(
        {
            "division_name": _find_match(text, divisions),
            "business_unit_name": _find_match(text, business_units),
            "region_name": _find_match(text, regions),
            "leader_name": _find_match(text, leaders),
            "strategic_pillar_name": _find_match(text, pillars),
            "strategic_objective_name": _find_match(text, objectives),
            "observation_type": observation_type if confidence >= 0.45 else None,
            "status": status if confidence >= 0.5 else "unknown",
            "trend": trend if confidence >= 0.5 else "flat",
            "risk_severity": risk_severity if observation_type == "risk" else None,
            "confidence": round(confidence, 2),
            "notes": "Heuristic enrichment applied with confidence gating",
        }
    )

    # Optional hook for future LLM-assisted enrichment.
    # Deterministic fallback remains default and primary behaviour.
    if confidence < 0.5:
        client = get_openai_client()
        if client is not None:
            metadata["notes"] = "Low-confidence heuristic tagging; LLM hook available but not enforced."

    return metadata


def enrich_document_chunks(db: Session, document_id) -> int:
    chunks = db.query(Chunk).filter(Chunk.document_id == document_id).all()
    for chunk in chunks:
        chunk.metadata_json = enrich_chunk_metadata(db, chunk)
        db.add(chunk)
    db.commit()
    return len(chunks)
