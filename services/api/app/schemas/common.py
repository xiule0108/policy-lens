from datetime import date, datetime
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
ExportFormat = Literal["markdown", "txt", "html", "json"]


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


class PolicyResponse(BaseModel):
    id: str
    title: str
    normalized_title: str | None = None
    issuer: str | None = None
    issuer_level: str | None = None
    jurisdiction: str | None = None
    policy_type: str | None = None
    publish_date: date | None = None
    effective_date: date | None = None
    expiry_date: date | None = None
    status: str
    source_url: str | None = None
    sha256: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    evidence: list[EvidenceItem] = Field(default_factory=list)


class PolicyDetailResponse(PolicyResponse):
    current_version_id: str | None = None
    evidence: list[EvidenceItem] = Field(default_factory=list)


class PolicyListResponse(BaseModel):
    items: list[PolicyResponse]


class PolicySearchRequest(BaseModel):
    query: str
    jurisdictions: list[str] = Field(default_factory=list)
    policy_types: list[str] = Field(default_factory=list)
    limit: int = Field(default=10, ge=1, le=50)


class PolicySearchResponse(BaseModel):
    query: str
    total: int
    items: list[PolicyResponse]
    evidence: list[dict[str, Any]] = Field(default_factory=list)


class PolicyCreateFromDocumentRequest(BaseModel):
    document_id: UUID
    policy_id: UUID | None = None
    title: str | None = None
    issuer: str | None = None
    issuer_level: str | None = None
    jurisdiction: str | None = None
    policy_type: str | None = None
    publish_date: date | None = None
    effective_date: date | None = None
    expiry_date: date | None = None
    status: str = "unknown"
    version_label: str | None = None
    force_new_version: bool = False


class PolicyCreateFromDocumentResponse(BaseModel):
    policy_id: str
    version_id: str
    section_count: int
    title: str
    status: str
    already_ingested: bool = False


class PolicyVersionResponse(BaseModel):
    id: str
    policy_id: str
    version_label: str | None = None
    source_url: str | None = None
    captured_at: datetime
    sha256: str | None = None
    is_current: bool
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class PolicyVersionListResponse(BaseModel):
    items: list[PolicyVersionResponse]


class PolicySectionResponse(BaseModel):
    id: str
    policy_id: str
    version_id: str
    section_path: str | None = None
    heading: str | None = None
    content: str
    order_index: int
    token_count: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class PolicySectionListResponse(BaseModel):
    items: list[PolicySectionResponse]
    total: int


class PolicyOriginalResponse(BaseModel):
    policy_id: str
    version_id: str
    title: str
    source_url: str | None = None
    captured_at: datetime
    sha256: str | None = None
    normalized_text: str
    sections_count: int
    metadata: dict[str, Any] = Field(default_factory=dict)


class AnalysisJobRequest(BaseModel):
    project_id: UUID
    document_ids: list[UUID] = Field(default_factory=list)
    analysis_types: list[str] = Field(default_factory=lambda: ["policy_deep_dive"])
    model_profile: str = "china_balanced"
    use_llm: bool = False
    provider_id: str | None = None
    model: str | None = None


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


class AnalysisJobResponse(BaseModel):
    id: str
    project_id: str
    document_id: str | None = None
    status: str
    mode: str
    model_profile: str | None = None
    progress: float
    result_id: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None


class AnalysisStepResponse(BaseModel):
    id: str
    job_id: str
    step_id: str
    tool_name: str | None = None
    status: str
    model_provider: str | None = None
    model_name: str | None = None
    input_ref: dict[str, Any] = Field(default_factory=dict)
    output_ref: dict[str, Any] = Field(default_factory=dict)
    token_usage: dict[str, Any] = Field(default_factory=dict)
    latency_ms: int | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class AnalysisStepListResponse(BaseModel):
    items: list[AnalysisStepResponse]


class ResearchPlanResponse(BaseModel):
    plan: dict[str, Any]


class AnalysisResultResponse(BaseModel):
    id: str
    project_id: str
    job_id: str
    summary: dict[str, Any] = Field(default_factory=dict)
    claims: list[dict[str, Any]] = Field(default_factory=list)
    related_policies: list[dict[str, Any]] = Field(default_factory=list)
    impact_matrix: list[dict[str, Any]] = Field(default_factory=list)
    report_markdown: str | None = None
    report_json: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class PolicyOriginalExportRequest(BaseModel):
    project_id: UUID | None = None
    policy_ids: list[UUID] = Field(default_factory=list)
    cited_section_ids: list[UUID] = Field(default_factory=list)
    mode: ExportMode = "related_policy_bundle"
    formats: list[ExportFormat] = Field(default_factory=lambda: ["markdown", "txt", "html", "json"])
    include_snapshots: bool = True
    include_sections: bool = True
    include_checksums: bool = True


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


class ExportDetailResponse(BaseModel):
    export_id: str
    project_id: str | None = None
    analysis_id: str | None = None
    export_type: str
    status: str
    formats: list[str] = Field(default_factory=list)
    storage_key: str | None = None
    manifest: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    finished_at: datetime | None = None


class LLMProvider(BaseModel):
    id: str
    display_name: str
    provider_family: str
    aliases: list[str] = Field(default_factory=list)
    api_key_env: str | None = None
    api_key_configured: bool = False
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
    model_name: str | None = None
    enabled: bool = False
    openai_compatible: bool = True
    local_provider: bool = False


class LLMProviderTestRequest(BaseModel):
    model: str | None = None
    prompt: str = "请用一句话说明你可以正常响应。"
    timeout_seconds: int = Field(default=30, ge=1, le=300)


class LLMProviderTestResponse(BaseModel):
    provider_id: str
    status: Literal["passed", "failed", "not_configured"]
    latency_ms: int
    message: str
    model: str | None = None
    token_usage: dict[str, Any] = Field(default_factory=dict)
    evidence: list[EvidenceItem] = Field(default_factory=list)


class LLMChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1)


class LLMChatCompletionRequest(BaseModel):
    provider_id: str
    model: str | None = None
    messages: list[LLMChatMessage] = Field(min_length=1)
    temperature: float = Field(default=0.2, ge=0, le=2)
    max_tokens: int | None = Field(default=None, ge=1)
    timeout_seconds: int = Field(default=60, ge=1, le=300)
    log_step: bool = True
    job_id: UUID | None = None


class LLMChatCompletionResponse(BaseModel):
    provider_id: str
    model: str
    content: str
    token_usage: dict[str, Any] = Field(default_factory=dict)
    latency_ms: int
    step_id: str | None = None
