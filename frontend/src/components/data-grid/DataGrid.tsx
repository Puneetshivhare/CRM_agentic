"use client";

import { ArrowDown, ArrowUp, ArrowUpDown } from "lucide-react";
import { cn } from "@/lib/utils";

type Primitive = string | number | null | undefined;

export interface DataGridColumn<T> {
  id: string;
  header: string;
  width?: string;
  align?: "left" | "right" | "center";
  sortable?: boolean;
  sortValue?: (row: T) => Primitive;
  render: (row: T) => React.ReactNode;
}

interface DataGridProps<T> {
  columns: Array<DataGridColumn<T>>;
  rows: T[];
  rowKey: (row: T) => string | number;
  selectedRows?: Array<string | number>;
  onToggleRow?: (rowId: string | number) => void;
  onToggleAll?: () => void;
  sortState?: {
    columnId: string;
    direction: "asc" | "desc";
  } | null;
  onSort?: (columnId: string) => void;
  loading?: boolean;
  loadingLabel?: string;
  emptyState?: React.ReactNode;
}

function SortIcon({ active, direction }: { active: boolean; direction?: "asc" | "desc" }) {
  if (!active) return <ArrowUpDown className="h-3.5 w-3.5 text-[var(--color-text-subtle)]" />;
  return direction === "asc" ? <ArrowUp className="h-3.5 w-3.5 text-[var(--color-text-muted)]" /> : <ArrowDown className="h-3.5 w-3.5 text-[var(--color-text-muted)]" />;
}

export function DataGrid<T>({
  columns,
  rows,
  rowKey,
  selectedRows = [],
  onToggleRow,
  onToggleAll,
  sortState,
  onSort,
  loading,
  loadingLabel = "Loading data...",
  emptyState,
}: DataGridProps<T>) {
  const hasSelection = Boolean(onToggleRow);
  const allSelected = rows.length > 0 && selectedRows.length === rows.length;

  return (
    <div className="overflow-hidden rounded-3xl border border-[var(--color-border)] bg-white shadow-[var(--shadow-card)]">
      <div className="overflow-x-auto">
        <table className="min-w-full border-collapse text-left">
          <thead className="sticky top-0 z-10 bg-[var(--color-surface-subtle)]">
            <tr className="border-b border-[var(--color-border)]">
              {hasSelection ? (
                <th className="w-12 px-4 py-3">
                  <input
                    type="checkbox"
                    checked={allSelected}
                    onChange={onToggleAll}
                    aria-label="Select all rows"
                    className="h-4 w-4 rounded border-[var(--color-border-strong)] text-[var(--color-accent)] focus:ring-[var(--color-accent-ring)]"
                  />
                </th>
              ) : null}
              {columns.map((column) => (
                <th
                  key={column.id}
                  className={cn(
                    "px-4 py-3 text-xs font-semibold uppercase tracking-[0.12em] text-[var(--color-text-subtle)]",
                    column.align === "right" ? "text-right" : column.align === "center" ? "text-center" : "text-left",
                  )}
                  style={column.width ? { width: column.width } : undefined}
                >
                  {column.sortable ? (
                    <button
                      type="button"
                      onClick={() => onSort?.(column.id)}
                      className={cn(
                        "inline-flex items-center gap-1.5 rounded-md transition hover:text-[var(--color-text-muted)]",
                        column.align === "right" ? "ml-auto" : "",
                      )}
                    >
                      <span>{column.header}</span>
                      <SortIcon active={sortState?.columnId === column.id} direction={sortState?.direction} />
                    </button>
                  ) : (
                    column.header
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={columns.length + (hasSelection ? 1 : 0)} className="px-6 py-16 text-center">
                  <div className="flex flex-col items-center gap-3">
                    <div className="h-6 w-6 animate-spin rounded-full border-2 border-[var(--color-border)] border-t-[var(--color-accent)]" />
                    <p className="text-sm font-medium text-[var(--color-text-muted)]">{loadingLabel}</p>
                  </div>
                </td>
              </tr>
            ) : rows.length === 0 ? (
              <tr>
                <td colSpan={columns.length + (hasSelection ? 1 : 0)} className="px-6 py-14">
                  {emptyState}
                </td>
              </tr>
            ) : (
              rows.map((row) => {
                const currentKey = rowKey(row);
                const isSelected = selectedRows.includes(currentKey);

                return (
                  <tr key={currentKey} className="border-b border-[var(--color-border)] last:border-b-0 hover:bg-[var(--color-surface-subtle)]">
                    {hasSelection ? (
                      <td className="px-4 py-4">
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => onToggleRow?.(currentKey)}
                          aria-label={`Select row ${currentKey}`}
                          className="h-4 w-4 rounded border-[var(--color-border-strong)] text-[var(--color-accent)] focus:ring-[var(--color-accent-ring)]"
                        />
                      </td>
                    ) : null}
                    {columns.map((column) => (
                      <td
                        key={column.id}
                        className={cn(
                          "px-4 py-4 align-middle text-sm text-[var(--color-text-muted)]",
                          column.align === "right" ? "text-right" : column.align === "center" ? "text-center" : "text-left",
                        )}
                      >
                        {column.render(row)}
                      </td>
                    ))}
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
