import type {
  AnalysisClaim,
  AnalysisJob,
  AnalysisReport,
  AnalysisResult,
  AnalysisStep,
  DocumentRecord,
  DocumentRole,
  ExportRecord,
  ExportResponse,
  ImpactItem,
  LLMProvider,
  Policy,
  PolicyMatch,
  PolicyOriginal,
  PolicySection,
  Project
} from "./types";

export const API_BASE_URL = (process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000").replace(/\/$/, "");

export class ApiError extends Error {
  status: number;
  detail: unknown;

  constructor(status: number, detail: unknown) {
    super(typeof detail === "string" ? detail : `API request failed with status ${status}`);
    this.status = status;
    this.detail = detail;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: init?.body instanceof FormData ? init.headers : { "Content-Type": "application/json", ...init?.headers }
  });
  if (!response.ok) {
    let detail: unknown = response.statusText;
    try {
      detail = (await response.json()).detail ?? detail;
    } catch {
      // Keep status text when the API returns a non-JSON error.
    }
    throw new ApiError(response.status, detail);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export function apiErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return typeof error.detail === "string" ? error.detail : JSON.stringify(error.detail);
  }
  return error instanceof Error ? error.message : "未知错误";
}

export async function listProjects(): Promise<Project[]> {
  return (await request<{ items: Project[] }>("/api/projects")).items;
}

export async function getProject(projectId: string): Promise<Project> {
  return request<Project>(`/api/projects/${projectId}`);
}

export async function createProject(payload: {
  name: string;
  description?: string;
  industry?: string;
  jurisdictions?: string[];
  default_model_profile?: string;
}): Promise<Project> {
  return request<Project>("/api/projects", { method: "POST", body: JSON.stringify(payload) });
}

export async function listDocuments(projectId: string): Promise<DocumentRecord[]> {
  return (await request<{ items: DocumentRecord[] }>(`/api/documents?project_id=${encodeURIComponent(projectId)}`)).items;
}

export async function uploadDocument(payload: {
  projectId: string;
  documentRole: DocumentRole;
  title?: string;
  sourceUrl?: string;
  file: File;
}): Promise<DocumentRecord> {
  const form = new FormData();
  form.append("project_id", payload.projectId);
  form.append("document_role", payload.documentRole);
  if (payload.title) form.append("title", payload.title);
  if (payload.sourceUrl) form.append("source_url", payload.sourceUrl);
  form.append("file", payload.file);
  return request<DocumentRecord>("/api/documents/upload", { method: "POST", body: form });
}

export async function parseDocument(documentId: string) {
  return request(`/api/documents/${documentId}/parse`, { method: "POST" });
}

export async function listPolicies(): Promise<Policy[]> {
  return (await request<{ items: Policy[] }>("/api/policies")).items;
}

export async function searchPolicies(payload: {
  query: string;
  jurisdictions?: string[];
  policy_types?: string[];
  limit?: number;
}): Promise<Policy[]> {
  return (await request<{ items: Policy[] }>("/api/policies/search", { method: "POST", body: JSON.stringify(payload) })).items;
}

export async function ingestPolicyFromDocument(payload: {
  document_id: string;
  title?: string;
  issuer?: string;
  jurisdiction?: string;
  policy_type?: string;
  status?: string;
}) {
  return request<{ policy_id: string; version_id: string; section_count: number; title: string; status: string; already_ingested: boolean }>(
    "/api/policies/from-document",
    { method: "POST", body: JSON.stringify(payload) }
  );
}

export async function getPolicyOriginal(policyId: string): Promise<PolicyOriginal> {
  return request<PolicyOriginal>(`/api/policies/${policyId}/original`);
}

export async function getPolicySections(policyId: string): Promise<{ items: PolicySection[]; total: number }> {
  return request<{ items: PolicySection[]; total: number }>(`/api/policies/${policyId}/sections`);
}

export async function createAnalysisJob(payload: {
  project_id: string;
  document_ids: string[];
  analysis_types?: string[];
  model_profile?: string;
}): Promise<AnalysisJob> {
  return request<AnalysisJob>("/api/analysis/jobs", { method: "POST", body: JSON.stringify(payload) });
}

export async function listAnalysisJobs(projectId?: string): Promise<AnalysisJob[]> {
  const query = projectId ? `?project_id=${encodeURIComponent(projectId)}` : "";
  return (await request<{ items: AnalysisJob[] }>(`/api/analysis/jobs${query}`)).items;
}

export async function getAnalysisJob(jobId: string): Promise<AnalysisJob> {
  return request<AnalysisJob>(`/api/analysis/jobs/${jobId}`);
}

export async function getAnalysisSteps(jobId: string): Promise<AnalysisStep[]> {
  return (await request<{ items: AnalysisStep[] }>(`/api/analysis/jobs/${jobId}/steps`)).items;
}

export async function getAnalysisPlan(jobId: string): Promise<Record<string, unknown>> {
  return request<Record<string, unknown>>(`/api/analysis/jobs/${jobId}/plan`);
}

export async function getAnalysisResult(jobId: string): Promise<AnalysisResult> {
  return request<AnalysisResult>(`/api/analysis/jobs/${jobId}/result`);
}

export async function getAnalysisClaims(jobId: string): Promise<AnalysisClaim[]> {
  return (await request<{ items: AnalysisClaim[] }>(`/api/analysis/jobs/${jobId}/claims`)).items;
}

export async function getAnalysisPolicyMatches(jobId: string): Promise<PolicyMatch[]> {
  return (await request<{ items: PolicyMatch[] }>(`/api/analysis/jobs/${jobId}/policy-matches`)).items;
}

export async function getAnalysisEvidence(jobId: string): Promise<{
  job_id: string;
  result_id: string;
  claim_policy_map: Array<Record<string, unknown>>;
  fact_boundaries: Record<string, unknown>;
}> {
  return request(`/api/analysis/jobs/${jobId}/evidence`);
}

export async function getAnalysisImpactMatrix(jobId: string): Promise<ImpactItem[]> {
  return (await request<{ items: ImpactItem[] }>(`/api/analysis/jobs/${jobId}/impact-matrix`)).items;
}

export async function getAnalysisReport(jobId: string): Promise<AnalysisReport> {
  return request<AnalysisReport>(`/api/analysis/jobs/${jobId}/report`);
}

export async function createReportExport(payload: {
  job_id?: string;
  analysis_id?: string;
  formats?: string[];
  include_evidence_bundle?: boolean;
  include_impact_matrix?: boolean;
  include_policy_matches?: boolean;
}): Promise<ExportResponse> {
  return request<ExportResponse>("/api/exports/report", { method: "POST", body: JSON.stringify(payload) });
}

export async function createPolicyOriginalExport(payload: {
  project_id?: string;
  policy_ids?: string[];
  cited_section_ids?: string[];
  mode?: string;
  formats?: string[];
}): Promise<ExportResponse> {
  return request<ExportResponse>("/api/exports/policy-originals", { method: "POST", body: JSON.stringify(payload) });
}

export async function getExport(exportId: string): Promise<ExportRecord> {
  return request<ExportRecord>(`/api/exports/${exportId}`);
}

export function downloadExportUrl(exportId: string): string {
  return `${API_BASE_URL}/api/exports/${exportId}/download`;
}

export async function listLLMProviders(): Promise<LLMProvider[]> {
  return (await request<{ items: LLMProvider[] }>("/api/llm/providers")).items;
}

export async function upsertLLMProvider(payload: {
  provider_id?: string;
  display_name: string;
  provider_family: string;
  aliases?: string[];
  api_key_env?: string;
  base_url?: string;
  model_name?: string;
  enabled?: boolean;
  openai_compatible?: boolean;
  local_provider?: boolean;
}): Promise<LLMProvider> {
  return request<LLMProvider>("/api/llm/providers", { method: "POST", body: JSON.stringify(payload) });
}

export async function testLLMProvider(providerId: string, payload: { model?: string; prompt?: string }) {
  return request(`/api/llm/providers/${providerId}/test`, { method: "POST", body: JSON.stringify(payload) });
}
