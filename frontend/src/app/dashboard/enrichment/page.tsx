"use client";

import { useEffect, useMemo, useState } from "react";
import { Activity, Bot, CheckCircle2, Cpu, ExternalLink, Search, ShieldCheck, Zap } from "lucide-react";
import { DataGrid, type DataGridColumn } from "@/components/data-grid/DataGrid";
import { DataGridToolbar } from "@/components/data-grid/DataGridToolbar";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { FeedbackBanner } from "@/components/ui/FeedbackBanner";
import { Input } from "@/components/ui/Input";
import { PageHeader } from "@/components/ui/PageHeader";
import { Panel } from "@/components/ui/Panel";
import { StatusBadge } from "@/components/ui/StatusBadge";
import api from "@/lib/api";
import { formatDate, formatRelativeCount } from "@/lib/format";
import type { AgentExecution, BrowserCandidate, BrowserSession, SearchResult } from "@/lib/types";

function Stat({
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

function CandidateCard({
  candidate,
  onAccept,
  accepting,
}: {
  candidate: BrowserCandidate;
  onAccept: (candidate: BrowserCandidate) => Promise<void>;
  accepting: boolean;
}) {
  return (
    <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface-subtle)] p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="font-semibold text-[var(--color-text)]">{candidate.title}</p>
          <a
            href={candidate.url}
            target="_blank"
            rel="noreferrer"
            className="mt-1 inline-flex max-w-full items-center gap-1 truncate text-sm text-[var(--color-accent)] hover:text-[var(--color-accent-strong)]"
          >
            <span className="truncate">{candidate.url}</span>
            <ExternalLink className="h-3.5 w-3.5 shrink-0" />
          </a>
          <p className="mt-2 text-sm text-[var(--color-text-muted)]">{candidate.snippet || "No snippet returned for this page."}</p>
        </div>
        <Button variant="secondary" onClick={() => void onAccept(candidate)} disabled={accepting}>
          {accepting ? "Saving..." : "Accept page"}
        </Button>
      </div>
    </div>
  );
}

function AcceptedResultCard({ result }: { result: SearchResult }) {
  return (
    <div className="rounded-2xl border border-[var(--color-success-border)] bg-[var(--color-success-soft)] p-4">
      <div className="flex items-start gap-3">
        <div className="mt-0.5 rounded-full bg-white/80 p-1 text-[var(--color-success)]">
          <CheckCircle2 className="h-4 w-4" />
        </div>
        <div className="min-w-0">
          <p className="font-semibold text-[var(--color-text)]">{result.title}</p>
          <a
            href={result.url}
            target="_blank"
            rel="noreferrer"
            className="mt-1 inline-flex max-w-full items-center gap-1 truncate text-sm text-[var(--color-accent)] hover:text-[var(--color-accent-strong)]"
          >
            <span className="truncate">{result.url}</span>
            <ExternalLink className="h-3.5 w-3.5 shrink-0" />
          </a>
          <p className="mt-2 text-sm text-[var(--color-text-muted)]">{result.text_preview || result.snippet}</p>
        </div>
      </div>
    </div>
  );
}

export default function EnrichmentPage() {
  const [executions, setExecutions] = useState<AgentExecution[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [browserQuery, setBrowserQuery] = useState("site:vercel.com Vercel leadership");
  const [browserSession, setBrowserSession] = useState<BrowserSession | null>(null);
  const [creatingSession, setCreatingSession] = useState(false);
  const [acceptingUrl, setAcceptingUrl] = useState<string | null>(null);

  const loadExecutions = async () => {
    try {
      setLoading(true);
      const response = await api.enrichment.executions({ page: 1, per_page: 50 });
      setExecutions(response.items);
      setError(null);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Failed to load execution history.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadExecutions();
  }, []);

  const handleCreateBrowserSession = async () => {
    try {
      setCreatingSession(true);
      const session = await api.search.createBrowserSession({
        query: browserQuery,
        limit: 4,
        mode: "analyst_assist",
      });
      setBrowserSession(session);
      setMessage(`Analyst assist session opened with ${session.candidates.length} candidate pages.`);
      setError(null);
      await loadExecutions();
    } catch (sessionError) {
      setError(sessionError instanceof Error ? sessionError.message : "Failed to start analyst assist.");
    } finally {
      setCreatingSession(false);
    }
  };

  const handleAcceptCandidate = async (candidate: BrowserCandidate) => {
    if (!browserSession) return;

    try {
      setAcceptingUrl(candidate.url);
      await api.search.acceptBrowserPage(browserSession.session_id, candidate);
      const refreshed = await api.search.getBrowserSession(browserSession.session_id);
      setBrowserSession(refreshed);
      setMessage(`Saved ${candidate.title} into the search memory and document store.`);
      setError(null);
      await loadExecutions();
    } catch (acceptError) {
      setError(acceptError instanceof Error ? acceptError.message : "Failed to accept the selected page.");
    } finally {
      setAcceptingUrl(null);
    }
  };

  const successCount = executions.filter((item) => item.status === "success").length;
  const avgConfidence = executions.length
    ? executions.reduce((sum, item) => sum + (item.confidence_score ?? 0), 0) / executions.length
    : 0;
  const avgDuration = executions.length
    ? executions.reduce((sum, item) => sum + (item.duration_ms ?? 0), 0) / executions.length
    : 0;

  const columns = useMemo<Array<DataGridColumn<AgentExecution>>>(() => [
    {
      id: "agent_type",
      header: "Agent",
      sortable: true,
      sortValue: (row) => row.agent_type,
      render: (row) => (
        <div>
          <p className="font-semibold text-[var(--color-text)]">{row.agent_type}</p>
          <p className="text-sm text-[var(--color-text-muted)]">{row.decision_description || "Autonomous enrichment execution"}</p>
        </div>
      ),
    },
    {
      id: "status",
      header: "Status",
      sortable: true,
      sortValue: (row) => row.status,
      render: (row) => (
        <StatusBadge
          status={row.status === "success" ? "active" : row.status === "running" ? "enriching" : "failed"}
          label={row.status}
        />
      ),
    },
    {
      id: "created_at",
      header: "Started",
      sortable: true,
      sortValue: (row) => new Date(row.start_time || row.created_at).getTime(),
      render: (row) => <span>{formatDate(row.start_time || row.created_at)}</span>,
    },
    {
      id: "duration_ms",
      header: "Duration",
      align: "right",
      sortable: true,
      sortValue: (row) => row.duration_ms,
      render: (row) => <span className="font-medium text-[var(--color-text)]">{row.duration_ms ? `${(row.duration_ms / 1000).toFixed(1)}s` : "In progress"}</span>,
    },
    {
      id: "confidence_score",
      header: "Confidence",
      align: "right",
      sortable: true,
      sortValue: (row) => row.confidence_score,
      render: (row) => <span className="font-medium text-[var(--color-text)]">{((row.confidence_score ?? 0) * 100).toFixed(0)}%</span>,
    },
  ], []);

  return (
    <div className="space-y-6 reveal-animation">
      <PageHeader
        eyebrow="Enrichment"
        title="Enrichment operations"
        description="Run browser-assisted research, review agent executions, and keep the search-to-enrichment loop visible while we harden automation."
      />

      {error ? <FeedbackBanner tone="error" message={error} /> : null}
      {message ? <FeedbackBanner tone="success" message={message} /> : null}

      <div className="grid gap-4 xl:grid-cols-4">
        <Stat title="Executions" value={formatRelativeCount(executions.length)} helper="Total tracked enrichment runs" icon={Activity} />
        <Stat title="Success" value={`${executions.length ? ((successCount / executions.length) * 100).toFixed(1) : "0.0"}%`} helper="Runs completed successfully" icon={ShieldCheck} />
        <Stat title="Confidence" value={`${(avgConfidence * 100).toFixed(0)}%`} helper="Average confidence score" icon={Cpu} />
        <Stat title="Avg duration" value={`${Math.round(avgDuration)}ms`} helper="Average run duration" icon={Zap} />
      </div>

      <Panel className="overflow-hidden">
        <div className="border-b border-[var(--color-border)] bg-[linear-gradient(135deg,rgba(15,23,42,0.03),rgba(14,165,233,0.08))] p-6">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-[var(--color-text-subtle)]">Analyst Assist</p>
              <h2 className="mt-2 text-2xl font-semibold tracking-[-0.03em] text-[var(--color-text)]">Open a browser-backed search session</h2>
              <p className="mt-2 max-w-3xl text-sm text-[var(--color-text-muted)]">
                Start with DuckDuckGo and Brave fallback in the backend, then review the discovered pages here before we promote them into live memory and automation.
              </p>
            </div>
            <div className="inline-flex items-center gap-2 rounded-full border border-[var(--color-border)] bg-white px-3 py-2 text-sm text-[var(--color-text-muted)]">
              <Bot className="h-4 w-4 text-[var(--color-accent)]" />
              Analyst assist stays human-guided
            </div>
          </div>
          <div className="mt-5 flex flex-col gap-3 lg:flex-row">
            <Input
              value={browserQuery}
              onChange={(event) => setBrowserQuery(event.target.value)}
              placeholder="Search query or site:domain operator"
              className="bg-white"
            />
            <Button onClick={() => void handleCreateBrowserSession()} disabled={creatingSession || !browserQuery.trim()} className="lg:min-w-52">
              <Search className="h-4 w-4" />
              {creatingSession ? "Opening session..." : "Open analyst assist"}
            </Button>
          </div>
        </div>

        <div className="grid gap-6 p-6 lg:grid-cols-[1.35fr_0.95fr]">
          <div className="space-y-4">
            <div className="flex items-center justify-between gap-3">
              <div>
                <h3 className="text-sm font-semibold uppercase tracking-[0.12em] text-[var(--color-text-subtle)]">Candidate Pages</h3>
                <p className="mt-1 text-sm text-[var(--color-text-muted)]">Review what the backend discovered before accepting it into documents and memory.</p>
              </div>
              {browserSession ? <StatusBadge status={browserSession.accepted_results.length ? "active" : "pending"} label={browserSession.status} /> : null}
            </div>

            {browserSession ? (
              <div className="space-y-3">
                {browserSession.candidates.map((candidate) => (
                  <CandidateCard
                    key={candidate.url}
                    candidate={candidate}
                    accepting={acceptingUrl === candidate.url}
                    onAccept={handleAcceptCandidate}
                  />
                ))}
                {!browserSession.candidates.length ? (
                  <EmptyState title="No candidates yet" description="Try a broader query or use a `site:` operator for a company domain." />
                ) : null}
              </div>
            ) : (
              <EmptyState title="Start a browser session" description="Enter a query above to discover pages the analyst can approve for downstream automation." />
            )}
          </div>

          <div className="space-y-4">
            <div>
              <h3 className="text-sm font-semibold uppercase tracking-[0.12em] text-[var(--color-text-subtle)]">Accepted Pages</h3>
              <p className="mt-1 text-sm text-[var(--color-text-muted)]">These pages have been crawled and stored for agents to reuse later.</p>
            </div>

            {browserSession ? (
              <Panel className="p-4">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-[var(--color-text)]">{browserSession.query}</p>
                    <p className="mt-1 text-xs text-[var(--color-text-muted)]">Session {browserSession.session_id.slice(0, 8)} • {formatDate(browserSession.created_at)}</p>
                  </div>
                  <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface-subtle)] px-3 py-2 text-sm text-[var(--color-text-muted)]">
                    {browserSession.accepted_results.length} accepted
                  </div>
                </div>
              </Panel>
            ) : null}

            {browserSession?.accepted_results.length ? (
              <div className="space-y-3">
                {browserSession.accepted_results.map((result) => (
                  <AcceptedResultCard key={`${result.document_id}-${result.url}`} result={result} />
                ))}
              </div>
            ) : (
              <EmptyState title="No accepted pages" description="Accepted pages will appear here once you approve a candidate from the analyst assist lane." />
            )}
          </div>
        </div>
      </Panel>

      <DataGridToolbar
        searchValue=""
        onSearchChange={() => undefined}
        searchPlaceholder="Execution search will be added in the next phase"
        actionSlot={<div className="rounded-xl border border-[var(--color-border)] bg-white px-3 py-2 text-sm text-[var(--color-text-muted)]">{executions.length} recent executions</div>}
      />

      <DataGrid
        columns={columns}
        rows={executions}
        rowKey={(row) => row.execution_id}
        loading={loading}
        loadingLabel="Loading execution history..."
        emptyState={<EmptyState title="No enrichment history" description="Trigger enrichment from the prospects workspace to populate this operational log." />}
      />
    </div>
  );
}
