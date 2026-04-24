"use client";

import { useEffect, useMemo, useState } from "react";
import { Plus, Trash2 } from "lucide-react";
import { DataGrid, type DataGridColumn } from "@/components/data-grid/DataGrid";
import { DataGridFooter } from "@/components/data-grid/DataGridFooter";
import { DataGridToolbar } from "@/components/data-grid/DataGridToolbar";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { FeedbackBanner } from "@/components/ui/FeedbackBanner";
import { Input } from "@/components/ui/Input";
import { PageHeader, PageHeaderActionGroup } from "@/components/ui/PageHeader";
import { StatusBadge } from "@/components/ui/StatusBadge";
import api from "@/lib/api";
import { formatDate, formatRelativeCount } from "@/lib/format";
import type { PaginatedResponse, Rule } from "@/lib/types";

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

export default function RulesPage() {
  const [rules, setRules] = useState<PaginatedResponse<Rule> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newRule, setNewRule] = useState({
    name: "",
    description: "",
    trigger_event: "enrichment_complete",
  });
  const [sortState, setSortState] = useState<SortState>({ columnId: "created_at", direction: "desc" });

  const fetchRules = async () => {
    try {
      setLoading(true);
      const response = await api.rules.list({ page, per_page: 10 });
      setRules(response);
      setError(null);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Failed to load rules.");
      setRules(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void fetchRules();
  }, [page]);

  const handleCreateRule = async () => {
    if (!newRule.name.trim()) {
      setError("Rule name is required.");
      return;
    }

    await api.rules.create({
      name: newRule.name.trim(),
      description: newRule.description.trim() || undefined,
      trigger_event: newRule.trigger_event,
      conditions: {},
      actions: [{ action_type: "send_email", action_params: {} }],
      is_active: true,
    });

    setNewRule({ name: "", description: "", trigger_event: "enrichment_complete" });
    setShowCreateForm(false);
    setMessage("Rule created successfully.");
    await fetchRules();
  };

  const handleDeleteRule = async (ruleId: number) => {
    if (!window.confirm("Delete this rule?")) return;
    await api.rules.remove(ruleId);
    setMessage("Rule deleted.");
    await fetchRules();
  };

  const columns = useMemo<Array<DataGridColumn<Rule>>>(() => [
    {
      id: "name",
      header: "Rule",
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
      id: "trigger_event",
      header: "Trigger",
      sortable: true,
      sortValue: (row) => row.trigger_event,
      render: (row) => <span className="font-medium text-[var(--color-text)]">{row.trigger_event}</span>,
    },
    {
      id: "status",
      header: "Status",
      sortable: true,
      sortValue: (row) => (row.is_active ? 1 : 0),
      render: (row) => <StatusBadge status={row.is_active ? "active" : "paused"} />,
    },
    {
      id: "execution_count",
      header: "Runs",
      align: "right",
      sortable: true,
      sortValue: (row) => row.execution_count,
      render: (row) => <span className="font-medium text-[var(--color-text)]">{formatRelativeCount(row.execution_count)}</span>,
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
        <Button variant="ghost" onClick={() => void handleDeleteRule(row.rule_id)}>
          <Trash2 className="h-4 w-4" />
        </Button>
      ),
    },
  ], []);

  const sortedRows = useMemo(() => {
    const items = [...(rules?.items ?? [])];
    if (!sortState) return items;
    const column = columns.find((entry) => entry.id === sortState.columnId);
    if (!column?.sortValue) return items;

    return items.sort((left, right) => {
      const comparison = compareValues(column.sortValue?.(left), column.sortValue?.(right));
      return sortState.direction === "asc" ? comparison : -comparison;
    });
  }, [columns, rules?.items, sortState]);

  return (
    <div className="space-y-6 reveal-animation">
      <PageHeader
        eyebrow="Rules"
        title="Automation workspace"
        description="Manage event-driven rules in the same enterprise pattern as the rest of the operational workspace."
        actions={(
          <PageHeaderActionGroup>
            <Button onClick={() => setShowCreateForm((current) => !current)}>
              <Plus className="h-4 w-4" />
              New rule
            </Button>
          </PageHeaderActionGroup>
        )}
      />

      {error ? <FeedbackBanner tone="error" message={error} /> : null}
      {message ? <FeedbackBanner tone="success" message={message} /> : null}

      {showCreateForm ? (
        <div className="grid gap-4 rounded-3xl border border-[var(--color-border)] bg-white p-6 shadow-[var(--shadow-card)] lg:grid-cols-3">
          <Input value={newRule.name} onChange={(event) => setNewRule((current) => ({ ...current, name: event.target.value }))} placeholder="Rule name" />
          <Input value={newRule.description} onChange={(event) => setNewRule((current) => ({ ...current, description: event.target.value }))} placeholder="Description" />
          <select
            value={newRule.trigger_event}
            onChange={(event) => setNewRule((current) => ({ ...current, trigger_event: event.target.value }))}
            className="w-full rounded-xl border border-[var(--color-border-strong)] bg-white px-3.5 py-2.5 text-sm text-[var(--color-text)] outline-none transition focus:border-[var(--color-accent)] focus:ring-4 focus:ring-[var(--color-accent-ring)]"
          >
            <option value="enrichment_complete">enrichment_complete</option>
            <option value="lead_score_high">lead_score_high</option>
          </select>
          <div className="lg:col-span-3 flex gap-2 justify-end">
            <Button variant="secondary" onClick={() => setShowCreateForm(false)}>Cancel</Button>
            <Button onClick={() => void handleCreateRule()}>Create rule</Button>
          </div>
        </div>
      ) : null}

      <DataGridToolbar
        searchValue=""
        onSearchChange={() => undefined}
        searchPlaceholder="Rule search will be added in the next phase"
        actionSlot={<div className="rounded-xl border border-[var(--color-border)] bg-white px-3 py-2 text-sm text-[var(--color-text-muted)]">{rules?.total ?? 0} total rules</div>}
      />

      <DataGrid
        columns={columns}
        rows={sortedRows}
        rowKey={(row) => row.rule_id}
        sortState={sortState}
        onSort={(columnId) =>
          setSortState((current) =>
            current?.columnId === columnId
              ? { columnId, direction: current.direction === "asc" ? "desc" : "asc" }
              : { columnId, direction: "asc" },
          )
        }
        loading={loading}
        loadingLabel="Loading rules..."
        emptyState={<EmptyState title="No rules yet" description="Create an automation rule to start codifying workflow behavior across the CRM." />}
      />

      {rules ? (
        <DataGridFooter
          page={page}
          perPage={rules.per_page}
          total={rules.total}
          count={rules.items.length}
          loading={loading}
          onPrev={() => setPage((current) => Math.max(1, current - 1))}
          onNext={() => setPage((current) => current + 1)}
        />
      ) : null}
    </div>
  );
}
