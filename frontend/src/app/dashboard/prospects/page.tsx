"use client";

import { useEffect, useMemo, useState } from "react";
import { Download, Plus } from "lucide-react";
import AddProspectModal from "@/components/AddProspectModal";
import ProspectActionsMenu from "@/components/ProspectActionsMenu";
import { DataGrid, type DataGridColumn } from "@/components/data-grid/DataGrid";
import { DataGridFooter } from "@/components/data-grid/DataGridFooter";
import { DataGridToolbar } from "@/components/data-grid/DataGridToolbar";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { FeedbackBanner } from "@/components/ui/FeedbackBanner";
import { PageHeader, PageHeaderActionGroup } from "@/components/ui/PageHeader";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { formatDate, getInitials } from "@/lib/format";
import api from "@/lib/api";
import type { PaginatedResponse, Prospect } from "@/lib/types";

type SortState = {
  columnId: string;
  direction: "asc" | "desc";
} | null;

function compareValues(a: string | number | null | undefined, b: string | number | null | undefined) {
  if (a == null && b == null) return 0;
  if (a == null) return 1;
  if (b == null) return -1;
  if (typeof a === "number" && typeof b === "number") return a - b;
  return String(a).localeCompare(String(b));
}

export default function ProspectsPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [page, setPage] = useState(1);
  const [data, setData] = useState<PaginatedResponse<Prospect> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [addingProspect, setAddingProspect] = useState(false);
  const [enrichingIds, setEnrichingIds] = useState<Set<number>>(new Set());
  const [selectedRows, setSelectedRows] = useState<Array<string | number>>([]);
  const [sortState, setSortState] = useState<SortState>({ columnId: "created_at", direction: "desc" });

  const fetchProspects = async () => {
    try {
      setLoading(true);
      const result = await api.prospects.list({ search: searchTerm || undefined, page, per_page: 10 });
      setData(result);
      setError(null);
    } catch (fetchError) {
      setError(fetchError instanceof Error ? fetchError.message : "Failed to load prospects.");
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void fetchProspects();
    }, 250);

    return () => window.clearTimeout(timer);
  }, [page, searchTerm]);

  useEffect(() => {
    setSelectedRows([]);
  }, [data?.page, searchTerm]);

  const handleAddProspect = async (formData: { first_name: string; last_name?: string; email: string; title?: string }) => {
    setAddingProspect(true);
    try {
      await api.prospects.create(formData);
      setShowAddModal(false);
      setMessage("Prospect created and queued for enrichment.");
      await fetchProspects();
    } finally {
      setAddingProspect(false);
    }
  };

  const handleEnrichProspect = async (prospectId: number) => {
    setEnrichingIds((current) => new Set(current).add(prospectId));
    try {
      await api.enrichment.triggerSearch(prospectId);
      setMessage("Search-driven enrichment triggered successfully.");
      await fetchProspects();
    } finally {
      setEnrichingIds((current) => {
        const next = new Set(current);
        next.delete(prospectId);
        return next;
      });
    }
  };

  const handleDeleteProspect = async (prospectId: number) => {
    await api.prospects.remove(prospectId);
    setMessage("Prospect removed from the workspace.");
    await fetchProspects();
  };

  const handleBulkEnrich = async () => {
    if (selectedRows.length === 0) return;

    setMessage(`Triggering search enrichment for ${selectedRows.length} selected prospects...`);
    await Promise.all(selectedRows.map((rowId) => api.enrichment.triggerSearch(Number(rowId))));
    setSelectedRows([]);
    setMessage("Bulk search enrichment queued successfully.");
    await fetchProspects();
  };

  const handleExport = () => {
    if (!data?.items.length) return;

    const csv = [
      ["First name", "Last name", "Email", "Title", "Status"].join(","),
      ...data.items.map((prospect) =>
        [
          prospect.first_name ?? "",
          prospect.last_name ?? "",
          prospect.email ?? "",
          prospect.title ?? "",
          prospect.enrichment_status,
        ].join(","),
      ),
    ].join("\n");

    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "prospects.csv";
    link.click();
    URL.revokeObjectURL(url);
  };

  const columns = useMemo<Array<DataGridColumn<Prospect>>>(() => [
    {
      id: "prospect",
      header: "Prospect",
      sortable: true,
      sortValue: (row) => `${row.first_name ?? ""} ${row.last_name ?? ""}`.trim(),
      render: (row) => (
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface-subtle)] text-sm font-semibold text-[var(--color-text)]">
            {getInitials(row.first_name, row.last_name)}
          </div>
          <div className="min-w-0">
            <p 
              className="truncate font-semibold text-[var(--color-text)] cursor-pointer hover:underline"
              onClick={() => alert("Prospect detail view coming soon")}
            >
              {`${row.first_name ?? ""} ${row.last_name ?? ""}`.trim() || "Unnamed prospect"}
            </p>
            <p className="truncate text-sm text-[var(--color-text-muted)]">{row.title || "No title provided"}</p>
          </div>
        </div>
      ),
    },
    {
      id: "email",
      header: "Email",
      sortable: true,
      sortValue: (row) => row.email,
      render: (row) => <span className="text-sm text-[var(--color-text-muted)]">{row.email || "No email"}</span>,
    },
    {
      id: "status",
      header: "Status",
      sortable: true,
      sortValue: (row) => row.enrichment_status,
      render: (row) => <StatusBadge status={row.enrichment_status as "enriched" | "pending" | "enriching" | "failed"} />,
    },
    {
      id: "confidence",
      header: "Confidence",
      align: "right",
      sortable: true,
      sortValue: (row) => row.enrichment_confidence,
      render: (row) => <span className="font-medium text-[var(--color-text)]">{Math.round((row.enrichment_confidence || 0) * 100)}%</span>,
    },
    {
      id: "created_at",
      header: "Added",
      sortable: true,
      sortValue: (row) => new Date(row.created_at).getTime(),
      render: (row) => <span>{formatDate(row.created_at)}</span>,
    },
    {
      id: "actions",
      header: "Actions",
      align: "right",
      render: (row) => (
        <ProspectActionsMenu
          prospectId={row.prospect_id}
          email={row.email}
          firstName={row.first_name}
          onEnrich={handleEnrichProspect}
          onDelete={handleDeleteProspect}
          isEnriching={enrichingIds.has(row.prospect_id)}
        />
      ),
    },
  ], [enrichingIds]);

  const sortedRows = useMemo(() => {
    const items = [...(data?.items ?? [])];
    if (!sortState) return items;

    const column = columns.find((entry) => entry.id === sortState.columnId);
    if (!column?.sortValue) return items;

    return items.sort((left, right) => {
      const comparison = compareValues(column.sortValue?.(left), column.sortValue?.(right));
      return sortState.direction === "asc" ? comparison : -comparison;
    });
  }, [columns, data?.items, sortState]);

  return (
    <div className="space-y-6 reveal-animation">
      <PageHeader
        eyebrow="Prospects"
        title="Prospect workspace"
        description="Manage people records, queue enrichment, and operate from one standardized Clay-style table."
        actions={(
          <PageHeaderActionGroup>
            <Button variant="secondary" onClick={handleExport} disabled={!data?.items.length}>
              <Download className="h-4 w-4" />
              Export
            </Button>
            <Button onClick={() => setShowAddModal(true)}>
              <Plus className="h-4 w-4" />
              Add prospect
            </Button>
          </PageHeaderActionGroup>
        )}
      />

      {error ? <FeedbackBanner tone="error" message={error} /> : null}
      {message ? <FeedbackBanner tone="success" message={message} /> : null}

      <div>
        <DataGridToolbar
          searchValue={searchTerm}
          onSearchChange={(value) => {
            setSearchTerm(value);
            setPage(1);
          }}
          searchPlaceholder="Search by name, email, or title"
          selectedCount={selectedRows.length}
          bulkActionLabel="Enrich selected"
          onBulkAction={handleBulkEnrich}
          actionSlot={
            <div className="rounded-xl border border-[var(--color-border)] bg-white px-3 py-2 text-sm text-[var(--color-text-muted)]">
              {data?.total ?? 0} total prospects
            </div>
          }
        />

        <DataGrid
          columns={columns}
          rows={sortedRows}
          rowKey={(row) => row.prospect_id}
          selectedRows={selectedRows}
          onToggleRow={(rowId) =>
            setSelectedRows((current) =>
              current.includes(rowId) ? current.filter((item) => item !== rowId) : [...current, rowId],
            )
          }
          onToggleAll={() => {
            const ids = sortedRows.map((row) => row.prospect_id);
            setSelectedRows(selectedRows.length === ids.length ? [] : ids);
          }}
          sortState={sortState}
          onSort={(columnId) =>
            setSortState((current) =>
              current?.columnId === columnId
                ? { columnId, direction: current.direction === "asc" ? "desc" : "asc" }
                : { columnId, direction: "asc" },
            )
          }
          loading={loading}
          loadingLabel="Loading prospects..."
          emptyState={<EmptyState title="No prospects found" description="Try a broader search, or add your first prospect to begin enrichment workflows." />}
        />

        {data ? (
          <DataGridFooter
            page={page}
            perPage={data.per_page}
            total={data.total}
            count={data.items.length}
            loading={loading}
            onPrev={() => setPage((current) => Math.max(1, current - 1))}
            onNext={() => setPage((current) => current + 1)}
          />
        ) : null}
      </div>

      <AddProspectModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        onSubmit={handleAddProspect}
        loading={addingProspect}
      />
    </div>
  );
}
