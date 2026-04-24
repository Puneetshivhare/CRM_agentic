import { cn } from "@/lib/utils";

export function Panel({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section className={cn("rounded-3xl border border-[var(--color-border)] bg-white shadow-[var(--shadow-card)]", className)}>
      {children}
    </section>
  );
}
