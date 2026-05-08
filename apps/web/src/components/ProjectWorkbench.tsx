"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

import { StatusPill } from "@/components/StatusPill";
import {
  apiErrorMessage,
  createAnalysisJob,
  createPolicyOriginalExport,
  createReportExport,
  downloadExportUrl,
  getAnalysisClaims,
  getAnalysisEvidence,
  getAnalysisImpactMatrix,
  getAnalysisPlan,
  getAnalysisPolicyMatches,
  getAnalysisReport,
  getAnalysisResult,
  getAnalysisSteps,
  getExport,
  getProject,
  ingestPolicyFromDocument,
  listAnalysisJobs,
  listDocuments,
  listLLMProviders,
  listPolicies,
  parseDocument,
  uploadDocument
} from "@/lib/api";
import type {
  AnalysisClaim,
  AnalysisJob,
  AnalysisReport,
  AnalysisResult,
  AnalysisStep,
  DocumentRecord,
  DocumentRole,
  ExportRecord,
  ImpactItem,
  LLMProvider,
  Policy,
  PolicyMatch,
  Project
} from "@/lib/types";

const tabs = ["文章概览", "政策关联", "证据链", "影响矩阵", "报告", "导出", "设置/模型"];

type AnalysisBundle = {
  steps: AnalysisStep[];
  plan: Record<string, unknown> | null;
  result: AnalysisResult | null;
  claims: AnalysisClaim[];
  matches: PolicyMatch[];
  evidence: { claim_policy_map: Array<Record<string, unknown>>; fact_boundaries: Record<string, unknown> } | null;
  impact: ImpactItem[];
  report: AnalysisReport | null;
};

export function ProjectWorkbench({ projectId }: { projectId: string }) {
  const [project, setProject] = useState<Project | null>(null);
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [jobs, setJobs] = useState<AnalysisJob[]>([]);
  const [providers, setProviders] = useState<LLMProvider[]>([]);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState(tabs[0]);
  const [analysis, setAnalysis] = useState<AnalysisBundle>(emptyAnalysis());
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lastExport, setLastExport] = useState<ExportRecord | null>(null);

  const latestJob = jobs[0];
  const researchDocuments = documents.filter((document) => document.document_role === "research_article");
  const policyDocuments = documents.filter((document) => document.document_role === "policy");
  const relatedPolicyIds = useMemo(() => {
    const fromResult = analysis.result?.related_policies ?? [];
    return Array.from(new Set(fromResult.map((item) => String(item.policy_id || item.id || "")).filter(Boolean)));
  }, [analysis.result]);
  const exportPolicyIds = relatedPolicyIds.length ? relatedPolicyIds : policies.map((policy) => policy.id);

  async function refreshWorkspace() {
    setError(null);
    const [projectData, documentItems, policyItems, jobItems, providerItems] = await Promise.all([
      getProject(projectId),
      listDocuments(projectId),
      listPolicies(),
      listAnalysisJobs(projectId),
      listLLMProviders()
    ]);
    setProject(projectData);
    setDocuments(documentItems);
    setPolicies(policyItems);
    setJobs(jobItems);
    setProviders(providerItems);
    const nextJobId = activeJobId || jobItems[0]?.id || null;
    setActiveJobId(nextJobId);
    if (nextJobId) {
      await loadAnalysis(nextJobId);
    }
  }

  async function loadAnalysis(jobId: string) {
    setError(null);
    try {
      const [steps, plan, result, claims, matches, evidence, impact, report] = await Promise.all([
        getAnalysisSteps(jobId),
        getAnalysisPlan(jobId),
        getAnalysisResult(jobId),
        getAnalysisClaims(jobId),
        getAnalysisPolicyMatches(jobId),
        getAnalysisEvidence(jobId),
        getAnalysisImpactMatrix(jobId),
        getAnalysisReport(jobId)
      ]);
      setAnalysis({ steps, plan, result, claims, matches, evidence, impact, report });
    } catch (err) {
      setAnalysis(emptyAnalysis());
      setError(apiErrorMessage(err));
    }
  }

  useEffect(() => {
    let mounted = true;
    refreshWorkspace()
      .catch((err) => {
        if (mounted) setError(apiErrorMessage(err));
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });
    return () => {
      mounted = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  async function runAction(label: string, action: () => Promise<void>) {
    setBusy(label);
    setError(null);
    try {
      await action();
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setBusy(null);
    }
  }

  async function handleUpload(payload: { role: DocumentRole; title: string; file: File | null }) {
    if (!payload.file) return;
    const uploadFile = payload.file;
    await runAction("upload", async () => {
      await uploadDocument({ projectId, documentRole: payload.role, title: payload.title, file: uploadFile });
      await refreshWorkspace();
    });
  }

  async function handleParse(documentId: string) {
    await runAction("parse", async () => {
      await parseDocument(documentId);
      await refreshWorkspace();
    });
  }

  async function handleIngest(document: DocumentRecord) {
    await runAction("ingest", async () => {
      await ingestPolicyFromDocument({
        document_id: document.id,
        title: document.title || document.file_name,
        jurisdiction: "China",
        policy_type: "notice",
        status: "active"
      });
      await refreshWorkspace();
    });
  }

  async function handleRunAnalysis(documentId: string) {
    await runAction("analysis", async () => {
      const job = await createAnalysisJob({
        project_id: projectId,
        document_ids: [documentId],
        analysis_types: ["policy_deep_dive"],
        model_profile: project?.default_model_profile || "china_balanced"
      });
      setActiveJobId(job.id);
      await refreshWorkspace();
      await loadAnalysis(job.id);
      setActiveTab("报告");
    });
  }

  async function handleReportExport() {
    if (!activeJobId) return;
    await runAction("report-export", async () => {
      const created = await createReportExport({
        job_id: activeJobId,
        formats: ["markdown", "json", "html"],
        include_evidence_bundle: true,
        include_impact_matrix: true,
        include_policy_matches: true
      });
      const detail = await getExport(created.export_id);
      setLastExport(detail);
      window.open(downloadExportUrl(created.export_id), "_blank");
    });
  }

  async function handlePolicyExport() {
    const policyIds = relatedPolicyIds.length ? relatedPolicyIds : policies.slice(0, 5).map((policy) => policy.id);
    if (!policyIds.length) return;
    await runAction("policy-export", async () => {
      const created = await createPolicyOriginalExport({
        project_id: projectId,
        policy_ids: policyIds,
        mode: "related_policy_bundle",
        formats: ["markdown", "json"]
      });
      const detail = await getExport(created.export_id);
      setLastExport(detail);
      window.open(downloadExportUrl(created.export_id), "_blank");
    });
  }

  return (
    <>
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-3xl font-semibold text-ink">{project?.name || "项目工作台"}</h1>
            <StatusPill tone={latestJob?.status === "completed" ? "green" : "amber"}>{latestJob?.status || "ready"}</StatusPill>
          </div>
          <p className="mt-2 text-sm text-zinc-600">{projectId}</p>
        </div>
        <div className="grid gap-2 text-sm text-zinc-600 sm:grid-cols-3">
          <Metric label="文档" value={documents.length} />
          <Metric label="政策" value={policies.length} />
          <Metric label="分析" value={jobs.length} />
        </div>
      </div>

      {loading ? <Notice text="正在加载工作台..." /> : null}
      {error ? <Notice text={error} tone="red" /> : null}
      {busy ? <Notice text={`处理中：${busy}`} /> : null}

      <section className="mt-6 grid gap-4 lg:grid-cols-[1fr_1fr]">
        <UploadPanel onUpload={handleUpload} />
        <AnalysisLauncher documents={researchDocuments} jobs={jobs} activeJobId={activeJobId} onRun={handleRunAnalysis} onSelect={loadAnalysisAndSet} />
      </section>

      <div className="mt-6 overflow-x-auto border-b border-line">
        <div className="flex min-w-max gap-2">
          {tabs.map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`rounded-t-md border border-b-0 px-4 py-2.5 text-sm font-medium ${
                activeTab === tab ? "border-line bg-white text-ink" : "border-transparent text-zinc-500 hover:bg-white"
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      <section className="rounded-b-lg rounded-tr-lg border border-t-0 border-line bg-white p-6 shadow-panel">
        {activeTab === "文章概览" ? (
          <OverviewTab documents={documents} jobs={jobs} steps={analysis.steps} plan={analysis.plan} result={analysis.result} onParse={handleParse} />
        ) : null}
        {activeTab === "政策关联" ? (
          <PolicyTab policies={policies} documents={policyDocuments} matches={analysis.matches} relatedPolicies={analysis.result?.related_policies ?? []} onIngest={handleIngest} />
        ) : null}
        {activeTab === "证据链" ? <EvidenceTab claims={analysis.claims} evidence={analysis.evidence} /> : null}
        {activeTab === "影响矩阵" ? <ImpactTab items={analysis.impact} /> : null}
        {activeTab === "报告" ? <ReportTab report={analysis.report} /> : null}
        {activeTab === "导出" ? (
          <ExportTab
            activeJobId={activeJobId}
            policyIds={exportPolicyIds}
            lastExport={lastExport}
            onReportExport={handleReportExport}
            onPolicyExport={handlePolicyExport}
          />
        ) : null}
        {activeTab === "设置/模型" ? <ProviderTab providers={providers} /> : null}
      </section>
    </>
  );

  async function loadAnalysisAndSet(jobId: string) {
    setActiveJobId(jobId);
    await loadAnalysis(jobId);
  }
}

function UploadPanel({ onUpload }: { onUpload: (payload: { role: DocumentRole; title: string; file: File | null }) => void }) {
  const [role, setRole] = useState<DocumentRole>("research_article");
  const [title, setTitle] = useState("");
  const [file, setFile] = useState<File | null>(null);
  return (
    <form
      onSubmit={(event: FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        onUpload({ role, title, file });
      }}
      className="rounded-lg border border-line bg-white p-5 shadow-panel"
    >
      <h2 className="font-semibold text-ink">上传文档</h2>
      <div className="mt-4 grid gap-3 sm:grid-cols-[160px_1fr]">
        <select value={role} onChange={(event) => setRole(event.target.value as DocumentRole)} className="rounded-md border border-line px-3 py-2 text-sm">
          <option value="research_article">研究文章</option>
          <option value="policy">政策文件</option>
          <option value="appendix">附件</option>
        </select>
        <input value={title} onChange={(event) => setTitle(event.target.value)} className="rounded-md border border-line px-3 py-2 text-sm" placeholder="标题，可选" />
      </div>
      <input onChange={(event) => setFile(event.target.files?.[0] ?? null)} type="file" className="mt-3 block w-full text-sm text-zinc-600" />
      <button className="mt-4 rounded-md bg-pine px-4 py-2 text-sm font-semibold text-white disabled:opacity-50" disabled={!file}>
        上传
      </button>
    </form>
  );
}

function AnalysisLauncher({
  documents,
  jobs,
  activeJobId,
  onRun,
  onSelect
}: {
  documents: DocumentRecord[];
  jobs: AnalysisJob[];
  activeJobId: string | null;
  onRun: (documentId: string) => void;
  onSelect: (jobId: string) => void;
}) {
  const [documentId, setDocumentId] = useState("");
  useEffect(() => {
    if (!documentId && documents[0]) setDocumentId(documents[0].id);
  }, [documents, documentId]);
  return (
    <div className="rounded-lg border border-line bg-white p-5 shadow-panel">
      <h2 className="font-semibold text-ink">运行分析</h2>
      <div className="mt-4 flex flex-wrap gap-3">
        <select value={documentId} onChange={(event) => setDocumentId(event.target.value)} className="min-w-64 rounded-md border border-line px-3 py-2 text-sm">
          <option value="">选择研究文章</option>
          {documents.map((document) => (
            <option key={document.id} value={document.id}>
              {document.title || document.file_name}
            </option>
          ))}
        </select>
        <button onClick={() => documentId && onRun(documentId)} disabled={!documentId} className="rounded-md bg-ink px-4 py-2 text-sm font-semibold text-white disabled:opacity-50">
          Run Analysis
        </button>
      </div>
      <div className="mt-4">
        <div className="text-xs font-semibold uppercase text-zinc-500">历史分析</div>
        <div className="mt-2 flex flex-wrap gap-2">
          {jobs.length === 0 ? <span className="text-sm text-zinc-500">暂无分析任务</span> : null}
          {jobs.map((job) => (
            <button key={job.id} onClick={() => onSelect(job.id)} className={`rounded-md border px-3 py-1.5 text-xs ${activeJobId === job.id ? "border-pine bg-emerald-50 text-pine" : "border-line text-zinc-600"}`}>
              {job.status} · {job.created_at.slice(0, 10)}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

function OverviewTab({
  documents,
  jobs,
  steps,
  plan,
  result,
  onParse
}: {
  documents: DocumentRecord[];
  jobs: AnalysisJob[];
  steps: AnalysisStep[];
  plan: Record<string, unknown> | null;
  result: AnalysisResult | null;
  onParse: (documentId: string) => void;
}) {
  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_0.8fr]">
      <div>
        <h2 className="text-xl font-semibold text-ink">文档列表</h2>
        <div className="mt-4 divide-y divide-line rounded-md border border-line">
          {documents.length === 0 ? <Empty text="暂无文档，请先上传研究文章或政策文件。" /> : null}
          {documents.map((document) => (
            <div key={document.id} className="grid gap-3 p-4 text-sm md:grid-cols-[1fr_120px_110px_90px]">
              <div>
                <div className="font-medium text-ink">{document.title || document.file_name}</div>
                <div className="mt-1 text-xs text-zinc-500">{document.sha256 || "no sha256"}</div>
              </div>
              <span>{document.document_role}</span>
              <StatusPill tone={document.parse_status === "parsed" ? "green" : "amber"}>{document.parse_status}</StatusPill>
              <button onClick={() => onParse(document.id)} className="rounded-md border border-line px-3 py-1.5 text-xs font-semibold text-ink">
                Parse
              </button>
            </div>
          ))}
        </div>
      </div>
      <div>
        <h2 className="text-xl font-semibold text-ink">分析概览</h2>
        <div className="mt-4 grid gap-3">
          <div className="rounded-md border border-line p-4 text-sm">
            <div className="font-medium text-ink">任务</div>
            <div className="mt-1 text-zinc-600">{jobs.length} 个分析任务，当前 result：{result?.id || "暂无"}</div>
          </div>
          <div className="rounded-md border border-line p-4">
            <div className="text-sm font-medium text-ink">执行步骤</div>
            <div className="mt-3 space-y-2">
              {steps.length === 0 ? <div className="text-sm text-zinc-500">暂无 steps。</div> : null}
              {steps.map((step) => (
                <div key={step.id} className="flex items-center justify-between gap-3 rounded-md bg-paper px-3 py-2 text-xs">
                  <span className="font-medium text-ink">{step.step_id}</span>
                  <span className="text-zinc-500">{step.status}</span>
                </div>
              ))}
            </div>
          </div>
          <details className="rounded-md border border-line p-4">
            <summary className="cursor-pointer text-sm font-medium text-ink">Research Plan / Result JSON</summary>
            <pre className="mt-3 max-h-96 overflow-auto rounded-md bg-paper p-4 text-xs text-zinc-700">
              {JSON.stringify({ plan: plan || {}, summary: result?.summary || {}, result_id: result?.id || null }, null, 2)}
            </pre>
          </details>
        </div>
      </div>
    </div>
  );
}

function PolicyTab({
  policies,
  documents,
  matches,
  relatedPolicies,
  onIngest
}: {
  policies: Policy[];
  documents: DocumentRecord[];
  matches: PolicyMatch[];
  relatedPolicies: Array<Record<string, unknown>>;
  onIngest: (document: DocumentRecord) => void;
}) {
  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <div>
        <h2 className="text-xl font-semibold text-ink">政策文档入库</h2>
        <div className="mt-4 space-y-3">
          {documents.length === 0 ? <Empty text="暂无 policy 文档。" /> : null}
          {documents.map((document) => (
            <div key={document.id} className="rounded-md border border-line p-4 text-sm">
              <div className="font-medium text-ink">{document.title || document.file_name}</div>
              <div className="mt-1 text-zinc-500">{document.parse_status}</div>
              <button onClick={() => onIngest(document)} disabled={document.parse_status !== "parsed"} className="mt-3 rounded-md bg-pine px-3 py-1.5 text-xs font-semibold text-white disabled:opacity-50">
                Ingest as Policy
              </button>
            </div>
          ))}
        </div>
      </div>
      <div>
        <h2 className="text-xl font-semibold text-ink">政策关联</h2>
        <div className="mt-4 space-y-3 text-sm">
          <div className="rounded-md border border-line p-4">政策库记录：{policies.length}</div>
          <div className="rounded-md border border-line p-4">候选政策：{relatedPolicies.length}</div>
          <div className="rounded-md border border-line p-4">Section matches：{matches.length}</div>
        </div>
      </div>
    </div>
  );
}

function EvidenceTab({ claims, evidence }: { claims: AnalysisClaim[]; evidence: AnalysisBundle["evidence"] }) {
  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <div>
        <h2 className="text-xl font-semibold text-ink">Claims</h2>
        <div className="mt-4 space-y-3">
          {claims.length === 0 ? <Empty text="暂无 claims。" /> : null}
          {claims.map((claim) => (
            <div key={claim.id} className="rounded-md border border-line p-4 text-sm">
              <div className="font-medium text-ink">{claim.claim_text}</div>
              <div className="mt-2 text-xs text-zinc-500">{claim.claim_type} · {claim.source_chunk_ids.join(", ")}</div>
            </div>
          ))}
        </div>
      </div>
      <div>
        <h2 className="text-xl font-semibold text-ink">Evidence Map</h2>
        <pre className="mt-4 max-h-[32rem] overflow-auto rounded-md border border-line bg-paper p-4 text-xs text-zinc-700">
          {JSON.stringify(evidence || {}, null, 2)}
        </pre>
      </div>
    </div>
  );
}

function ImpactTab({ items }: { items: ImpactItem[] }) {
  return (
    <div>
      <h2 className="text-xl font-semibold text-ink">政策影响矩阵</h2>
      <div className="mt-4 overflow-x-auto rounded-md border border-line">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-zinc-50 text-xs uppercase text-zinc-500">
            <tr>
              {["主体", "方向", "周期", "机制", "市场变量", "置信度", "说明"].map((heading) => (
                <th key={heading} className="px-3 py-2">{heading}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {items.length === 0 ? (
              <tr><td className="px-3 py-6 text-zinc-500" colSpan={7}>暂无影响矩阵。</td></tr>
            ) : null}
            {items.map((item) => (
              <tr key={item.id}>
                <td className="px-3 py-3">{item.impact_subject}</td>
                <td className="px-3 py-3">{item.impact_direction}</td>
                <td className="px-3 py-3">{item.impact_horizon}</td>
                <td className="px-3 py-3">{item.impact_mechanism}</td>
                <td className="px-3 py-3">{item.market_variable}</td>
                <td className="px-3 py-3">{item.confidence}</td>
                <td className="max-w-xl px-3 py-3 text-zinc-600">{item.analysis_text}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ReportTab({ report }: { report: AnalysisReport | null }) {
  return (
    <div>
      <h2 className="text-xl font-semibold text-ink">Markdown 报告</h2>
      <pre className="mt-4 max-h-[42rem] whitespace-pre-wrap overflow-auto rounded-md border border-line bg-paper p-5 text-sm leading-6 text-zinc-800">
        {report?.report_markdown || "暂无报告。请先运行分析任务。"}
      </pre>
    </div>
  );
}

function ExportTab({
  activeJobId,
  policyIds,
  lastExport,
  onReportExport,
  onPolicyExport
}: {
  activeJobId: string | null;
  policyIds: string[];
  lastExport: ExportRecord | null;
  onReportExport: () => void;
  onPolicyExport: () => void;
}) {
  return (
    <div>
      <h2 className="text-xl font-semibold text-ink">导出</h2>
      <div className="mt-4 flex flex-wrap gap-3">
        <button onClick={onReportExport} disabled={!activeJobId} className="rounded-md bg-pine px-4 py-2 text-sm font-semibold text-white disabled:opacity-50">
          Export Report Bundle
        </button>
        <button onClick={onPolicyExport} disabled={policyIds.length === 0} className="rounded-md border border-line px-4 py-2 text-sm font-semibold text-ink disabled:opacity-50">
          Export Policy Original Bundle
        </button>
        {lastExport ? (
          <a href={downloadExportUrl(lastExport.export_id)} target="_blank" className="rounded-md border border-line px-4 py-2 text-sm font-semibold text-ink">
            Download Export
          </a>
        ) : null}
      </div>
      <pre className="mt-4 max-h-80 overflow-auto rounded-md border border-line bg-paper p-4 text-xs">
        {JSON.stringify(lastExport || {}, null, 2)}
      </pre>
    </div>
  );
}

function ProviderTab({ providers }: { providers: LLMProvider[] }) {
  return (
    <div>
      <h2 className="text-xl font-semibold text-ink">模型 Provider</h2>
      <div className="mt-4 grid gap-3 lg:grid-cols-2">
        {providers.map((provider) => (
          <div key={provider.id} className="rounded-md border border-line p-4 text-sm">
            <div className="font-medium text-ink">{provider.display_name}</div>
            <div className="mt-2 text-zinc-600">{provider.id} · {provider.api_key_env || "no env"} · {provider.api_key_configured ? "configured" : "not configured"}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-md border border-line bg-white px-4 py-3">
      <div className="text-xs text-zinc-500">{label}</div>
      <div className="text-xl font-semibold text-ink">{value}</div>
    </div>
  );
}

function Notice({ text, tone = "neutral" }: { text: string; tone?: "neutral" | "red" }) {
  return (
    <div className={`mt-4 rounded-md border px-4 py-3 text-sm ${tone === "red" ? "border-red-200 bg-red-50 text-red-700" : "border-line bg-white text-zinc-600"}`}>
      {text}
    </div>
  );
}

function Empty({ text }: { text: string }) {
  return <div className="rounded-md border border-dashed border-line p-4 text-sm text-zinc-500">{text}</div>;
}

function emptyAnalysis(): AnalysisBundle {
  return {
    steps: [],
    plan: null,
    result: null,
    claims: [],
    matches: [],
    evidence: null,
    impact: [],
    report: null
  };
}
