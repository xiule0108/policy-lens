import { AppShell } from "@/components/AppShell";
import { StatusPill } from "@/components/StatusPill";
import { policies } from "@/lib/mock";

export default function PolicyLibraryPage() {
  return (
    <AppShell>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-semibold text-ink">政策库</h1>
          <p className="mt-2 text-sm text-zinc-600">Policy records preserve source, timestamp, and checksum fields.</p>
        </div>
        <button className="w-fit rounded-md border border-line bg-white px-4 py-2.5 text-sm font-semibold text-ink">检索政策</button>
      </div>

      <div className="mt-6 grid gap-4">
        {policies.map((policy) => (
          <article key={policy.id} className="rounded-lg border border-line bg-white p-5 shadow-panel">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <h2 className="text-lg font-semibold text-ink">{policy.title}</h2>
                <p className="mt-2 text-sm text-zinc-600">{policy.issuer} · {policy.jurisdiction} · {policy.date}</p>
              </div>
              <StatusPill>{policy.type}</StatusPill>
            </div>
            <div className="mt-4 grid gap-3 text-sm text-zinc-600 sm:grid-cols-3">
              <div>Policy ID: {policy.id}</div>
              <div>sha256: {policy.checksum}</div>
              <div>Export: reserved</div>
            </div>
          </article>
        ))}
      </div>
    </AppShell>
  );
}
