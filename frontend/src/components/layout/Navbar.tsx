"use client";

import React from "react";
import { Bell, HelpCircle, Search, User } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { Input } from "@/components/ui/Input";

export default function Navbar() {
  const { user } = useAuth();

  return (
    <div className="flex h-[72px] items-center justify-between gap-4 px-4 sm:px-6">
      <div className="flex min-w-0 flex-1 items-center gap-4">
        <div className="hidden max-w-md flex-1 lg:block">
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--color-text-subtle)]" />
            <Input
              type="text"
              placeholder="Search prospects, companies, and workflows"
              className="pl-10"
            />
          </div>
        </div>
      </div>

      <div className="flex items-center gap-1 sm:gap-2">
        <button className="rounded-xl p-2 text-[var(--color-text-muted)] transition hover:bg-[var(--color-surface-subtle)] hover:text-[var(--color-text)]">
          <HelpCircle className="h-4 w-4" />
        </button>

        <button className="group relative rounded-xl p-2 text-[var(--color-text-muted)] transition hover:bg-[var(--color-surface-subtle)] hover:text-[var(--color-text)]">
          <Bell className="h-4 w-4" />
          <span className="absolute right-2 top-2 h-1.5 w-1.5 rounded-full border border-white bg-[var(--color-danger)]" />
        </button>

        <div className="mx-1 hidden h-5 w-px bg-[var(--color-border)] sm:block" />

        <button className="flex items-center gap-3 rounded-2xl border border-[var(--color-border)] bg-white px-2 py-1.5 transition hover:bg-[var(--color-surface-subtle)]">
          <div className="hidden text-right sm:block">
            <p className="text-sm font-semibold leading-none text-[var(--color-text)]">{user?.email ?? "Workspace user"}</p>
            <p className="mt-1 text-xs text-[var(--color-text-subtle)]">Authenticated session</p>
          </div>
          <div className="flex h-9 w-9 items-center justify-center overflow-hidden rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-subtle)]">
            <User className="h-4 w-4 text-[var(--color-text-muted)]" />
          </div>
        </button>
      </div>
    </div>
  );
}
