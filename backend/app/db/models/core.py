import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DocumentType(str, enum.Enum):
    annual_strategy = "annual_strategy"
    quarterly_report = "quarterly_report"
    supporting_doc = "supporting_doc"


class ParseStatus(str, enum.Enum):
    pending = "pending"
    parsed = "parsed"
    review_required = "review_required"
    failed = "failed"
    published = "published"


class SectionType(str, enum.Enum):
    heading_block = "heading_block"
    narrative = "narrative"
    metric_block = "metric_block"
    risk_block = "risk_block"
    opportunity_block = "opportunity_block"
    action_block = "action_block"
    table_context = "table_context"
    other = "other"


class ChunkType(str, enum.Enum):
    narrative = "narrative"
    metric = "metric"
    risk = "risk"
    opportunity = "opportunity"
    action = "action"
    table_summary = "table_summary"
    mixed = "mixed"


class PeriodType(str, enum.Enum):
    quarter = "quarter"
    annual = "annual"


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    document_type: Mapped[DocumentType] = mapped_column(Enum(DocumentType, name="document_type"), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(128), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    source_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    version_label: Mapped[str | None] = mapped_column(String(128), nullable=True)
    uploaded_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    reporting_period_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("reporting_periods.id"), nullable=True)
    parse_status: Mapped[ParseStatus] = mapped_column(Enum(ParseStatus, name="parse_status"), nullable=False, default=ParseStatus.pending)
    parse_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    sections: Mapped[list["DocumentSection"]] = relationship(back_populates="document", cascade="all, delete-orphan")
    chunks: Mapped[list["Chunk"]] = relationship(back_populates="document", cascade="all, delete-orphan")
    tables: Mapped[list["TableExtract"]] = relationship(back_populates="document", cascade="all, delete-orphan")


class DocumentSection(Base):
    __tablename__ = "document_sections"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True)
    parent_section_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("document_sections.id"), nullable=True)
    heading: Mapped[str] = mapped_column(String(512), nullable=False)
    heading_level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    section_order: Mapped[int] = mapped_column(Integer, nullable=False)
    page_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    section_type: Mapped[SectionType] = mapped_column(Enum(SectionType, name="section_type"), nullable=False, default=SectionType.narrative)
    extraction_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    document: Mapped["Document"] = relationship(back_populates="sections")


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True)
    document_section_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("document_sections.id"), nullable=False, index=True)
    chunk_order: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    embedding_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    page_ref_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_ref_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    structural_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    chunk_type: Mapped[ChunkType] = mapped_column(Enum(ChunkType, name="chunk_type"), nullable=False, default=ChunkType.narrative)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    document: Mapped["Document"] = relationship(back_populates="chunks")


class TableExtract(Base):
    __tablename__ = "table_extracts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True)
    document_section_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("document_sections.id"), nullable=True)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_table_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    markdown_table: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    document: Mapped["Document"] = relationship(back_populates="tables")


class Division(Base):
    __tablename__ = "divisions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    code: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class BusinessUnit(Base):
    __tablename__ = "business_units"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    division_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("divisions.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class Region(Base):
    __tablename__ = "regions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    code: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class Leader(Base):
    __tablename__ = "leaders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class ReportingPeriod(Base):
    __tablename__ = "reporting_periods"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    label: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    period_type: Mapped[PeriodType] = mapped_column(Enum(PeriodType, name="period_type"), nullable=False, default=PeriodType.quarter)
    fiscal_year: Mapped[int] = mapped_column(Integer, nullable=False)
    quarter: Mapped[int | None] = mapped_column(Integer, nullable=True)
    start_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[Date | None] = mapped_column(Date, nullable=True)


class StrategicPillar(Base):
    __tablename__ = "strategic_pillars"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class StrategicObjective(Base):
    __tablename__ = "strategic_objectives"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    strategic_pillar_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("strategic_pillars.id"), nullable=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class ObjectiveMapping(Base):
    __tablename__ = "objective_mappings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chunk_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("chunks.id"), nullable=False, index=True)
    strategic_objective_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("strategic_objectives.id"), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)


class AppUser(Base):
    __tablename__ = "app_users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


class Observation(Base):
    __tablename__ = "observations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chunk_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("chunks.id"), nullable=False, index=True, unique=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    observation_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


class PerformanceSignal(Base):
    __tablename__ = "performance_signals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chunk_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("chunks.id"), nullable=False, index=True)
    signal_text: Mapped[str] = mapped_column(Text, nullable=False)
    trend: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


class Risk(Base):
    __tablename__ = "risks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chunk_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("chunks.id"), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    owner_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


class Opportunity(Base):
    __tablename__ = "opportunities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chunk_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("chunks.id"), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


class ActionItem(Base):
    __tablename__ = "action_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chunk_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("chunks.id"), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    owner_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    due_date_text: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


class EvidenceLink(Base):
    __tablename__ = "evidence_links"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chunk_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("chunks.id"), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


class QuerySession(Base):
    __tablename__ = "query_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("app_users.id"), nullable=True)
    session_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


class QueryRecord(Base):
    __tablename__ = "query_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("query_sessions.id"), nullable=True, index=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("app_users.id"), nullable=True, index=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    intent: Mapped[str] = mapped_column(String(64), nullable=False)
    filters_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    response_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


class AnswerFeedback(Base):
    __tablename__ = "answer_feedback"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query_record_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("query_records.id"), nullable=False, index=True)
    feedback_type: Mapped[str] = mapped_column(String(64), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
