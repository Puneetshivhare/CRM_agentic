"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

export const Input = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  function Input({ className, ...props }, ref) {
    return (
      <input
        ref={ref}
        className={cn(
          "w-full rounded-xl border border-[var(--color-border-strong)] bg-white px-3.5 py-2.5 text-sm text-[var(--color-text)] outline-none transition placeholder:text-[var(--color-text-subtle)] focus:border-[var(--color-accent)] focus:ring-4 focus:ring-[var(--color-accent-ring)] disabled:cursor-not-allowed disabled:bg-[var(--color-surface-subtle)]",
          className,
        )}
        {...props}
      />
    );
  },
);
