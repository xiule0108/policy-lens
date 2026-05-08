"use client";

import { FormEvent, useEffect, useState } from "react";

import { AppShell } from "@/components/AppShell";
import { StatusPill } from "@/components/StatusPill";
import { apiErrorMessage, listLLMProviders, testLLMProvider, upsertLLMProvider } from "@/lib/api";
import type { LLMProvider } from "@/lib/types";

export default function ModelSettingsPage() {
  const [providers, setProviders] = useState<LLMProvider[]>([]);
  const [form, setForm] = useState({
    provider_id: "openai_compatible_custom",
    display_name: "OpenAI-compatible Custom Provider",
    provider_family: "custom",
    base_url: "",
    api_key_env: "CUSTOM_LLM_API_KEY",
    model_name: "",
    enabled: false,
    openai_compatible: true,
    local_provider: false
  });
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    setProviders(await listLLMProviders());
  }

  useEffect(() => {
    let mounted = true;
    refresh()
      .catch((err) => mounted && setError(apiErrorMessage(err)))
      .finally(() => mounted && setLoading(false));
    return () => {
      mounted = false;
    };
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setMessage(null);
    try {
      await upsertLLMProvider(form);
      await refresh();
      setMessage("Provider 已保存。API Key 只会从服务端环境变量读取。");
    } catch (err) {
      setError(apiErrorMessage(err));
    }
  }

  async function handleTest(provider: LLMProvider) {
    setError(null);
    setMessage(null);
    try {
      const result = await testLLMProvider(provider.id, { model: provider.model_name || undefined });
      setMessage(JSON.stringify(result));
    } catch (err) {
      setError(apiErrorMessage(err));
    }
  }

  return (
    <AppShell>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-semibold text-ink">模型设置</h1>
          <p className="mt-2 text-sm text-zinc-600">只配置环境变量名，不在前端输入或保存真实 API Key。</p>
        </div>
      </div>

      {loading ? <Notice text="正在加载 Provider..." /> : null}
      {message ? <Notice text={message} /> : null}
      {error ? <Notice text={error} tone="red" /> : null}

      <section className="mt-6 grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
        <form onSubmit={handleSubmit} className="space-y-4 rounded-lg border border-line bg-white p-5 shadow-panel">
          <h2 className="font-semibold text-ink">新增或更新 Provider</h2>
          <Field label="Provider ID" value={form.provider_id} onChange={(value) => setForm({ ...form, provider_id: value })} />
          <Field label="展示名" value={form.display_name} onChange={(value) => setForm({ ...form, display_name: value })} />
          <Field label="Provider family" value={form.provider_family} onChange={(value) => setForm({ ...form, provider_family: value })} />
          <Field label="Base URL" value={form.base_url} onChange={(value) => setForm({ ...form, base_url: value })} />
          <Field label="API Key env name" value={form.api_key_env} onChange={(value) => setForm({ ...form, api_key_env: value })} />
          <Field label="Model name" value={form.model_name} onChange={(value) => setForm({ ...form, model_name: value })} />
          <div className="grid gap-3 text-sm sm:grid-cols-3">
            <label className="flex items-center gap-2"><input type="checkbox" checked={form.enabled} onChange={(event) => setForm({ ...form, enabled: event.target.checked })} /> Enabled</label>
            <label className="flex items-center gap-2"><input type="checkbox" checked={form.openai_compatible} onChange={(event) => setForm({ ...form, openai_compatible: event.target.checked })} /> OpenAI-compatible</label>
            <label className="flex items-center gap-2"><input type="checkbox" checked={form.local_provider} onChange={(event) => setForm({ ...form, local_provider: event.target.checked })} /> Local</label>
          </div>
          <button className="rounded-md bg-pine px-4 py-2 text-sm font-semibold text-white">保存 Provider</button>
        </form>

        <div className="grid gap-4">
          {providers.map((provider) => (
            <article key={provider.id} className="rounded-lg border border-line bg-white p-5 shadow-panel">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h2 className="font-semibold text-ink">{provider.display_name}</h2>
                  <p className="mt-2 text-sm text-zinc-600">{provider.id} · {provider.provider_family}</p>
                </div>
                <StatusPill tone={provider.api_key_configured || provider.local_provider ? "green" : "amber"}>
                  {provider.local_provider ? "local" : provider.api_key_configured ? "configured" : "missing env"}
                </StatusPill>
              </div>
              <div className="mt-4 grid gap-2 text-xs text-zinc-600 sm:grid-cols-2">
                <div>api_key_env: {provider.api_key_env || "none"}</div>
                <div>base_url: {provider.base_url || "未设置"}</div>
                <div>model_name: {provider.model_name || "用户配置"}</div>
                <div>enabled: {provider.enabled ? "true" : "false"}</div>
              </div>
              <button onClick={() => handleTest(provider)} className="mt-4 rounded-md border border-line px-3 py-1.5 text-xs font-semibold text-ink">
                Test Provider
              </button>
            </article>
          ))}
        </div>
      </section>
    </AppShell>
  );
}

function Field({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return (
    <label className="block">
      <span className="text-sm font-medium text-zinc-700">{label}</span>
      <input value={value} onChange={(event) => onChange(event.target.value)} className="mt-2 w-full rounded-md border border-line px-3 py-2 text-sm outline-none ring-pine/20 focus:ring-4" />
    </label>
  );
}

function Notice({ text, tone = "neutral" }: { text: string; tone?: "neutral" | "red" }) {
  return (
    <div className={`mt-4 rounded-md border px-4 py-3 text-sm ${tone === "red" ? "border-red-200 bg-red-50 text-red-700" : "border-line bg-white text-zinc-600"}`}>
      {text}
    </div>
  );
}
