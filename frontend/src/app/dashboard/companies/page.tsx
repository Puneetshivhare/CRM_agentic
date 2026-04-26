"use client";

import { useEffect, useMemo, useState } from "react";
import { Plus, Radar } from "lucide-react";
import AddCompanyModal from "@/components/AddCompanyModal";
import { DataGrid, type DataGridColumn } from "@/components/data-grid/DataGrid";
import { DataGridFooter } from "@/components/data-grid/DataGridFooter";
import { DataGridToolbar } from "@/components/data-grid/DataGridToolbar";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { FeedbackBanner } from "@/components/ui/FeedbackBanner";
import { PageHeader, PageHeaderActionGroup } from "@/components/ui/PageHeader";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { formatDate, formatRelativeCount } from "@/lib/format";
import api from "@/lib/api";
import type { Company, PaginatedResponse } from "@/lib/types";

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

export default function CompaniesPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [page, setPage] = useState(1);
  const [data, setData] = useState<PaginatedResponse<Company> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [addingCompany, setAddingCompany] = useState(false);
  const [selectedRows, setSelectedRows] = useState<Array<string | number>>([]);
  const [sortState, setSortState] = useState<SortState>({ columnId: "created_at", direction: "desc" });

  const fetchCompanies = async () => {
    try {
      setLoading(true);
      const result = await api.companies.list({ search: searchTerm || undefined, page, per_page: 10 });
      setData(result);
      setError(null);
    } catch (fetchError) {
      setError(fetchError instanceof Error ? fetchError.message : "Failed to load companies.");
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void fetchCompanies();
    }, 250);

    return () => window.clearTimeout(timer);
  }, [page, searchTerm]);

  useEffect(() => {
    setSelectedRows([]);
  }, [data?.page, searchTerm]);

  const handleAddCompany = async (formData: { name: string; domain?: string; industry?: string; headcount?: number; funding_stage?: string }) => {
    setAddingCompany(true);
    try {
      await api.companies.create(formData);
      setShowAddModal(false);
      setMessage("Company created and added to the monitoring workspace.");
      await fetchCompanies();
    } finally {
      setAddingCompany(false);
    }
  };

  const handleToggleMonitoring = async (companyId: number) => {
    await api.companies.toggleMonitoring(companyId);
    setMessage("Monitoring state updated.");
    await fetchCompanies();
  };

  const handleBulkToggleMonitoring = async () => {
    if (selectedRows.length === 0) return;

    await Promise.all(selectedRows.map((rowId) => api.companies.toggleMonitoring(Number(rowId))));
    setSelectedRows([]);
    setMessage("Monitoring state updated for selected companies.");
    await fetchCompanies();
  };

  const columns = useMemo<Array<DataGridColumn<Company>>>(() => [
    {
      id: "name",
      header: "Company",
      sortable: true,
      sortValue: (row) => row.name,
      render: (row) => (
        <div className="min-w-0">
          <p 
            className="truncate font-semibold text-[var(--color-text)] cursor-pointer hover:underline"
            onClick={() => alert("Company detail view coming soon")}
          >
            {row.name}
          </p>
          <p className="truncate text-sm text-[var(--color-text-muted)]">{row.domain || "No domain recorded"}</p>
        </div>
      ),
    },
    {
      id: "industry",
      header: "Industry",
      sortable: true,
      sortValue: (row) => row.industry,
      render: (row) => (
        <div>
          <p className="font-medium text-[var(--color-text)]">{row.industry || "Uncategorized"}</p>
          <p className="text-sm text-[var(--color-text-muted)]">{row.funding_stage || "Funding stage unknown"}</p>
        </div>
      ),
    },
    {
      id: "headcount",
      header: "Headcount",
      align: "right",
      sortable: true,
      sortValue: (row) => row.headcount,
      render: (row) => <span className="font-medium text-[var(--color-text)]">{formatRelativeCount(row.headcount)}</span>,
    },
    {
      id: "prospects_count",
      header: "Prospects",
      align: "right",
      sortable: true,
      sortValue: (row) => row.prospects_count,
      render: (row) => <span className="font-medium text-[var(--color-text)]">{formatRelativeCount(row.prospects_count)}</span>,
    },
    {
      id: "monitoring_enabled",
      header: "Monitoring",
      sortable: true,
      sortValue: (row) => (row.monitoring_enabled ? 1 : 0),
      render: (row) => <StatusBadge status={row.monitoring_enabled ? "active" : "paused"} />,
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
        <Button variant="secondary" onClick={() => void handleToggleMonitoring(row.company_id)}>
          <Radar className="h-4 w-4" />
          {row.monitoring_enabled ? "Pause" : "Monitor"}
        </Button>
      ),
    },
  ], []);

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
        eyebrow="Companies"
        title="Account workspace"
        description="Track companies, monitor buying signals, and run a consistent operating model across the entire account list."
        actions={(
          <PageHeaderActionGroup>
            <Button onClick={() => setShowAddModal(true)}>
              <Plus className="h-4 w-4" />
              Add company
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
          searchPlaceholder="Search by company, domain, or industry"
          selectedCount={selectedRows.length}
          bulkActionLabel="Toggle monitoring"
          onBulkAction={handleBulkToggleMonitoring}
          actionSlot={
            <div className="rounded-xl border border-[var(--color-border)] bg-white px-3 py-2 text-sm text-[var(--color-text-muted)]">
              {data?.total ?? 0} total companies
            </div>
          }
        />

        <DataGrid
          columns={columns}
          rows={sortedRows}
          rowKey={(row) => row.company_id}
          selectedRows={selectedRows}
          onToggleRow={(rowId) =>
            setSelectedRows((current) =>
              current.includes(rowId) ? current.filter((item) => item !== rowId) : [...current, rowId],
            )
          }
          onToggleAll={() => {
            const ids = sortedRows.map((row) => row.company_id);
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
          loadingLabel="Loading companies..."
          emptyState={<EmptyState title="No companies found" description="Track your first account to start collecting signals and mapping prospects to target companies." />}
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

      <AddCompanyModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        onSubmit={handleAddCompany}
        loading={addingCompany}
      />
    </div>
  );
}
