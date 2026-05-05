import Link from "next/link";

import { AppShell } from "@/components/AppShell";
import { StatusPill } from "@/components/StatusPill";
import { projects } from "@/lib/mock";

export default function ProjectsPage() {
  return (
    <AppShell>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-semibold text-ink">项目</h1>
          <p className="mt-2 text-sm text-zinc-600">Research workspaces backed by mock API contracts.</p>
        </div>
        <Link href="/projects/new" className="w-fit rounded-md bg-pine px-4 py-2.5 text-sm font-semibold text-white">
          新建项目
        </Link>
      </div>

      <div className="mt-6 overflow-hidden rounded-lg border border-line bg-white shadow-panel">
        <div className="grid grid-cols-12 border-b border-line bg-zinc-50 px-5 py-3 text-xs font-semibold uppercase text-zinc-500">
          <div className="col-span-5">Project</div>
          <div className="col-span-2">Status</div>
          <div className="col-span-2">Documents</div>
          <div className="col-span-2">Policies</div>
          <div className="col-span-1">Date</div>
        </div>
        {projects.map((project) => (
          <Link key={project.id} href={`/projects/${project.id}`} className="grid grid-cols-12 items-center border-b border-line px-5 py-4 last:border-b-0 hover:bg-zinc-50">
            <div className="col-span-5">
              <div className="font-medium text-ink">{project.name}</div>
              <div className="mt-1 text-xs text-zinc-500">{project.id}</div>
            </div>
            <div className="col-span-2">
              <StatusPill tone={project.status === "解析完成" ? "green" : "amber"}>{project.status}</StatusPill>
            </div>
            <div className="col-span-2 text-sm text-zinc-600">{project.documents}</div>
            <div className="col-span-2 text-sm text-zinc-600">{project.policies}</div>
            <div className="col-span-1 text-sm text-zinc-500">{project.updatedAt}</div>
          </Link>
        ))}
      </div>
    </AppShell>
  );
}
