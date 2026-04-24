import { AlertCircle, CheckCircle2, Info } from "lucide-react";
import { cn } from "@/lib/utils";

const toneMap = {
  error: {
    icon: AlertCircle,
    className: "border-[var(--color-danger-border)] bg-[var(--color-danger-soft)] text-[var(--color-danger)]",
  },
  success: {
    icon: CheckCircle2,
    className: "border-[var(--color-success-border)] bg-[var(--color-success-soft)] text-[var(--color-success)]",
  },
  info: {
    icon: Info,
    className: "border-[var(--color-border-strong)] bg-[var(--color-surface-subtle)] text-[var(--color-text-muted)]",
  },
} as const;

export function FeedbackBanner({
  tone = "info",
  message,
  className,
}: {
  tone?: keyof typeof toneMap;
  message: string;
  className?: string;
}) {
  const config = toneMap[tone];
  const Icon = config.icon;

  return (
    <div className={cn("flex items-start gap-3 rounded-2xl border px-4 py-3 text-sm font-medium", config.className, className)}>
      <Icon className="mt-0.5 h-4 w-4 shrink-0" />
      <span>{message}</span>
    </div>
  );
}
