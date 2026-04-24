"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, Building2, Radar, Users, Zap } from "lucide-react";
import { FeedbackBanner } from "@/components/ui/FeedbackBanner";
import { PageHeader } from "@/components/ui/PageHeader";
import { Panel } from "@/components/ui/Panel";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { formatRelativeCount } from "@/lib/format";
import api from "@/lib/api";
import type { AgentExecution } from "@/lib/types";

interface DashboardStats {
  totalProspects: number;
  enrichedProspects: number;
  pendingProspects: number;
  totalCompanies: number;
}

function StatCard({
  label,
  value,
  helper,
  icon: Icon,
}: {
  label: string;
  value: string;
  helper: string;
  icon: React.ComponentType<{ className?: string }>;
}) {
  return (
    <Panel className="p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.12em] text-[var(--color-text-subtle)]">{label}</p>
          <p className="mt-3 text-3xl font-semibold tracking-[-0.03em] text-[var(--color-text)]">{value}</p>
          <p className="mt-2 text-sm text-[var(--color-text-muted)]">{helper}</p>
        </div>
        <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface-subtle)] p-3">
          <Icon className="h-5 w-5 text-[var(--color-accent)]" />
        </div>
      </div>
    </Panel>
  );
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [executions, setExecutions] = useState<AgentExecution[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);

        const [prospectsResponse, companiesResponse, executionsResponse] = await Promise.all([
          api.prospects.list({ page: 1, per_page: 100 }),
          api.companies.list({ page: 1, per_page: 50 }),
          api.enrichment.executions({ page: 1, per_page: 5 }),
        ]);

        const enrichedProspects = prospectsResponse.items.filter((item) => item.enrichment_status === "enriched").length;
        const pendingProspects = prospectsResponse.items.filter((item) => item.enrichment_status !== "enriched").length;

        setStats({
          totalProspects: prospectsResponse.total,
          enrichedProspects,
          pendingProspects,
          totalCompanies: companiesResponse.total,
        });
        setExecutions(executionsResponse.items);
        setError(null);
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : "Failed to load dashboard.");
      } finally {
        setLoading(false);
      }
    };

    void load();
  }, []);

  return (
    <div className="space-y-6 reveal-animation">
      <PageHeader
        eyebrow="Overview"
        title="Operational overview"
        description="A cleaner, denser dashboard for daily CRM operations. Use it to jump into the standardized prospect and company workspaces."
      />

      {error ? <FeedbackBanner tone="error" message={error} /> : null}

      <div className="grid gap-4 xl:grid-cols-4">
        <StatCard
          label="Prospects"
          value={loading ? "--" : formatRelativeCount(stats?.totalProspects)}
          helper="Total people records in the workspace"
          icon={Users}
        />
        <StatCard
          label="Enriched"
          value={loading ? "--" : formatRelativeCount(stats?.enrichedProspects)}
          helper="Prospects with completed enrichment"
          icon={Zap}
        />
        <StatCard
          label="Pending"
          value={loading ? "--" : formatRelativeCount(stats?.pendingProspects)}
          helper="Records still waiting on enrichment"
          icon={Radar}
        />
        <StatCard
          label="Companies"
          value={loading ? "--" : formatRelativeCount(stats?.totalCompanies)}
          helper="Tracked accounts in the monitoring workspace"
          icon={Building2}
        />
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
        <Panel className="p-6">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-[var(--color-text-subtle)]">Recent enrichment runs</p>
              <h2 className="mt-2 text-xl font-semibold tracking-[-0.03em] text-[var(--color-text)]">Latest workflow activity</h2>
            </div>
            <Link href="/dashboard/enrichment" className="inline-flex items-center gap-2 text-sm font-semibold text-[var(--color-accent)]">
              Open enrichment
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>

          <div className="mt-6 space-y-3">
            {executions.length > 0 ? executions.map((execution) => (
              <div
                key={execution.execution_id}
                className="flex flex-col gap-3 rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface-subtle)] p-4 sm:flex-row sm:items-center sm:justify-between"
              >
                <div>
                  <p className="font-semibold text-[var(--color-text)]">{execution.agent_type} runner</p>
                  <p className="mt-1 text-sm text-[var(--color-text-muted)]">
                    {execution.decision_description || "Recent enrichment decision completed in the shared workspace."}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <StatusBadge
                    status={execution.status === "success" ? "active" : execution.status === "running" ? "enriching" : "failed"}
                    label={execution.status}
                  />
                  <span className="text-sm text-[var(--color-text-muted)]">
                    {execution.duration_ms ? `${(execution.duration_ms / 1000).toFixed(1)}s` : "In progress"}
                  </span>
                </div>
              </div>
            )) : (
              <div className="rounded-2xl border border-dashed border-[var(--color-border)] bg-[var(--color-surface-subtle)] px-5 py-10 text-center text-sm text-[var(--color-text-muted)]">
                No executions yet. Start from the prospects table to trigger enrichment.
              </div>
            )}
          </div>
        </Panel>

        <Panel className="p-6">
          <p className="text-xs font-semibold uppercase tracking-[0.12em] text-[var(--color-text-subtle)]">Workspace standard</p>
          <h2 className="mt-2 text-xl font-semibold tracking-[-0.03em] text-[var(--color-text)]">What changed in this takeover</h2>
          <div className="mt-6 space-y-4 text-sm text-[var(--color-text-muted)]">
            <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface-subtle)] p-4">
              Centralized auth and guarded dashboard access now replace page-by-page token checks.
            </div>
            <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface-subtle)] p-4">
              Prospects and Companies now share the same data-grid shell, toolbar, selection model, and pagination pattern.
            </div>
            <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface-subtle)] p-4">
              Local reloads and alerts have been replaced with inline feedback and local state refreshes.
            </div>
          </div>
        </Panel>
      </div>
    </div>
  );
}
