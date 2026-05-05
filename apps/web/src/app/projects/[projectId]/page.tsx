import { AppShell } from "@/components/AppShell";
import { StatusPill } from "@/components/StatusPill";

const tabs = [
  "文章概览",
  "政策关联",
  "政策原文",
  "影响矩阵",
  "市场传导链",
  "事实核查",
  "图谱",
  "追问",
  "导出"
];

const panelRows = [
  ["原文事实", "上传文章中提到的产业政策信号", "doc_demo_001"],
  ["检索事实", "匹配到示例产业政策原文第二节", "policy_demo_001_section_02"],
  ["模型推理", "对供应链成本和资本开支的影响为 mock_high", "analysis_demo"]
];

export default async function ProjectWorkspacePage({
  params
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;

  return (
    <AppShell>
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-3xl font-semibold text-ink">项目工作台</h1>
            <StatusPill tone="green">mock ready</StatusPill>
          </div>
          <p className="mt-2 text-sm text-zinc-600">{projectId}</p>
        </div>
        <button className="w-fit rounded-md bg-ink px-4 py-2.5 text-sm font-semibold text-white">上传文章</button>
      </div>

      <div className="mt-6 overflow-x-auto border-b border-line">
        <div className="flex min-w-max gap-2">
          {tabs.map((tab, index) => (
            <button
              key={tab}
              className={`rounded-t-md border border-b-0 px-4 py-2.5 text-sm font-medium ${
                index === 0 ? "border-line bg-white text-ink" : "border-transparent text-zinc-500 hover:bg-white"
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      <section className="grid gap-6 rounded-b-lg rounded-tr-lg border border-t-0 border-line bg-white p-6 shadow-panel lg:grid-cols-[1.05fr_0.95fr]">
        <div>
          <h2 className="text-xl font-semibold text-ink">文章概览</h2>
          <p className="mt-3 text-sm leading-6 text-zinc-600">
            当前页面使用静态 mock 数据呈现工作台信息架构，后续由文档解析、政策检索、分析任务和导出任务填充。
          </p>
          <div className="mt-5 grid gap-3 sm:grid-cols-3">
            {[
              ["文章", "3"],
              ["政策", "18"],
              ["证据", "42"]
            ].map(([label, value]) => (
              <div key={label} className="rounded-md border border-line bg-paper p-4">
                <div className="text-xs text-zinc-500">{label}</div>
                <div className="mt-2 text-2xl font-semibold text-ink">{value}</div>
              </div>
            ))}
          </div>
        </div>
        <div className="rounded-md border border-line">
          <div className="border-b border-line px-4 py-3 text-sm font-semibold text-ink">事实边界</div>
          <div className="divide-y divide-line">
            {panelRows.map(([kind, text, source]) => (
              <div key={kind} className="px-4 py-3">
                <div className="flex items-center justify-between gap-3">
                  <span className="text-sm font-medium text-ink">{kind}</span>
                  <span className="text-xs text-zinc-500">{source}</span>
                </div>
                <p className="mt-2 text-sm text-zinc-600">{text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="mt-6 grid gap-5 lg:grid-cols-3">
        {[
          ["政策关联", "Hybrid search, rerank, vector store reserved"],
          ["影响矩阵", "Policy axis x market axis with evidence IDs"],
          ["导出", "Original policy bundle and report export queue"]
        ].map(([title, detail]) => (
          <div key={title} className="rounded-lg border border-line bg-white p-5 shadow-panel">
            <h3 className="font-semibold text-ink">{title}</h3>
            <p className="mt-2 text-sm leading-6 text-zinc-600">{detail}</p>
          </div>
        ))}
      </section>
    </AppShell>
  );
}
