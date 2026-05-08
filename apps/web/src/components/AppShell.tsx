import Link from "next/link";
import type { ReactNode } from "react";

const navItems = [
  { href: "/", label: "总览" },
  { href: "/projects", label: "项目" },
  { href: "/policy-library", label: "政策库" },
  { href: "/settings/models", label: "模型" }
];

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-paper">
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-line bg-white/82 px-5 py-6 shadow-sm lg:block">
        <Link href="/" className="block">
          <div className="text-xl font-semibold text-ink">PolicyLens</div>
          <div className="mt-1 text-sm text-zinc-500">政研透镜</div>
        </Link>
        <nav className="mt-9 space-y-2">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="block rounded-md px-3 py-2 text-sm font-medium text-zinc-700 transition hover:bg-pine hover:text-white"
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="absolute bottom-6 left-5 right-5 rounded-md border border-line bg-paper p-4 text-xs leading-5 text-zinc-600">
          v0.1.0-alpha
          <br />
          Deterministic draft · human review
        </div>
      </aside>
      <header className="border-b border-line bg-white px-5 py-4 lg:hidden">
        <div className="flex items-center justify-between">
          <Link href="/" className="font-semibold">PolicyLens</Link>
          <Link href="/projects/new" className="rounded-md bg-pine px-3 py-2 text-sm font-medium text-white">
            新建
          </Link>
        </div>
      </header>
      <main className="lg:pl-64">
        <div className="mx-auto max-w-7xl px-5 py-6 sm:px-8 lg:px-10">{children}</div>
      </main>
    </div>
  );
}
