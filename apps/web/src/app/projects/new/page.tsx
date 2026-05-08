"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { AppShell } from "@/components/AppShell";
import { apiErrorMessage, createProject } from "@/lib/api";

export default function NewProjectPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [industry, setIndustry] = useState("");
  const [jurisdictions, setJurisdictions] = useState("China");
  const [modelProfile, setModelProfile] = useState("china_balanced");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const project = await createProject({
        name,
        description,
        industry,
        jurisdictions: jurisdictions.split(",").map((item) => item.trim()).filter(Boolean),
        default_model_profile: modelProfile
      });
      router.push(`/projects/${project.id}`);
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AppShell>
      <div className="max-w-3xl">
        <h1 className="text-3xl font-semibold text-ink">新建项目</h1>
        <form onSubmit={handleSubmit} className="mt-6 space-y-5 rounded-lg border border-line bg-white p-6 shadow-panel">
          {error ? <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div> : null}
          <label className="block">
            <span className="text-sm font-medium text-zinc-700">项目名称</span>
            <input value={name} onChange={(event) => setName(event.target.value)} required className="mt-2 w-full rounded-md border border-line px-3 py-2.5 outline-none ring-pine/20 focus:ring-4" placeholder="例如 新能源产业政策影响研究" />
          </label>
          <label className="block">
            <span className="text-sm font-medium text-zinc-700">研究说明</span>
            <textarea value={description} onChange={(event) => setDescription(event.target.value)} className="mt-2 min-h-32 w-full rounded-md border border-line px-3 py-2.5 outline-none ring-pine/20 focus:ring-4" placeholder="研究对象、区域、行业和输出目标" />
          </label>
          <div className="grid gap-4 sm:grid-cols-3">
            <label className="block">
              <span className="text-sm font-medium text-zinc-700">地区</span>
              <input value={jurisdictions} onChange={(event) => setJurisdictions(event.target.value)} className="mt-2 w-full rounded-md border border-line px-3 py-2.5 outline-none ring-pine/20 focus:ring-4" placeholder="China, EU, US" />
            </label>
            <label className="block">
              <span className="text-sm font-medium text-zinc-700">行业</span>
              <input value={industry} onChange={(event) => setIndustry(event.target.value)} className="mt-2 w-full rounded-md border border-line px-3 py-2.5 outline-none ring-pine/20 focus:ring-4" placeholder="energy, manufacturing" />
            </label>
            <label className="block">
              <span className="text-sm font-medium text-zinc-700">默认模型 Profile</span>
              <input value={modelProfile} onChange={(event) => setModelProfile(event.target.value)} className="mt-2 w-full rounded-md border border-line px-3 py-2.5 outline-none ring-pine/20 focus:ring-4" />
            </label>
          </div>
          <div className="flex flex-wrap gap-3 pt-2">
            <button type="submit" disabled={submitting || !name} className="rounded-md bg-pine px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50">
              {submitting ? "创建中..." : "创建项目"}
            </button>
            <Link href="/projects" className="rounded-md border border-line px-4 py-2.5 text-sm font-semibold text-ink">
              返回列表
            </Link>
          </div>
        </form>
      </div>
    </AppShell>
  );
}
