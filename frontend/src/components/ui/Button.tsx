"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";

const variantClasses: Record<ButtonVariant, string> = {
  primary: "bg-[var(--color-accent)] text-white shadow-sm hover:bg-[var(--color-accent-strong)] border border-[var(--color-accent)]",
  secondary: "bg-white text-[var(--color-text)] border border-[var(--color-border-strong)] hover:bg-[var(--color-surface-subtle)]",
  ghost: "bg-transparent text-[var(--color-text-muted)] border border-transparent hover:bg-[var(--color-surface-subtle)] hover:text-[var(--color-text)]",
  danger: "bg-[var(--color-danger-soft)] text-[var(--color-danger)] border border-[var(--color-danger-border)] hover:bg-[#fee2e2]",
};

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { className, variant = "primary", children, ...props },
  ref,
) {
  return (
    <button
      ref={ref}
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-60",
        variantClasses[variant],
        className,
      )}
      {...props}
    >
      {children}
    </button>
  );
});
