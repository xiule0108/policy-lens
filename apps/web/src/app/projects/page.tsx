"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/AppShell";
import { StatusPill } from "@/components/StatusPill";
import { apiErrorMessage, listProjects } from "@/lib/api";
import type { Project } from "@/lib/types";

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    listProjects()
      .then((items) => {
        if (mounted) setProjects(items);
      })
      .catch((err) => {
        if (mounted) setError(apiErrorMessage(err));
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, []);

  return (
    <AppShell>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-semibold text-ink">项目</h1>
          <p className="mt-2 text-sm text-zinc-600">从 FastAPI 加载真实研究项目。</p>
        </div>
        <Link href="/projects/new" className="w-fit rounded-md bg-pine px-4 py-2.5 text-sm font-semibold text-white">
          新建项目
        </Link>
      </div>

      <div className="mt-6 overflow-hidden rounded-lg border border-line bg-white shadow-panel">
        <div className="grid grid-cols-12 border-b border-line bg-zinc-50 px-5 py-3 text-xs font-semibold uppercase text-zinc-500">
          <div className="col-span-5">Project</div>
          <div className="col-span-2">Status</div>
          <div className="col-span-2">Industry</div>
          <div className="col-span-2">Jurisdiction</div>
          <div className="col-span-1">Date</div>
        </div>
        {loading ? <StateRow text="正在加载项目..." /> : null}
        {error ? <StateRow text={`API 连接失败：${error}`} tone="red" /> : null}
        {!loading && !error && projects.length === 0 ? <StateRow text="暂无项目，请新建项目。" /> : null}
        {projects.map((project) => (
          <Link
            key={project.id}
            href={`/projects/${project.id}`}
            className="grid grid-cols-12 items-center border-b border-line px-5 py-4 last:border-b-0 hover:bg-zinc-50"
          >
            <div className="col-span-5">
              <div className="font-medium text-ink">{project.name}</div>
              <div className="mt-1 text-xs text-zinc-500">{project.id}</div>
            </div>
            <div className="col-span-2">
              <StatusPill tone={project.status === "active" ? "green" : "amber"}>{project.status}</StatusPill>
            </div>
            <div className="col-span-2 text-sm text-zinc-600">{project.industry || "未设置"}</div>
            <div className="col-span-2 text-sm text-zinc-600">{project.jurisdictions.join(", ") || "未设置"}</div>
            <div className="col-span-1 text-sm text-zinc-500">{project.updated_at.slice(0, 10)}</div>
          </Link>
        ))}
      </div>
    </AppShell>
  );
}

function StateRow({ text, tone = "neutral" }: { text: string; tone?: "neutral" | "red" }) {
  return (
    <div className={`border-b border-line px-5 py-8 text-sm ${tone === "red" ? "text-red-700" : "text-zinc-500"}`}>
      {text}
    </div>
  );
}
