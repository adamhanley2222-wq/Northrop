from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models.core import AppUser, Document, DocumentType, StrategicObjective
from app.db.session import get_db

router = APIRouter(tags=["strategy"])


@router.get("/strategic-plans")
def list_strategic_plans(db: Session = Depends(get_db), _: AppUser = Depends(get_current_user)) -> list[dict]:
    documents = (
        db.query(Document)
        .filter(Document.document_type == DocumentType.annual_strategy)
        .order_by(Document.uploaded_at.desc())
        .all()
    )
    return [
        {
            "id": str(doc.id),
            "title": doc.title,
            "original_filename": doc.original_filename,
            "parse_status": doc.parse_status.value,
            "uploaded_at": doc.uploaded_at.isoformat(),
        }
        for doc in documents
    ]


@router.get("/strategic-objectives")
def list_strategic_objectives(db: Session = Depends(get_db), _: AppUser = Depends(get_current_user)) -> list[dict]:
    objectives = db.query(StrategicObjective).order_by(StrategicObjective.code.asc()).all()
    return [
        {
            "id": str(obj.id),
            "code": obj.code,
            "title": obj.title,
            "description": obj.description,
            "active": obj.active,
        }
        for obj in objectives
    ]
