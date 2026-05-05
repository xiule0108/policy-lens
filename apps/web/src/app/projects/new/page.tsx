import Link from "next/link";

import { AppShell } from "@/components/AppShell";

export default function NewProjectPage() {
  return (
    <AppShell>
      <div className="max-w-3xl">
        <h1 className="text-3xl font-semibold text-ink">新建项目</h1>
        <form className="mt-6 space-y-5 rounded-lg border border-line bg-white p-6 shadow-panel">
          <label className="block">
            <span className="text-sm font-medium text-zinc-700">项目名称</span>
            <input className="mt-2 w-full rounded-md border border-line px-3 py-2.5 outline-none ring-pine/20 focus:ring-4" placeholder="例如 新能源产业政策影响研究" />
          </label>
          <label className="block">
            <span className="text-sm font-medium text-zinc-700">研究说明</span>
            <textarea className="mt-2 min-h-32 w-full rounded-md border border-line px-3 py-2.5 outline-none ring-pine/20 focus:ring-4" placeholder="研究对象、区域、行业和输出目标" />
          </label>
          <div className="grid gap-4 sm:grid-cols-2">
            <label className="block">
              <span className="text-sm font-medium text-zinc-700">地区</span>
              <input className="mt-2 w-full rounded-md border border-line px-3 py-2.5 outline-none ring-pine/20 focus:ring-4" placeholder="China, EU, US" />
            </label>
            <label className="block">
              <span className="text-sm font-medium text-zinc-700">行业</span>
              <input className="mt-2 w-full rounded-md border border-line px-3 py-2.5 outline-none ring-pine/20 focus:ring-4" placeholder="energy, manufacturing" />
            </label>
          </div>
          <div className="flex flex-wrap gap-3 pt-2">
            <button type="button" className="rounded-md bg-pine px-4 py-2.5 text-sm font-semibold text-white">
              创建 mock 项目
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
