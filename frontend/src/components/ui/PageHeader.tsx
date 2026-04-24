import { Button } from "@/components/ui/Button";

export function PageHeader({
  eyebrow,
  title,
  description,
  actions,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  actions?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-4 border-b border-[var(--color-border)] pb-6 lg:flex-row lg:items-end lg:justify-between">
      <div className="space-y-1.5">
        {eyebrow ? <p className="text-xs font-semibold uppercase tracking-[0.12em] text-[var(--color-text-subtle)]">{eyebrow}</p> : null}
        <h1 className="text-3xl font-semibold tracking-[-0.03em] text-[var(--color-text)]">{title}</h1>
        {description ? <p className="max-w-2xl text-sm text-[var(--color-text-muted)]">{description}</p> : null}
      </div>
      {actions ? <div className="flex flex-wrap items-center gap-2">{actions}</div> : null}
    </div>
  );
}

export function PageHeaderActionGroup({ children }: { children: React.ReactNode }) {
  return <div className="flex flex-wrap items-center gap-2">{children}</div>;
}

export { Button };
