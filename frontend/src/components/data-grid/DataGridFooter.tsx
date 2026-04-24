import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/Button";

export function DataGridFooter({
  page,
  perPage,
  total,
  count,
  loading,
  onPrev,
  onNext,
}: {
  page: number;
  perPage: number;
  total: number;
  count: number;
  loading?: boolean;
  onPrev: () => void;
  onNext: () => void;
}) {
  return (
    <div className="flex flex-col gap-3 border-t border-[var(--color-border)] bg-[var(--color-surface-subtle)] px-4 py-4 sm:flex-row sm:items-center sm:justify-between">
      <p className="text-sm text-[var(--color-text-muted)]">
        Showing <span className="font-semibold text-[var(--color-text)]">{count}</span> of{" "}
        <span className="font-semibold text-[var(--color-text)]">{total}</span> records
      </p>
      <div className="flex items-center gap-2">
        <span className="rounded-xl border border-[var(--color-border)] bg-white px-3 py-2 text-sm font-medium text-[var(--color-text-muted)]">
          Page {page}
        </span>
        <Button variant="secondary" onClick={onPrev} disabled={page === 1 || loading}>
          <ChevronLeft className="h-4 w-4" />
          Prev
        </Button>
        <Button variant="secondary" onClick={onNext} disabled={page * perPage >= total || loading}>
          Next
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
