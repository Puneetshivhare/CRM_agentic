import { Search } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";

export function DataGridToolbar({
  searchValue,
  searchPlaceholder,
  onSearchChange,
  selectedCount = 0,
  bulkActionLabel,
  onBulkAction,
  actionSlot,
}: {
  searchValue: string;
  searchPlaceholder: string;
  onSearchChange: (value: string) => void;
  selectedCount?: number;
  bulkActionLabel?: string;
  onBulkAction?: () => void;
  actionSlot?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-3 border-b border-[var(--color-border)] bg-[var(--color-surface-subtle)] px-4 py-4 lg:flex-row lg:items-center lg:justify-between">
      <div className="flex flex-1 items-center gap-3">
        <div className="relative max-w-xl flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--color-text-subtle)]" />
          <Input
            value={searchValue}
            onChange={(event) => onSearchChange(event.target.value)}
            placeholder={searchPlaceholder}
            className="pl-10"
          />
        </div>
        {selectedCount > 0 && bulkActionLabel && onBulkAction ? (
          <Button variant="secondary" onClick={onBulkAction}>
            {bulkActionLabel} ({selectedCount})
          </Button>
        ) : null}
      </div>
      {actionSlot ? <div className="flex items-center gap-2">{actionSlot}</div> : null}
    </div>
  );
}
