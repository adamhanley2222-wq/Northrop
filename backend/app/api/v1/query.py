from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models.core import AnswerFeedback, AppUser, QueryRecord
from app.db.session import get_db
from app.query.service import run_query_pipeline
from app.schemas.query import FeedbackRequest, FeedbackResponse, QueryRequest, QueryResponse

router = APIRouter(tags=["query"])


@router.post("/query", response_model=QueryResponse)
def query(
    payload: QueryRequest,
    db: Session = Depends(get_db),
    user: AppUser = Depends(get_current_user),
) -> QueryResponse:
    response, _, _ = run_query_pipeline(
        db=db,
        question=payload.question,
        filter_input=payload.filters,
        session_id=payload.session_id,
        user=user,
    )
    return QueryResponse(**response)


@router.post("/query/feedback", response_model=FeedbackResponse)
def submit_feedback(
    payload: FeedbackRequest,
    db: Session = Depends(get_db),
    _: AppUser = Depends(get_current_user),
) -> FeedbackResponse:
    if payload.feedback_type not in {"helpful", "incomplete", "incorrect", "needs_more_evidence", "needs_more_challenge"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported feedback type")

    query_record = db.query(QueryRecord).filter(QueryRecord.id == UUID(payload.query_record_id)).first()
    if query_record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Query record not found")

    feedback = AnswerFeedback(
        query_record_id=query_record.id,
        feedback_type=payload.feedback_type,
        note=payload.note,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    return FeedbackResponse(id=str(feedback.id), query_record_id=str(feedback.query_record_id), feedback_type=feedback.feedback_type)
