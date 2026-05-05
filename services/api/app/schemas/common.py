from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


ExportMode = Literal[
    "single_policy_full_text",
    "related_policy_bundle",
    "cited_sections_only",
    "evidence_bundle",
    "machine_readable_json",
]


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
    jurisdiction_focus: list[str] = Field(default_factory=list)
    industry_focus: list[str] = Field(default_factory=list)


class Project(ProjectCreate):
    id: str
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


class DocumentListResponse(BaseModel):
    items: list[Document]


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
    project_id: str | None = None
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
