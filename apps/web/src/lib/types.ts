export type EvidenceItem = {
  id: string;
  source_type: string;
  summary: string;
  confidence: number;
};

export type Project = {
  id: string;
  name: string;
  description?: string | null;
  industry?: string | null;
  jurisdictions: string[];
  default_model_profile?: string | null;
  status: string;
  created_at: string;
  updated_at: string;
};

export type DocumentRole = "research_article" | "policy" | "appendix";

export type DocumentRecord = {
  id: string;
  project_id: string;
  document_role: DocumentRole;
  title?: string | null;
  file_name: string;
  file_type: string;
  file_size?: number | null;
  content_type?: string | null;
  storage_key?: string | null;
  language?: string | null;
  page_count?: number | null;
  parse_status: string;
  source_url?: string | null;
  sha256?: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type Policy = {
  id: string;
  title: string;
  normalized_title?: string | null;
  issuer?: string | null;
  jurisdiction?: string | null;
  policy_type?: string | null;
  status: string;
  source_url?: string | null;
  sha256?: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type PolicySection = {
  id: string;
  policy_id: string;
  version_id: string;
  section_path?: string | null;
  heading?: string | null;
  content: string;
  order_index: number;
  metadata: Record<string, unknown>;
  created_at: string;
};

export type PolicyOriginal = {
  policy_id: string;
  version_id: string;
  title: string;
  source_url?: string | null;
  captured_at: string;
  sha256?: string | null;
  normalized_text: string;
  sections_count: number;
  metadata: Record<string, unknown>;
};

export type AnalysisJob = {
  id: string;
  project_id: string;
  document_id?: string | null;
  status: string;
  mode: string;
  model_profile?: string | null;
  progress: number;
  result_id?: string | null;
  created_at: string;
  started_at?: string | null;
  finished_at?: string | null;
};

export type AnalysisStep = {
  id: string;
  job_id: string;
  step_id: string;
  tool_name?: string | null;
  status: string;
  input_ref: Record<string, unknown>;
  output_ref: Record<string, unknown>;
  token_usage: Record<string, unknown>;
  latency_ms?: number | null;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
};

export type AnalysisResult = {
  id: string;
  project_id: string;
  job_id: string;
  summary: Record<string, unknown>;
  claims: Array<Record<string, unknown>>;
  related_policies: Array<Record<string, unknown>>;
  impact_matrix: Array<Record<string, unknown>>;
  report_markdown?: string | null;
  report_json: Record<string, unknown>;
  created_at: string;
};

export type AnalysisClaim = {
  id: string;
  project_id: string;
  document_id: string;
  claim_text: string;
  claim_type: string;
  confidence?: number | null;
  source_chunk_ids: string[];
  created_at: string;
};

export type PolicyMatch = {
  id: string;
  project_id: string;
  analysis_id?: string | null;
  claim_id: string;
  policy_id: string;
  policy_section_id?: string | null;
  match_type: string;
  relevance_score?: number | null;
  reason?: string | null;
  evidence: Record<string, unknown>;
  created_at: string;
};

export type ImpactItem = {
  id: string;
  project_id: string;
  analysis_id?: string | null;
  policy_id?: string | null;
  impact_subject?: string | null;
  impact_direction?: string | null;
  impact_horizon?: string | null;
  impact_mechanism?: string | null;
  market_variable?: string | null;
  analysis_text: string;
  confidence?: number | null;
  citations: Array<Record<string, unknown>>;
  created_at: string;
};

export type AnalysisReport = {
  job_id: string;
  result_id: string;
  report_markdown?: string | null;
  report_outline: Record<string, unknown>;
  fact_boundaries: Record<string, unknown>;
};

export type ExportRecord = {
  export_id: string;
  project_id?: string | null;
  analysis_id?: string | null;
  export_type: string;
  status: string;
  formats: string[];
  storage_key?: string | null;
  manifest: Record<string, unknown>;
  created_at: string;
  finished_at?: string | null;
};

export type ExportResponse = {
  export_id: string;
  status: string;
  mode: string;
  bundle_path?: string | null;
  manifest: Record<string, unknown>;
  evidence: EvidenceItem[];
};

export type LLMProvider = {
  id: string;
  display_name: string;
  provider_family: string;
  aliases: string[];
  api_key_env?: string | null;
  api_key_configured: boolean;
  base_url?: string | null;
  model_name?: string | null;
  enabled: boolean;
  openai_compatible: boolean;
  local_provider: boolean;
  notes?: string | null;
};
