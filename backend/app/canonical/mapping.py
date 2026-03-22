from sqlalchemy.orm import Session

from app.db.models.core import (
    ActionItem,
    Chunk,
    EvidenceLink,
    Observation,
    Opportunity,
    PerformanceSignal,
    Risk,
)


def _reset_chunk_entities(db: Session, chunk_id) -> None:
    db.query(Observation).filter(Observation.chunk_id == chunk_id).delete()
    db.query(PerformanceSignal).filter(PerformanceSignal.chunk_id == chunk_id).delete()
    db.query(Risk).filter(Risk.chunk_id == chunk_id).delete()
    db.query(Opportunity).filter(Opportunity.chunk_id == chunk_id).delete()
    db.query(ActionItem).filter(ActionItem.chunk_id == chunk_id).delete()
    db.query(EvidenceLink).filter(EvidenceLink.chunk_id == chunk_id).delete()


def map_chunk_to_canonical_records(db: Session, chunk: Chunk) -> list[str]:
    _reset_chunk_entities(db, chunk.id)

    metadata = chunk.metadata_json or {}
    confidence = float(metadata.get("confidence") or 0.0)
    created_entities: list[str] = []

    if confidence < 0.4:
        db.commit()
        return created_entities

    observation = Observation(
        chunk_id=chunk.id,
        summary=chunk.text[:500],
        observation_type=metadata.get("observation_type"),
        status=metadata.get("status"),
        confidence=metadata.get("confidence"),
    )
    db.add(observation)
    db.flush()
    db.add(EvidenceLink(chunk_id=chunk.id, entity_type="Observation", entity_id=str(observation.id)))
    created_entities.append("Observation")

    obs_type = (metadata.get("observation_type") or "").lower()
    if obs_type == "performance" and confidence >= 0.5:
        signal = PerformanceSignal(
            chunk_id=chunk.id,
            signal_text=chunk.text[:500],
            trend=metadata.get("trend"),
            status=metadata.get("status"),
            confidence=metadata.get("confidence"),
        )
        db.add(signal)
        db.flush()
        db.add(EvidenceLink(chunk_id=chunk.id, entity_type="PerformanceSignal", entity_id=str(signal.id)))
        created_entities.append("PerformanceSignal")

    if obs_type == "risk" and confidence >= 0.55:
        risk = Risk(
            chunk_id=chunk.id,
            description=chunk.text[:500],
            severity=metadata.get("risk_severity"),
            status=metadata.get("status"),
            owner_name=metadata.get("leader_name"),
        )
        db.add(risk)
        db.flush()
        db.add(EvidenceLink(chunk_id=chunk.id, entity_type="Risk", entity_id=str(risk.id)))
        created_entities.append("Risk")

    if obs_type == "opportunity" and confidence >= 0.55:
        opportunity = Opportunity(
            chunk_id=chunk.id,
            description=chunk.text[:500],
            confidence=metadata.get("confidence"),
        )
        db.add(opportunity)
        db.flush()
        db.add(EvidenceLink(chunk_id=chunk.id, entity_type="Opportunity", entity_id=str(opportunity.id)))
        created_entities.append("Opportunity")

    if obs_type == "action" and confidence >= 0.5:
        action_item = ActionItem(
            chunk_id=chunk.id,
            description=chunk.text[:500],
            owner_name=metadata.get("leader_name"),
            due_date_text=None,
            status=metadata.get("status"),
        )
        db.add(action_item)
        db.flush()
        db.add(EvidenceLink(chunk_id=chunk.id, entity_type="ActionItem", entity_id=str(action_item.id)))
        created_entities.append("ActionItem")

    db.commit()
    return created_entities


def map_document_chunks(db: Session, document_id) -> int:
    chunks = db.query(Chunk).filter(Chunk.document_id == document_id).all()
    for chunk in chunks:
        map_chunk_to_canonical_records(db, chunk)
    return len(chunks)
