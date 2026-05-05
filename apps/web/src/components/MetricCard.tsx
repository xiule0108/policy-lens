export function MetricCard({ label, value, detail }: { label: string; value: string; detail: string }) {
  return (
    <div className="rounded-lg border border-line bg-white p-5 shadow-panel">
      <div className="text-sm font-medium text-zinc-500">{label}</div>
      <div className="mt-3 text-3xl font-semibold text-ink">{value}</div>
      <div className="mt-2 text-sm text-zinc-600">{detail}</div>
    </div>
  );
}
