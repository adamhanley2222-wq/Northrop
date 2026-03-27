"""initial schema

Revision ID: 20260322_0001
Revises:
Create Date: 2026-03-22 00:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260322_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";")

    op.create_table(
        "reporting_periods",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("label", sa.String(length=64), nullable=False, unique=True),
        sa.Column("period_type", sa.Enum("quarter", "annual", name="period_type"), nullable=False),
        sa.Column("fiscal_year", sa.Integer(), nullable=False),
        sa.Column("quarter", sa.Integer(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
    )

    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("original_filename", sa.String(length=512), nullable=False),
        sa.Column("document_type", sa.Enum("annual_strategy", "quarterly_report", "supporting_doc", name="document_type"), nullable=False),
        sa.Column("mime_type", sa.String(length=128), nullable=False),
        sa.Column("file_path", sa.String(length=1024), nullable=False),
        sa.Column("source_hash", sa.String(length=128), nullable=False),
        sa.Column("version_label", sa.String(length=128), nullable=True),
        sa.Column("uploaded_by", sa.String(length=255), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reporting_period_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("reporting_periods.id"), nullable=True),
        sa.Column("parse_status", sa.Enum("pending", "parsed", "review_required", "failed", "published", name="parse_status"), nullable=False),
        sa.Column("parse_confidence", sa.Float(), nullable=True),
    )
    op.create_index("ix_documents_source_hash", "documents", ["source_hash"])

    op.create_table(
        "document_sections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id"), nullable=False),
        sa.Column("parent_section_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("document_sections.id"), nullable=True),
        sa.Column("heading", sa.String(length=512), nullable=False),
        sa.Column("heading_level", sa.Integer(), nullable=False),
        sa.Column("section_order", sa.Integer(), nullable=False),
        sa.Column("page_start", sa.Integer(), nullable=True),
        sa.Column("page_end", sa.Integer(), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("section_type", sa.Enum(
            "heading_block", "narrative", "metric_block", "risk_block", "opportunity_block", "action_block", "table_context", "other", name="section_type"
        ), nullable=False),
        sa.Column("extraction_confidence", sa.Float(), nullable=True),
    )
    op.create_index("ix_document_sections_document_id", "document_sections", ["document_id"])

    op.create_table(
        "chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id"), nullable=False),
        sa.Column("document_section_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("document_sections.id"), nullable=False),
        sa.Column("chunk_order", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.Column("embedding_id", sa.String(length=256), nullable=True),
        sa.Column("page_ref_start", sa.Integer(), nullable=True),
        sa.Column("page_ref_end", sa.Integer(), nullable=True),
        sa.Column("structural_path", sa.String(length=1024), nullable=False),
        sa.Column("chunk_type", sa.Enum("narrative", "metric", "risk", "opportunity", "action", "table_summary", "mixed", name="chunk_type"), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("published", sa.Boolean(), nullable=False),
    )
    op.create_index("ix_chunks_document_id", "chunks", ["document_id"])
    op.create_index("ix_chunks_document_section_id", "chunks", ["document_section_id"])

    op.create_table(
        "table_extracts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id"), nullable=False),
        sa.Column("document_section_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("document_sections.id"), nullable=True),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("raw_table_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("markdown_table", sa.Text(), nullable=True),
        sa.Column("summary_text", sa.Text(), nullable=True),
    )
    op.create_index("ix_table_extracts_document_id", "table_extracts", ["document_id"])

    op.create_table(
        "divisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False, unique=True),
        sa.Column("code", sa.String(length=64), nullable=True, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False),
    )

    op.create_table(
        "business_units",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("division_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("divisions.id"), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=True, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False),
    )

    op.create_table(
        "regions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False, unique=True),
        sa.Column("code", sa.String(length=64), nullable=True, unique=True),
        sa.Column("active", sa.Boolean(), nullable=False),
    )

    op.create_table(
        "leaders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("role_title", sa.String(length=255), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False),
    )

    op.create_table(
        "strategic_pillars",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False, unique=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
    )

    op.create_table(
        "strategic_objectives",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("strategic_pillar_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("strategic_pillars.id"), nullable=True),
        sa.Column("code", sa.String(length=64), nullable=False, unique=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False),
    )

    op.create_table(
        "objective_mappings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("chunk_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("chunks.id"), nullable=False),
        sa.Column("strategic_objective_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("strategic_objectives.id"), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=True),
    )
    op.create_index("ix_objective_mappings_chunk_id", "objective_mappings", ["chunk_id"])
    op.create_index("ix_objective_mappings_strategic_objective_id", "objective_mappings", ["strategic_objective_id"])

    op.create_table(
        "app_users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("is_admin", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_app_users_email", "app_users", ["email"])


def downgrade() -> None:
    op.drop_index("ix_app_users_email", table_name="app_users")
    op.drop_table("app_users")
    op.drop_index("ix_objective_mappings_strategic_objective_id", table_name="objective_mappings")
    op.drop_index("ix_objective_mappings_chunk_id", table_name="objective_mappings")
    op.drop_table("objective_mappings")
    op.drop_table("strategic_objectives")
    op.drop_table("strategic_pillars")
    op.drop_table("leaders")
    op.drop_table("regions")
    op.drop_table("business_units")
    op.drop_table("divisions")
    op.drop_index("ix_table_extracts_document_id", table_name="table_extracts")
    op.drop_table("table_extracts")
    op.drop_index("ix_chunks_document_section_id", table_name="chunks")
    op.drop_index("ix_chunks_document_id", table_name="chunks")
    op.drop_table("chunks")
    op.drop_index("ix_document_sections_document_id", table_name="document_sections")
    op.drop_table("document_sections")
    op.drop_index("ix_documents_source_hash", table_name="documents")
    op.drop_table("documents")
    op.drop_table("reporting_periods")

    op.execute("DROP TYPE IF EXISTS chunk_type")
    op.execute("DROP TYPE IF EXISTS section_type")
    op.execute("DROP TYPE IF EXISTS parse_status")
    op.execute("DROP TYPE IF EXISTS document_type")
    op.execute("DROP TYPE IF EXISTS period_type")
