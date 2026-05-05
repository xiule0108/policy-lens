from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
import uuid

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Integer, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, GUID, JSONBCompatible, utc_now


def uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(GUID(), primary_key=True, default=uuid.uuid4)


def created_at_column() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


def updated_at_column() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    industry: Mapped[str | None] = mapped_column(Text)
    jurisdictions: Mapped[list] = mapped_column(JSONBCompatible, default=list, nullable=False)
    default_model_profile: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, default="active", nullable=False)
    created_at: Mapped[datetime] = created_at_column()
    updated_at: Mapped[datetime] = updated_at_column()

    documents: Mapped[list[Document]] = relationship(back_populates="project", cascade="all, delete-orphan")
    exports: Mapped[list[Export]] = relationship(back_populates="project")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = uuid_pk()
    project_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    document_role: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str | None] = mapped_column(Text)
    file_name: Mapped[str] = mapped_column(Text, nullable=False)
    file_type: Mapped[str] = mapped_column(Text, nullable=False)
    file_size: Mapped[int | None] = mapped_column(BigInteger)
    storage_key: Mapped[str | None] = mapped_column(Text)
    language: Mapped[str | None] = mapped_column(Text)
    page_count: Mapped[int | None] = mapped_column(Integer)
    parse_status: Mapped[str] = mapped_column(Text, default="pending", nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text)
    sha256: Mapped[str | None] = mapped_column(Text)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONBCompatible, default=dict, nullable=False)
    created_at: Mapped[datetime] = created_at_column()
    updated_at: Mapped[datetime] = updated_at_column()

    project: Mapped[Project] = relationship(back_populates="documents")
    chunks: Mapped[list[DocumentChunk]] = relationship(back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[uuid.UUID] = uuid_pk()
    document_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    project_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    page_start: Mapped[int | None] = mapped_column(Integer)
    page_end: Mapped[int | None] = mapped_column(Integer)
    section_title: Mapped[str | None] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[str] = mapped_column(Text, default="paragraph", nullable=False)
    token_count: Mapped[int | None] = mapped_column(Integer)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONBCompatible, default=dict, nullable=False)
    created_at: Mapped[datetime] = created_at_column()

    document: Mapped[Document] = relationship(back_populates="chunks")


class Policy(Base):
    __tablename__ = "policies"

    id: Mapped[uuid.UUID] = uuid_pk()
    source_id: Mapped[uuid.UUID | None] = mapped_column(GUID())
    title: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_title: Mapped[str | None] = mapped_column(Text)
    issuer: Mapped[str | None] = mapped_column(Text)
    issuer_level: Mapped[str | None] = mapped_column(Text)
    jurisdiction: Mapped[str | None] = mapped_column(Text)
    policy_type: Mapped[str | None] = mapped_column(Text)
    publish_date: Mapped[date | None] = mapped_column(Date)
    effective_date: Mapped[date | None] = mapped_column(Date)
    expiry_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(Text, default="unknown", nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text)
    sha256: Mapped[str | None] = mapped_column(Text)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONBCompatible, default=dict, nullable=False)
    created_at: Mapped[datetime] = created_at_column()
    updated_at: Mapped[datetime] = updated_at_column()

    versions: Mapped[list[PolicyVersion]] = relationship(back_populates="policy", cascade="all, delete-orphan")
    sections: Mapped[list[PolicySection]] = relationship(back_populates="policy", cascade="all, delete-orphan")


class PolicyVersion(Base):
    __tablename__ = "policy_versions"

    id: Mapped[uuid.UUID] = uuid_pk()
    policy_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("policies.id", ondelete="CASCADE"), nullable=False)
    version_label: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(Text)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    normalized_text: Mapped[str | None] = mapped_column(Text)
    sha256: Mapped[str | None] = mapped_column(Text)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONBCompatible, default=dict, nullable=False)
    created_at: Mapped[datetime] = created_at_column()

    policy: Mapped[Policy] = relationship(back_populates="versions")
    sections: Mapped[list[PolicySection]] = relationship(back_populates="version", cascade="all, delete-orphan")


class PolicySection(Base):
    __tablename__ = "policy_sections"

    id: Mapped[uuid.UUID] = uuid_pk()
    policy_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("policies.id", ondelete="CASCADE"), nullable=False)
    version_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("policy_versions.id", ondelete="CASCADE"), nullable=False)
    section_path: Mapped[str | None] = mapped_column(Text)
    heading: Mapped[str | None] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    token_count: Mapped[int | None] = mapped_column(Integer)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONBCompatible, default=dict, nullable=False)
    created_at: Mapped[datetime] = created_at_column()

    policy: Mapped[Policy] = relationship(back_populates="sections")
    version: Mapped[PolicyVersion] = relationship(back_populates="sections")


class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[uuid.UUID] = uuid_pk()
    project_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    document_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    claim_text: Mapped[str] = mapped_column(Text, nullable=False)
    claim_type: Mapped[str] = mapped_column(Text, nullable=False)
    topic: Mapped[str | None] = mapped_column(Text)
    industry: Mapped[str | None] = mapped_column(Text)
    jurisdiction: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[Decimal | None] = mapped_column(Numeric)
    source_chunk_ids: Mapped[list] = mapped_column(JSONBCompatible, default=list, nullable=False)
    created_at: Mapped[datetime] = created_at_column()


class PolicyMatch(Base):
    __tablename__ = "policy_matches"

    id: Mapped[uuid.UUID] = uuid_pk()
    project_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    analysis_id: Mapped[uuid.UUID | None] = mapped_column(GUID())
    claim_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False)
    policy_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("policies.id", ondelete="CASCADE"), nullable=False)
    policy_section_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("policy_sections.id", ondelete="SET NULL"))
    match_type: Mapped[str] = mapped_column(Text, nullable=False)
    relevance_score: Mapped[Decimal | None] = mapped_column(Numeric)
    reason: Mapped[str | None] = mapped_column(Text)
    evidence: Mapped[dict] = mapped_column(JSONBCompatible, default=dict, nullable=False)
    created_at: Mapped[datetime] = created_at_column()


class ImpactItem(Base):
    __tablename__ = "impact_items"

    id: Mapped[uuid.UUID] = uuid_pk()
    project_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    analysis_id: Mapped[uuid.UUID | None] = mapped_column(GUID())
    policy_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("policies.id", ondelete="SET NULL"))
    impact_subject: Mapped[str | None] = mapped_column(Text)
    impact_direction: Mapped[str | None] = mapped_column(Text)
    impact_horizon: Mapped[str | None] = mapped_column(Text)
    impact_mechanism: Mapped[str | None] = mapped_column(Text)
    market_variable: Mapped[str | None] = mapped_column(Text)
    analysis_text: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[Decimal | None] = mapped_column(Numeric)
    citations: Mapped[list] = mapped_column(JSONBCompatible, default=list, nullable=False)
    created_at: Mapped[datetime] = created_at_column()


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id: Mapped[uuid.UUID] = uuid_pk()
    project_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    document_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("documents.id", ondelete="SET NULL"))
    mode: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, default="queued", nullable=False)
    model_profile: Mapped[str | None] = mapped_column(Text)
    progress: Mapped[Decimal] = mapped_column(Numeric, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = created_at_column()
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AnalysisStep(Base):
    __tablename__ = "analysis_steps"

    id: Mapped[uuid.UUID] = uuid_pk()
    job_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("analysis_jobs.id", ondelete="CASCADE"), nullable=False)
    step_id: Mapped[str] = mapped_column(Text, nullable=False)
    tool_name: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, default="pending", nullable=False)
    model_provider: Mapped[str | None] = mapped_column(Text)
    model_name: Mapped[str | None] = mapped_column(Text)
    input_ref: Mapped[dict] = mapped_column(JSONBCompatible, default=dict, nullable=False)
    output_ref: Mapped[dict] = mapped_column(JSONBCompatible, default=dict, nullable=False)
    token_usage: Mapped[dict] = mapped_column(JSONBCompatible, default=dict, nullable=False)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = created_at_column()
    updated_at: Mapped[datetime] = updated_at_column()


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id: Mapped[uuid.UUID] = uuid_pk()
    project_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    job_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("analysis_jobs.id", ondelete="CASCADE"), nullable=False)
    summary: Mapped[dict] = mapped_column(JSONBCompatible, default=dict, nullable=False)
    claims: Mapped[list] = mapped_column(JSONBCompatible, default=list, nullable=False)
    related_policies: Mapped[list] = mapped_column(JSONBCompatible, default=list, nullable=False)
    impact_matrix: Mapped[list] = mapped_column(JSONBCompatible, default=list, nullable=False)
    report_markdown: Mapped[str | None] = mapped_column(Text)
    report_json: Mapped[dict] = mapped_column(JSONBCompatible, default=dict, nullable=False)
    created_at: Mapped[datetime] = created_at_column()


class Export(Base):
    __tablename__ = "exports"

    id: Mapped[uuid.UUID] = uuid_pk()
    project_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("projects.id", ondelete="CASCADE"))
    analysis_id: Mapped[uuid.UUID | None] = mapped_column(GUID())
    export_type: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, default="queued", nullable=False)
    formats: Mapped[list] = mapped_column(JSONBCompatible, default=list, nullable=False)
    storage_key: Mapped[str | None] = mapped_column(Text)
    manifest: Mapped[dict] = mapped_column(JSONBCompatible, default=dict, nullable=False)
    created_at: Mapped[datetime] = created_at_column()
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    project: Mapped[Project | None] = relationship(back_populates="exports")


class LLMProvider(Base):
    __tablename__ = "llm_providers"

    id: Mapped[uuid.UUID] = uuid_pk()
    provider_key: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    provider_type: Mapped[str] = mapped_column(Text, nullable=False)
    base_url: Mapped[str | None] = mapped_column(Text)
    api_key_env: Mapped[str | None] = mapped_column(Text)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    config: Mapped[dict] = mapped_column(JSONBCompatible, default=dict, nullable=False)
    created_at: Mapped[datetime] = created_at_column()
    updated_at: Mapped[datetime] = updated_at_column()


class ModelProfile(Base):
    __tablename__ = "model_profiles"

    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    profile_config: Mapped[dict] = mapped_column(JSONBCompatible, default=dict, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = created_at_column()
    updated_at: Mapped[datetime] = updated_at_column()
