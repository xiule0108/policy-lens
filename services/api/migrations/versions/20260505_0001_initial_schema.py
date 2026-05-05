"""initial PolicyLens schema

Revision ID: 20260505_0001
Revises:
Create Date: 2026-05-05 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.types import TypeEngine


revision = "20260505_0001"
down_revision = None
branch_labels = None
depends_on = None


def uuid_type() -> TypeEngine:
    return sa.String(length=36).with_variant(postgresql.UUID(as_uuid=True), "postgresql")


def json_type() -> TypeEngine:
    return sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql")


def timestamp_column(name: str) -> sa.Column:
    return sa.Column(name, sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())


def metadata_column() -> sa.Column:
    return sa.Column("metadata", json_type(), nullable=False, server_default=sa.text("'{}'"))


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", uuid_type(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("industry", sa.Text(), nullable=True),
        sa.Column("jurisdictions", json_type(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("default_model_profile", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="active"),
        timestamp_column("created_at"),
        timestamp_column("updated_at"),
    )

    op.create_table(
        "policies",
        sa.Column("id", uuid_type(), primary_key=True),
        sa.Column("source_id", uuid_type(), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("normalized_title", sa.Text(), nullable=True),
        sa.Column("issuer", sa.Text(), nullable=True),
        sa.Column("issuer_level", sa.Text(), nullable=True),
        sa.Column("jurisdiction", sa.Text(), nullable=True),
        sa.Column("policy_type", sa.Text(), nullable=True),
        sa.Column("publish_date", sa.Date(), nullable=True),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="unknown"),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("sha256", sa.Text(), nullable=True),
        metadata_column(),
        timestamp_column("created_at"),
        timestamp_column("updated_at"),
    )

    op.create_table(
        "llm_providers",
        sa.Column("id", uuid_type(), primary_key=True),
        sa.Column("provider_key", sa.Text(), nullable=False, unique=True),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("provider_type", sa.Text(), nullable=False),
        sa.Column("base_url", sa.Text(), nullable=True),
        sa.Column("api_key_env", sa.Text(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("config", json_type(), nullable=False, server_default=sa.text("'{}'")),
        timestamp_column("created_at"),
        timestamp_column("updated_at"),
    )

    op.create_table(
        "model_profiles",
        sa.Column("id", uuid_type(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("profile_config", json_type(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false()),
        timestamp_column("created_at"),
        timestamp_column("updated_at"),
    )

    op.create_table(
        "documents",
        sa.Column("id", uuid_type(), primary_key=True),
        sa.Column("project_id", uuid_type(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_role", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("file_name", sa.Text(), nullable=False),
        sa.Column("file_type", sa.Text(), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=True),
        sa.Column("storage_key", sa.Text(), nullable=True),
        sa.Column("language", sa.Text(), nullable=True),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("parse_status", sa.Text(), nullable=False, server_default="pending"),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("sha256", sa.Text(), nullable=True),
        metadata_column(),
        timestamp_column("created_at"),
        timestamp_column("updated_at"),
    )

    op.create_table(
        "policy_versions",
        sa.Column("id", uuid_type(), primary_key=True),
        sa.Column("policy_id", uuid_type(), sa.ForeignKey("policies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version_label", sa.Text(), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("normalized_text", sa.Text(), nullable=True),
        sa.Column("sha256", sa.Text(), nullable=True),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.true()),
        metadata_column(),
        timestamp_column("created_at"),
    )

    op.create_table(
        "analysis_jobs",
        sa.Column("id", uuid_type(), primary_key=True),
        sa.Column("project_id", uuid_type(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_id", uuid_type(), sa.ForeignKey("documents.id", ondelete="SET NULL"), nullable=True),
        sa.Column("mode", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="queued"),
        sa.Column("model_profile", sa.Text(), nullable=True),
        sa.Column("progress", sa.Numeric(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        timestamp_column("created_at"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "exports",
        sa.Column("id", uuid_type(), primary_key=True),
        sa.Column("project_id", uuid_type(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=True),
        sa.Column("analysis_id", uuid_type(), nullable=True),
        sa.Column("export_type", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="queued"),
        sa.Column("formats", json_type(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("storage_key", sa.Text(), nullable=True),
        sa.Column("manifest", json_type(), nullable=False, server_default=sa.text("'{}'")),
        timestamp_column("created_at"),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "document_chunks",
        sa.Column("id", uuid_type(), primary_key=True),
        sa.Column("document_id", uuid_type(), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("project_id", uuid_type(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("page_start", sa.Integer(), nullable=True),
        sa.Column("page_end", sa.Integer(), nullable=True),
        sa.Column("section_title", sa.Text(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_type", sa.Text(), nullable=False, server_default="paragraph"),
        sa.Column("token_count", sa.Integer(), nullable=True),
        metadata_column(),
        timestamp_column("created_at"),
    )

    op.create_table(
        "policy_sections",
        sa.Column("id", uuid_type(), primary_key=True),
        sa.Column("policy_id", uuid_type(), sa.ForeignKey("policies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version_id", uuid_type(), sa.ForeignKey("policy_versions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("section_path", sa.Text(), nullable=True),
        sa.Column("heading", sa.Text(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=True),
        metadata_column(),
        timestamp_column("created_at"),
    )

    op.create_table(
        "claims",
        sa.Column("id", uuid_type(), primary_key=True),
        sa.Column("project_id", uuid_type(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_id", uuid_type(), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("claim_text", sa.Text(), nullable=False),
        sa.Column("claim_type", sa.Text(), nullable=False),
        sa.Column("topic", sa.Text(), nullable=True),
        sa.Column("industry", sa.Text(), nullable=True),
        sa.Column("jurisdiction", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Numeric(), nullable=True),
        sa.Column("source_chunk_ids", json_type(), nullable=False, server_default=sa.text("'[]'")),
        timestamp_column("created_at"),
    )

    op.create_table(
        "analysis_steps",
        sa.Column("id", uuid_type(), primary_key=True),
        sa.Column("job_id", uuid_type(), sa.ForeignKey("analysis_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("step_id", sa.Text(), nullable=False),
        sa.Column("tool_name", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="pending"),
        sa.Column("model_provider", sa.Text(), nullable=True),
        sa.Column("model_name", sa.Text(), nullable=True),
        sa.Column("input_ref", json_type(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("output_ref", json_type(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("token_usage", json_type(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        timestamp_column("created_at"),
        timestamp_column("updated_at"),
    )

    op.create_table(
        "analysis_results",
        sa.Column("id", uuid_type(), primary_key=True),
        sa.Column("project_id", uuid_type(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_id", uuid_type(), sa.ForeignKey("analysis_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("summary", json_type(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("claims", json_type(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("related_policies", json_type(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("impact_matrix", json_type(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("report_markdown", sa.Text(), nullable=True),
        sa.Column("report_json", json_type(), nullable=False, server_default=sa.text("'{}'")),
        timestamp_column("created_at"),
    )

    op.create_table(
        "policy_matches",
        sa.Column("id", uuid_type(), primary_key=True),
        sa.Column("project_id", uuid_type(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("analysis_id", uuid_type(), nullable=True),
        sa.Column("claim_id", uuid_type(), sa.ForeignKey("claims.id", ondelete="CASCADE"), nullable=False),
        sa.Column("policy_id", uuid_type(), sa.ForeignKey("policies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("policy_section_id", uuid_type(), sa.ForeignKey("policy_sections.id", ondelete="SET NULL"), nullable=True),
        sa.Column("match_type", sa.Text(), nullable=False),
        sa.Column("relevance_score", sa.Numeric(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("evidence", json_type(), nullable=False, server_default=sa.text("'{}'")),
        timestamp_column("created_at"),
    )

    op.create_table(
        "impact_items",
        sa.Column("id", uuid_type(), primary_key=True),
        sa.Column("project_id", uuid_type(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("analysis_id", uuid_type(), nullable=True),
        sa.Column("policy_id", uuid_type(), sa.ForeignKey("policies.id", ondelete="SET NULL"), nullable=True),
        sa.Column("impact_subject", sa.Text(), nullable=True),
        sa.Column("impact_direction", sa.Text(), nullable=True),
        sa.Column("impact_horizon", sa.Text(), nullable=True),
        sa.Column("impact_mechanism", sa.Text(), nullable=True),
        sa.Column("market_variable", sa.Text(), nullable=True),
        sa.Column("analysis_text", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Numeric(), nullable=True),
        sa.Column("citations", json_type(), nullable=False, server_default=sa.text("'[]'")),
        timestamp_column("created_at"),
    )


def downgrade() -> None:
    for table_name in (
        "impact_items",
        "policy_matches",
        "analysis_results",
        "analysis_steps",
        "claims",
        "policy_sections",
        "document_chunks",
        "exports",
        "analysis_jobs",
        "policy_versions",
        "documents",
        "model_profiles",
        "llm_providers",
        "policies",
        "projects",
    ):
        op.drop_table(table_name)
