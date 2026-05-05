import Link from "next/link";

import { AppShell } from "@/components/AppShell";
import { MetricCard } from "@/components/MetricCard";
import { StatusPill } from "@/components/StatusPill";
import { projects } from "@/lib/mock";

export default function HomePage() {
  return (
    <AppShell>
      <section className="grid gap-8 lg:grid-cols-[1.4fr_0.8fr]">
        <div className="rounded-lg border border-line bg-white p-8 shadow-panel">
          <StatusPill tone="green">v0.1 工程骨架</StatusPill>
          <h1 className="mt-6 max-w-3xl text-4xl font-semibold leading-tight text-ink">
            政策与市场研究解析工作台
          </h1>
          <p className="mt-4 max-w-2xl text-base leading-7 text-zinc-600">
            PolicyLens / 政研透镜面向政策研究、行业研究和市场分析流程，当前版本聚焦项目、文章、政策、模型和导出链路的工程骨架。
          </p>
          <div className="mt-7 flex flex-wrap gap-3">
            <Link href="/projects" className="rounded-md bg-pine px-4 py-2.5 text-sm font-semibold text-white shadow-sm">
              进入项目
            </Link>
            <Link href="/projects/new" className="rounded-md border border-line bg-white px-4 py-2.5 text-sm font-semibold text-ink">
              新建项目
            </Link>
          </div>
        </div>
        <div className="rounded-lg border border-line bg-ink p-6 text-white shadow-panel">
          <div className="text-sm text-zinc-300">Service readiness</div>
          <div className="mt-5 space-y-4">
            {["FastAPI /api/health", "PostgreSQL reserved", "Qdrant reserved", "Worker skeleton", "Policy export manifest"].map((item) => (
              <div key={item} className="flex items-center justify-between border-b border-white/10 pb-3 text-sm">
                <span>{item}</span>
                <span className="text-emerald-300">mock</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="mt-8 grid gap-4 md:grid-cols-3">
        <MetricCard label="研究项目" value="2" detail="Mock project records" />
        <MetricCard label="关联政策" value="25" detail="Policy library placeholders" />
        <MetricCard label="Provider 预设" value="11" detail="China, custom, and local profiles" />
      </section>

      <section className="mt-8 rounded-lg border border-line bg-white shadow-panel">
        <div className="flex items-center justify-between border-b border-line px-5 py-4">
          <h2 className="text-lg font-semibold text-ink">近期项目</h2>
          <Link href="/projects" className="text-sm font-medium text-pine">查看全部</Link>
        </div>
        <div className="divide-y divide-line">
          {projects.map((project) => (
            <Link key={project.id} href={`/projects/${project.id}`} className="grid gap-3 px-5 py-4 transition hover:bg-zinc-50 md:grid-cols-[1fr_120px_120px_120px]">
              <div>
                <div className="font-medium text-ink">{project.name}</div>
                <div className="mt-1 text-sm text-zinc-500">{project.id}</div>
              </div>
              <div className="text-sm text-zinc-600">{project.documents} 篇文章</div>
              <div className="text-sm text-zinc-600">{project.policies} 条政策</div>
              <div className="text-sm text-zinc-500">{project.updatedAt}</div>
            </Link>
          ))}
        </div>
      </section>
    </AppShell>
  );
}
