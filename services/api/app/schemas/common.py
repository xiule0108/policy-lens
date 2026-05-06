from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


ExportMode = Literal[
    "single_policy_full_text",
    "related_policy_bundle",
    "cited_sections_only",
    "evidence_bundle",
    "machine_readable_json",
]

DocumentRole = Literal["research_article", "policy", "appendix"]


class SourceRef(BaseModel):
    id: str | None = None
    title: str | None = None
    url: str | None = None
    publisher: str | None = None
    retrieved_at: datetime | None = None
    published_at: datetime | None = None
    sha256: str | None = None


class Citation(BaseModel):
    id: str
    source_id: str
    locator: str | None = None
    quote: str | None = None
    url: str | None = None


class EvidenceItem(BaseModel):
    id: str
    source_type: str
    summary: str
    confidence: float = Field(ge=0, le=1)
    source: SourceRef | None = None
    citations: list[Citation] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    version: str
    dependencies: dict[str, Any]


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None
    industry: str | None = None
    jurisdictions: list[str] = Field(default_factory=list)
    default_model_profile: str | None = None
    jurisdiction_focus: list[str] = Field(default_factory=list)
    industry_focus: list[str] = Field(default_factory=list)


class Project(ProjectCreate):
    id: str
    status: str = "active"
    created_at: datetime
    updated_at: datetime
    evidence: list[EvidenceItem] = Field(default_factory=list)


class ProjectListResponse(BaseModel):
    items: list[Project]


class DocumentUploadRequest(BaseModel):
    project_id: str
    filename: str
    content_type: str = "text/markdown"
    source: SourceRef = Field(default_factory=SourceRef)
    text_preview: str | None = None


class Document(BaseModel):
    id: str
    project_id: str
    filename: str
    content_type: str
    status: str
    parser: str
    uploaded_at: datetime
    source: SourceRef
    citations: list[Citation] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)


class DocumentResponse(BaseModel):
    id: str
    project_id: str
    document_role: DocumentRole
    title: str | None = None
    file_name: str
    file_type: str
    file_size: int | None = None
    content_type: str | None = None
    storage_key: str | None = None
    language: str | None = None
    page_count: int | None = None
    parse_status: str
    source_url: str | None = None
    sha256: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    evidence: list[EvidenceItem] = Field(default_factory=list)


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]


class DocumentParseResponse(BaseModel):
    document_id: str
    parse_status: str
    chunk_count: int
    page_count: int | None = None
    language: str | None = None
    title: str | None = None
    error: str | None = None


class DocumentChunkResponse(BaseModel):
    id: str
    document_id: str
    project_id: str
    chunk_index: int
    page_start: int | None = None
    page_end: int | None = None
    section_title: str | None = None
    content: str
    content_type: str
    token_count: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class DocumentChunkListResponse(BaseModel):
    items: list[DocumentChunkResponse]
    total: int


class Policy(BaseModel):
    id: str
    title: str
    issuer: str
    jurisdiction: str
    policy_type: str
    published_at: datetime | None = None
    effective_at: datetime | None = None
    summary: str
    source: SourceRef
    sha256: str
    citations: list[Citation] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)


class PolicyListResponse(BaseModel):
    items: list[Policy]


class PolicySearchRequest(BaseModel):
    query: str
    jurisdictions: list[str] = Field(default_factory=list)
    policy_types: list[str] = Field(default_factory=list)
    limit: int = Field(default=10, ge=1, le=50)


class PolicySearchResponse(BaseModel):
    query: str
    total: int
    items: list[Policy]
    evidence: list[dict[str, Any]] = Field(default_factory=list)


class AnalysisJobRequest(BaseModel):
    project_id: str
    document_ids: list[str] = Field(default_factory=list)
    analysis_types: list[str] = Field(default_factory=lambda: ["impact_matrix"])
    model_profile: str = "china_balanced"


class AnalysisJob(BaseModel):
    id: str
    project_id: str
    status: str
    analysis_types: list[str]
    model_profile: str
    created_at: datetime
    updated_at: datetime
    result_preview: dict[str, Any]
    evidence: list[EvidenceItem] = Field(default_factory=list)


class PolicyOriginalExportRequest(BaseModel):
    project_id: UUID | None = None
    policy_ids: list[str] = Field(default_factory=list)
    cited_section_ids: list[str] = Field(default_factory=list)
    mode: ExportMode = "related_policy_bundle"
    include_snapshots: bool = True


class ReportExportRequest(BaseModel):
    project_id: str
    report_format: Literal["markdown", "docx", "pdf", "json"] = "markdown"
    include_policy_originals: bool = True
    include_evidence_bundle: bool = True


class ExportResponse(BaseModel):
    export_id: str
    status: str
    mode: str
    bundle_path: str | None = None
    manifest: dict[str, Any]
    evidence: list[EvidenceItem] = Field(default_factory=list)


class LLMProvider(BaseModel):
    id: str
    display_name: str
    provider_family: str
    aliases: list[str] = Field(default_factory=list)
    api_key_env: str | None = None
    base_url: str | None = None
    model_name: str | None = None
    enabled: bool = False
    openai_compatible: bool = False
    local_provider: bool = False
    notes: str | None = None


class LLMProviderListResponse(BaseModel):
    items: list[LLMProvider]


class LLMProviderCreate(BaseModel):
    provider_id: str | None = None
    display_name: str
    provider_family: str
    aliases: list[str] = Field(default_factory=list)
    api_key_env: str | None = None
    base_url: str | None = None
    model_name: str
    enabled: bool = False
    openai_compatible: bool = True
    local_provider: bool = False


class LLMProviderTestResponse(BaseModel):
    provider_id: str
    status: Literal["mock_passed", "mock_failed"]
    latency_ms: int
    message: str
    evidence: list[EvidenceItem] = Field(default_factory=list)
