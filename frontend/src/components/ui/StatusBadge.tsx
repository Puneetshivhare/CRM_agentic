import { AlertCircle, CheckCircle2, Clock3, LoaderCircle, Zap } from "lucide-react";
import { cn } from "@/lib/utils";

const badgeMap = {
  enriched: { label: "Enriched", icon: CheckCircle2, className: "bg-[var(--color-success-soft)] text-[var(--color-success)] border-[var(--color-success-border)]" },
  pending: { label: "Queued", icon: Clock3, className: "bg-[var(--color-surface-subtle)] text-[var(--color-text-muted)] border-[var(--color-border)]" },
  enriching: { label: "Enriching", icon: LoaderCircle, className: "bg-[var(--color-accent-soft)] text-[var(--color-accent)] border-[var(--color-accent-border)]" },
  failed: { label: "Failed", icon: AlertCircle, className: "bg-[var(--color-danger-soft)] text-[var(--color-danger)] border-[var(--color-danger-border)]" },
  active: { label: "Active", icon: Zap, className: "bg-[var(--color-success-soft)] text-[var(--color-success)] border-[var(--color-success-border)]" },
  paused: { label: "Paused", icon: Clock3, className: "bg-[var(--color-surface-subtle)] text-[var(--color-text-muted)] border-[var(--color-border)]" },
} as const;

export function StatusBadge({
  status,
  label,
}: {
  status: keyof typeof badgeMap;
  label?: string;
}) {
  const config = badgeMap[status];
  const Icon = config.icon;

  return (
    <span className={cn("inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold", config.className)}>
      <Icon className={cn("h-3.5 w-3.5", status === "enriching" ? "animate-spin" : "")} />
      {label ?? config.label}
    </span>
  );
}
