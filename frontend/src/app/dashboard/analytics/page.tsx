"use client";

import { useEffect, useState } from "react";
import { Activity, Building2, Clock3, TrendingUp, Users, Zap } from "lucide-react";
import { FeedbackBanner } from "@/components/ui/FeedbackBanner";
import { PageHeader } from "@/components/ui/PageHeader";
import { Panel } from "@/components/ui/Panel";
import api from "@/lib/api";
import { formatRelativeCount } from "@/lib/format";

interface AnalyticsSummary {
  executionCount: number;
  avgDurationMs: number;
  companies: number;
  prospects: number;
  successRate: number;
}

function Metric({
  title,
  value,
  helper,
  icon: Icon,
}: {
  title: string;
  value: string;
  helper: string;
  icon: React.ComponentType<{ className?: string }>;
}) {
  return (
    <Panel className="p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.12em] text-[var(--color-text-subtle)]">{title}</p>
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

export default function AnalyticsPage() {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const [executions, prospects, companies] = await Promise.all([
          api.enrichment.executions({ page: 1, per_page: 100 }),
          api.prospects.list({ page: 1, per_page: 100 }),
          api.companies.list({ page: 1, per_page: 100 }),
        ]);

        const executionItems = executions.items;
        const successCount = executionItems.filter((item) => item.status === "success").length;
        const averageDuration = executionItems.length
          ? executionItems.reduce((accumulator, item) => accumulator + (item.duration_ms || 0), 0) / executionItems.length
          : 0;

        setSummary({
          executionCount: executionItems.length,
          avgDurationMs: averageDuration,
          companies: companies.total,
          prospects: prospects.total,
          successRate: executionItems.length ? (successCount / executionItems.length) * 100 : 0,
        });
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : "Failed to load analytics.");
      }
    };

    void load();
  }, []);

  return (
    <div className="space-y-6 reveal-animation">
      <PageHeader
        eyebrow="Analytics"
        title="Workspace analytics"
        description="A lightweight analytics page that stays aligned with the enterprise shell while deeper charting is deferred to a later phase."
      />

      {error ? <FeedbackBanner tone="error" message={error} /> : null}

      <div className="grid gap-4 xl:grid-cols-5">
        <Metric
          title="Executions"
          value={formatRelativeCount(summary?.executionCount)}
          helper="Tracked enrichment executions"
          icon={Activity}
        />
        <Metric
          title="Success rate"
          value={`${summary?.successRate.toFixed(1) ?? "0.0"}%`}
          helper="Completed runs that finished successfully"
          icon={TrendingUp}
        />
        <Metric
          title="Avg duration"
          value={`${Math.round(summary?.avgDurationMs ?? 0)}ms`}
          helper="Average execution latency"
          icon={Clock3}
        />
        <Metric
          title="Prospects"
          value={formatRelativeCount(summary?.prospects)}
          helper="Active prospect records"
          icon={Users}
        />
        <Metric
          title="Companies"
          value={formatRelativeCount(summary?.companies)}
          helper="Tracked company records"
          icon={Building2}
        />
      </div>

      <Panel className="p-6">
        <p className="text-xs font-semibold uppercase tracking-[0.12em] text-[var(--color-text-subtle)]">Next analytics phase</p>
        <h2 className="mt-2 text-xl font-semibold tracking-[-0.03em] text-[var(--color-text)]">Planned enterprise follow-up</h2>
        <div className="mt-6 grid gap-4 md:grid-cols-3">
          {[
            "Reusable chart primitives that match the same visual standard as the table workspace.",
            "Deeper funnel, enrichment, and monitoring trend analysis from centralized query hooks.",
            "Analytics views that inherit the same app shell, feedback banners, and panel system already used elsewhere.",
          ].map((item) => (
            <div key={item} className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface-subtle)] p-4 text-sm text-[var(--color-text-muted)]">
              <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-xl border border-[var(--color-border)] bg-white">
                <Zap className="h-4 w-4 text-[var(--color-accent)]" />
              </div>
              {item}
            </div>
          ))}
        </div>
      </Panel>
    </div>
  );
}
