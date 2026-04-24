import { SearchX } from "lucide-react";

export function EmptyState({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-[var(--color-border-strong)] bg-[var(--color-surface-subtle)] px-6 py-12 text-center">
      <div className="rounded-2xl bg-white p-3 shadow-[var(--shadow-card)]">
        <SearchX className="h-5 w-5 text-[var(--color-text-subtle)]" />
      </div>
      <div className="space-y-1">
        <p className="text-base font-semibold text-[var(--color-text)]">{title}</p>
        <p className="max-w-md text-sm text-[var(--color-text-muted)]">{description}</p>
      </div>
    </div>
  );
}
