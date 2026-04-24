"use client";

import { useEffect, useMemo, useState } from "react";
import { Mail, Plus, Trash2 } from "lucide-react";
import CreateCampaignModal from "@/components/CreateCampaignModal";
import { DataGrid, type DataGridColumn } from "@/components/data-grid/DataGrid";
import { DataGridFooter } from "@/components/data-grid/DataGridFooter";
import { DataGridToolbar } from "@/components/data-grid/DataGridToolbar";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { FeedbackBanner } from "@/components/ui/FeedbackBanner";
import { PageHeader, PageHeaderActionGroup } from "@/components/ui/PageHeader";
import { StatusBadge } from "@/components/ui/StatusBadge";
import api from "@/lib/api";
import { formatDate, formatRelativeCount } from "@/lib/format";
import type { Campaign, PaginatedResponse } from "@/lib/types";

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

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<PaginatedResponse<Campaign> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [creatingCampaign, setCreatingCampaign] = useState(false);
  const [sortState, setSortState] = useState<SortState>({ columnId: "created_at", direction: "desc" });

  const fetchCampaigns = async () => {
    try {
      setLoading(true);
      const response = await api.campaigns.list({ page, per_page: 10 });
      setCampaigns(response);
      setError(null);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Failed to load campaigns.");
      setCampaigns(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void fetchCampaigns();
  }, [page]);

  const handleCreateCampaign = async (formData: { name: string; description: string; sequence_steps: Campaign["sequence_steps"] }) => {
    setCreatingCampaign(true);
    try {
      await api.campaigns.create({ ...formData, is_active: true });
      setShowCreateModal(false);
      setMessage("Campaign created successfully.");
      setPage(1);
      await fetchCampaigns();
    } finally {
      setCreatingCampaign(false);
    }
  };

  const handleDeleteCampaign = async (campaignId: number) => {
    if (!window.confirm("Delete this campaign?")) return;
    await api.campaigns.remove(campaignId);
    setMessage("Campaign deleted.");
    await fetchCampaigns();
  };

  const columns = useMemo<Array<DataGridColumn<Campaign>>>(() => [
    {
      id: "name",
      header: "Campaign",
      sortable: true,
      sortValue: (row) => row.name,
      render: (row) => (
        <div>
          <p className="font-semibold text-[var(--color-text)]">{row.name}</p>
          <p className="text-sm text-[var(--color-text-muted)]">{row.description || "No description"}</p>
        </div>
      ),
    },
    {
      id: "status",
      header: "Status",
      sortable: true,
      sortValue: (row) => (row.is_active ? 1 : 0),
      render: (row) => <StatusBadge status={row.is_active ? "active" : "paused"} />,
    },
    {
      id: "steps",
      header: "Steps",
      align: "right",
      sortable: true,
      sortValue: (row) => row.sequence_steps.length,
      render: (row) => <span className="font-medium text-[var(--color-text)]">{row.sequence_steps.length}</span>,
    },
    {
      id: "enrolled",
      header: "Enrolled",
      align: "right",
      sortable: true,
      sortValue: (row) => row.enrolled_count,
      render: (row) => <span className="font-medium text-[var(--color-text)]">{formatRelativeCount(row.enrolled_count)}</span>,
    },
    {
      id: "conversion",
      header: "Conversion",
      align: "right",
      sortable: true,
      sortValue: (row) => row.conversion_rate,
      render: (row) => <span className="font-medium text-[var(--color-text)]">{(row.conversion_rate * 100).toFixed(1)}%</span>,
    },
    {
      id: "created_at",
      header: "Created",
      sortable: true,
      sortValue: (row) => new Date(row.created_at).getTime(),
      render: (row) => <span>{formatDate(row.created_at)}</span>,
    },
    {
      id: "actions",
      header: "Actions",
      align: "right",
      render: (row) => (
        <Button variant="ghost" onClick={() => void handleDeleteCampaign(row.campaign_id)}>
          <Trash2 className="h-4 w-4" />
        </Button>
      ),
    },
  ], []);

  const sortedRows = useMemo(() => {
    const items = [...(campaigns?.items ?? [])];
    if (!sortState) return items;
    const column = columns.find((entry) => entry.id === sortState.columnId);
    if (!column?.sortValue) return items;

    return items.sort((left, right) => {
      const comparison = compareValues(column.sortValue?.(left), column.sortValue?.(right));
      return sortState.direction === "asc" ? comparison : -comparison;
    });
  }, [campaigns?.items, columns, sortState]);

  return (
    <div className="space-y-6 reveal-animation">
      <PageHeader
        eyebrow="Campaigns"
        title="Campaign workspace"
        description="Manage outreach sequences in the same enterprise operating model as prospects and companies."
        actions={(
          <PageHeaderActionGroup>
            <Button onClick={() => setShowCreateModal(true)}>
              <Plus className="h-4 w-4" />
              Add campaign
            </Button>
          </PageHeaderActionGroup>
        )}
      />

      {error ? <FeedbackBanner tone="error" message={error} /> : null}
      {message ? <FeedbackBanner tone="success" message={message} /> : null}

      <DataGridToolbar
        searchValue=""
        onSearchChange={() => undefined}
        searchPlaceholder="Campaign search will be added in the next phase"
        actionSlot={<div className="rounded-xl border border-[var(--color-border)] bg-white px-3 py-2 text-sm text-[var(--color-text-muted)]">{campaigns?.total ?? 0} total campaigns</div>}
      />

      <DataGrid
        columns={columns}
        rows={sortedRows}
        rowKey={(row) => row.campaign_id}
        sortState={sortState}
        onSort={(columnId) =>
          setSortState((current) =>
            current?.columnId === columnId
              ? { columnId, direction: current.direction === "asc" ? "desc" : "asc" }
              : { columnId, direction: "asc" },
          )
        }
        loading={loading}
        loadingLabel="Loading campaigns..."
        emptyState={<EmptyState title="No campaigns yet" description="Create your first sequence to standardize outbound execution for the team." />}
      />

      {campaigns ? (
        <DataGridFooter
          page={page}
          perPage={campaigns.per_page}
          total={campaigns.total}
          count={campaigns.items.length}
          loading={loading}
          onPrev={() => setPage((current) => Math.max(1, current - 1))}
          onNext={() => setPage((current) => current + 1)}
        />
      ) : null}

      <CreateCampaignModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSubmit={handleCreateCampaign}
        loading={creatingCampaign}
      />
    </div>
  );
}
