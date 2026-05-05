import { AppShell } from "@/components/AppShell";
import { StatusPill } from "@/components/StatusPill";
import { providers } from "@/lib/mock";

export default function ModelSettingsPage() {
  return (
    <AppShell>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-semibold text-ink">模型设置</h1>
          <p className="mt-2 text-sm text-zinc-600">Provider presets keep model names user-configurable.</p>
        </div>
        <button className="w-fit rounded-md bg-pine px-4 py-2.5 text-sm font-semibold text-white">新增 Provider</button>
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        {providers.map((provider, index) => (
          <article key={provider} className="rounded-lg border border-line bg-white p-5 shadow-panel">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 className="font-semibold text-ink">{provider}</h2>
                <p className="mt-2 text-sm text-zinc-600">模型名、base URL 和密钥环境变量由用户配置。</p>
              </div>
              <StatusPill tone={index < 9 ? "amber" : "neutral"}>{index < 9 ? "China preset" : "reserved"}</StatusPill>
            </div>
            <div className="mt-4 rounded-md border border-line bg-paper px-3 py-2 text-xs text-zinc-600">
              No API key stored in frontend state
            </div>
          </article>
        ))}
      </div>
    </AppShell>
  );
}
