"""phase3 query and canonical tables

Revision ID: 20260322_0002
Revises: 20260322_0001
Create Date: 2026-03-22 00:30:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260322_0002"
down_revision = "20260322_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "observations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("chunk_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("chunks.id"), nullable=False, unique=True),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("observation_type", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_observations_chunk_id", "observations", ["chunk_id"])

    op.create_table(
        "performance_signals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("chunk_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("chunks.id"), nullable=False),
        sa.Column("signal_text", sa.Text(), nullable=False),
        sa.Column("trend", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_performance_signals_chunk_id", "performance_signals", ["chunk_id"])

    op.create_table(
        "risks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("chunk_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("chunks.id"), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=True),
        sa.Column("owner_name", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_risks_chunk_id", "risks", ["chunk_id"])

    op.create_table(
        "opportunities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("chunk_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("chunks.id"), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_opportunities_chunk_id", "opportunities", ["chunk_id"])

    op.create_table(
        "action_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("chunk_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("chunks.id"), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("owner_name", sa.String(length=255), nullable=True),
        sa.Column("due_date_text", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_action_items_chunk_id", "action_items", ["chunk_id"])

    op.create_table(
        "evidence_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("chunk_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("chunks.id"), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.String(length=64), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_evidence_links_chunk_id", "evidence_links", ["chunk_id"])

    op.create_table(
        "query_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("app_users.id"), nullable=True),
        sa.Column("session_label", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "query_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("query_sessions.id"), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("app_users.id"), nullable=True),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("intent", sa.String(length=64), nullable=False),
        sa.Column("filters_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("response_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_query_records_session_id", "query_records", ["session_id"])
    op.create_index("ix_query_records_user_id", "query_records", ["user_id"])

    op.create_table(
        "answer_feedback",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("query_record_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("query_records.id"), nullable=False),
        sa.Column("feedback_type", sa.String(length=64), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_answer_feedback_query_record_id", "answer_feedback", ["query_record_id"])


def downgrade() -> None:
    op.drop_index("ix_answer_feedback_query_record_id", table_name="answer_feedback")
    op.drop_table("answer_feedback")
    op.drop_index("ix_query_records_user_id", table_name="query_records")
    op.drop_index("ix_query_records_session_id", table_name="query_records")
    op.drop_table("query_records")
    op.drop_table("query_sessions")
    op.drop_index("ix_evidence_links_chunk_id", table_name="evidence_links")
    op.drop_table("evidence_links")
    op.drop_index("ix_action_items_chunk_id", table_name="action_items")
    op.drop_table("action_items")
    op.drop_index("ix_opportunities_chunk_id", table_name="opportunities")
    op.drop_table("opportunities")
    op.drop_index("ix_risks_chunk_id", table_name="risks")
    op.drop_table("risks")
    op.drop_index("ix_performance_signals_chunk_id", table_name="performance_signals")
    op.drop_table("performance_signals")
    op.drop_index("ix_observations_chunk_id", table_name="observations")
    op.drop_table("observations")
