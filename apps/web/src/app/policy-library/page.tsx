"use client";

import { useEffect, useState } from "react";

import { AppShell } from "@/components/AppShell";
import { StatusPill } from "@/components/StatusPill";
import { apiErrorMessage, createPolicyOriginalExport, downloadExportUrl, getPolicyOriginal, getPolicySections, listPolicies, searchPolicies } from "@/lib/api";
import type { Policy, PolicyOriginal, PolicySection } from "@/lib/types";

export default function PolicyLibraryPage() {
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [query, setQuery] = useState("");
  const [selectedPolicy, setSelectedPolicy] = useState<PolicyOriginal | null>(null);
  const [sections, setSections] = useState<PolicySection[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadPolicies() {
    setError(null);
    const items = query ? await searchPolicies({ query, limit: 20 }) : await listPolicies();
    setPolicies(items);
  }

  useEffect(() => {
    let mounted = true;
    loadPolicies()
      .catch((err) => mounted && setError(apiErrorMessage(err)))
      .finally(() => mounted && setLoading(false));
    return () => {
      mounted = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function inspectPolicy(policyId: string) {
    setError(null);
    try {
      const [original, sectionPayload] = await Promise.all([getPolicyOriginal(policyId), getPolicySections(policyId)]);
      setSelectedPolicy(original);
      setSections(sectionPayload.items);
    } catch (err) {
      setError(apiErrorMessage(err));
    }
  }

  async function exportPolicy(policyId: string) {
    setError(null);
    try {
      const created = await createPolicyOriginalExport({
        policy_ids: [policyId],
        mode: "single_policy_full_text",
        formats: ["markdown", "json"]
      });
      window.open(downloadExportUrl(created.export_id), "_blank");
    } catch (err) {
      setError(apiErrorMessage(err));
    }
  }

  return (
    <AppShell>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-semibold text-ink">政策库</h1>
          <p className="mt-2 text-sm text-zinc-600">从数据库读取政策、原文和条款，并支持政策原文包导出。</p>
        </div>
        <form
          onSubmit={(event) => {
            event.preventDefault();
            setLoading(true);
            loadPolicies().catch((err) => setError(apiErrorMessage(err))).finally(() => setLoading(false));
          }}
          className="flex gap-2"
        >
          <input value={query} onChange={(event) => setQuery(event.target.value)} className="rounded-md border border-line px-3 py-2 text-sm" placeholder="搜索政策" />
          <button className="rounded-md border border-line bg-white px-4 py-2 text-sm font-semibold text-ink">检索</button>
        </form>
      </div>

      {loading ? <Notice text="正在加载政策库..." /> : null}
      {error ? <Notice text={error} tone="red" /> : null}

      <div className="mt-6 grid gap-4 lg:grid-cols-[1fr_0.8fr]">
        <div className="grid gap-4">
          {!loading && policies.length === 0 ? <Notice text="暂无政策，请先在项目工作台入库 policy 文档。" /> : null}
          {policies.map((policy) => (
            <article key={policy.id} className="rounded-lg border border-line bg-white p-5 shadow-panel">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <h2 className="text-lg font-semibold text-ink">{policy.title}</h2>
                  <p className="mt-2 text-sm text-zinc-600">{policy.issuer || "未知发文方"} · {policy.jurisdiction || "未知地区"} · {policy.policy_type || "未分类"}</p>
                </div>
                <StatusPill>{policy.status}</StatusPill>
              </div>
              <div className="mt-4 grid gap-3 text-sm text-zinc-600 sm:grid-cols-3">
                <div>Policy ID: {policy.id}</div>
                <div>sha256: {policy.sha256 || "none"}</div>
                <div>{policy.created_at.slice(0, 10)}</div>
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                <button onClick={() => inspectPolicy(policy.id)} className="rounded-md border border-line px-3 py-1.5 text-xs font-semibold text-ink">查看原文</button>
                <button onClick={() => exportPolicy(policy.id)} className="rounded-md bg-pine px-3 py-1.5 text-xs font-semibold text-white">导出政策原文</button>
              </div>
            </article>
          ))}
        </div>
        <aside className="rounded-lg border border-line bg-white p-5 shadow-panel">
          <h2 className="font-semibold text-ink">原文与条款</h2>
          {selectedPolicy ? (
            <>
              <div className="mt-3 text-sm font-medium text-ink">{selectedPolicy.title}</div>
              <pre className="mt-3 max-h-56 overflow-auto rounded-md border border-line bg-paper p-3 text-xs text-zinc-700">{selectedPolicy.normalized_text}</pre>
              <div className="mt-4 space-y-2">
                {sections.slice(0, 8).map((section) => (
                  <div key={section.id} className="rounded-md border border-line p-3 text-xs text-zinc-600">
                    <div className="font-medium text-ink">{section.heading || section.section_path || `Section ${section.order_index}`}</div>
                    <div className="mt-1 line-clamp-3">{section.content}</div>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <p className="mt-3 text-sm text-zinc-500">选择一条政策查看原文。</p>
          )}
        </aside>
      </div>
    </AppShell>
  );
}

function Notice({ text, tone = "neutral" }: { text: string; tone?: "neutral" | "red" }) {
  return (
    <div className={`mt-4 rounded-md border px-4 py-3 text-sm ${tone === "red" ? "border-red-200 bg-red-50 text-red-700" : "border-line bg-white text-zinc-600"}`}>
      {text}
    </div>
  );
}
