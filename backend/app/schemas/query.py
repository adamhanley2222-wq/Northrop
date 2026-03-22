from pydantic import BaseModel


class QueryRequest(BaseModel):
    question: str
    filters: dict | None = None
    session_id: str | None = None


class QueryResponse(BaseModel):
    session_id: str
    query_record_id: str
    intent: str
    direct_answer: str
    source_backed_statements: list[str]
    inferred_observations: list[str]
    key_evidence: list[dict]
    comparison_view: dict | None = None
    gaps: list[str]
    executive_questions: list[str]
    sources: list[dict]
    debug: dict | None = None


class FeedbackRequest(BaseModel):
    query_record_id: str
    feedback_type: str
    note: str | None = None


class FeedbackResponse(BaseModel):
    id: str
    query_record_id: str
    feedback_type: str
