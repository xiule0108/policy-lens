import Link from "next/link";

import { AppShell } from "@/components/AppShell";
import { MetricCard } from "@/components/MetricCard";
import { StatusPill } from "@/components/StatusPill";

export default function HomePage() {
  return (
    <AppShell>
      <section className="grid gap-8 lg:grid-cols-[1.4fr_0.8fr]">
        <div className="rounded-lg border border-line bg-white p-8 shadow-panel">
          <StatusPill tone="green">v0.1.0-alpha</StatusPill>
          <h1 className="mt-6 max-w-3xl text-4xl font-semibold leading-tight text-ink">
            政策与市场研究解析工作台
          </h1>
          <p className="mt-4 max-w-2xl text-base leading-7 text-zinc-600">
            PolicyLens / 政研透镜已经打通上传、解析、政策入库、Research Plan、证据链、影响矩阵、Markdown 报告和导出 bundle 的本地最小闭环。
          </p>
          <div className="mt-7 flex flex-wrap gap-3">
            <Link href="/projects" className="rounded-md bg-pine px-4 py-2.5 text-sm font-semibold text-white shadow-sm">
              进入项目
            </Link>
            <Link href="/projects/new" className="rounded-md border border-line bg-white px-4 py-2.5 text-sm font-semibold text-ink">
              新建项目
            </Link>
            <Link href="/policy-library" className="rounded-md border border-line bg-white px-4 py-2.5 text-sm font-semibold text-ink">
              查看政策库
            </Link>
          </div>
        </div>
        <div className="rounded-lg border border-line bg-ink p-6 text-white shadow-panel">
          <div className="text-sm text-zinc-300">v0.1 release readiness</div>
          <div className="mt-5 space-y-4">
            {[
              ["Workbench", "API-backed"],
              ["Research Plan", "deterministic"],
              ["Evidence", "traceable"],
              ["Exports", "ZIP + checksum"],
              ["Provider Gateway", "env-key only"]
            ].map(([item, state]) => (
              <div key={item} className="flex items-center justify-between border-b border-white/10 pb-3 text-sm">
                <span>{item}</span>
                <span className="text-emerald-300">{state}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="mt-8 grid gap-4 md:grid-cols-3">
        <MetricCard label="Demo workflow" value="E2E" detail="scripts/e2e_demo.py" />
        <MetricCard label="Report export" value="ZIP" detail="Markdown / JSON / HTML" />
        <MetricCard label="Policy export" value="ZIP" detail="Manifest + sha256" />
      </section>

      <section className="mt-8 rounded-lg border border-line bg-white p-6 shadow-panel">
        <h2 className="text-lg font-semibold text-ink">当前边界</h2>
        <div className="mt-4 grid gap-3 text-sm text-zinc-600 md:grid-cols-3">
          <div className="rounded-md border border-line p-4">确定性规则草稿，需要人工复核。</div>
          <div className="rounded-md border border-line p-4">暂不包含 Qdrant、embedding、RAG 或 OCR。</div>
          <div className="rounded-md border border-line p-4">暂不导出 PPT、DOCX 或 PDF 报告。</div>
        </div>
      </section>
    </AppShell>
  );
}
