"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  Building2,
  LayoutDashboard,
  LogOut,
  Mail,
  Settings,
  Sparkles,
  Users,
  Workflow,
  Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/contexts/AuthContext";

const navItems = [
  { name: "Overview", icon: LayoutDashboard, href: "/dashboard" },
  { name: "Prospects", icon: Users, href: "/dashboard/prospects" },
  { name: "Companies", icon: Building2, href: "/dashboard/companies" },
  { name: "Campaigns", icon: Mail, href: "/dashboard/campaigns" },
  { name: "Enrichment", icon: Sparkles, href: "/dashboard/enrichment" },
  { name: "Rules", icon: Workflow, href: "/dashboard/rules" },
  { name: "Analytics", icon: BarChart3, href: "/dashboard/analytics" },
  { name: "Settings", icon: Settings, href: "/dashboard/settings" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { logout, user } = useAuth();

  return (
    <div className="flex h-full flex-col bg-white">
      <div className="flex h-[72px] items-center px-6">
        <Link href="/dashboard/prospects" className="group flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-[var(--color-accent)] shadow-sm">
            <Zap className="h-4 w-4 fill-white text-white" />
          </div>
          <span className="font-display text-lg font-bold tracking-tight text-[var(--color-text)]">
            Agentic<span className="text-[var(--color-accent)]">CRM</span>
          </span>
        </Link>
      </div>

      <div className="px-6 pb-5">
        <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface-subtle)] px-4 py-3">
          <p className="text-xs font-semibold uppercase tracking-[0.12em] text-[var(--color-text-subtle)]">Workspace</p>
          <p className="mt-2 truncate text-sm font-semibold text-[var(--color-text)]">{user?.email ?? "No active session"}</p>
          <p className="mt-1 text-sm text-[var(--color-text-muted)]">Clay-style operating system for revenue teams.</p>
        </div>
      </div>

      <nav className="flex-1 space-y-6 overflow-y-auto px-4 pb-6 no-scrollbar">
        <div>
          <div className="mb-2 px-3 text-xs font-semibold uppercase tracking-[0.12em] text-[var(--color-text-subtle)]">
            Workspace
          </div>
          <div className="space-y-1">
            {navItems.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex items-center gap-3 rounded-2xl px-3 py-3 transition",
                    isActive
                      ? "border border-[var(--color-accent-border)] bg-[var(--color-accent-soft)] text-[var(--color-accent)] shadow-sm"
                      : "text-[var(--color-text-muted)] hover:bg-[var(--color-surface-subtle)] hover:text-[var(--color-text)]",
                  )}
                >
                  <item.icon className={cn("h-4 w-4", isActive ? "text-[var(--color-accent)]" : "text-[var(--color-text-subtle)]")} />
                  <span className="text-sm font-medium">{item.name}</span>
                </Link>
              );
            })}
          </div>
        </div>

        <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface-subtle)] px-4 py-4">
          <p className="text-xs font-semibold uppercase tracking-[0.12em] text-[var(--color-text-subtle)]">Current focus</p>
          <p className="mt-2 text-sm font-semibold text-[var(--color-text)]">Enterprise data workspace</p>
          <p className="mt-1 text-sm text-[var(--color-text-muted)]">
            Prospects and companies now share one standard operating model.
          </p>
        </div>
      </nav>

      <div className="border-t border-[var(--color-border)] p-4">
        <button
          className="group flex w-full items-center gap-3 rounded-2xl px-3 py-3 text-sm font-medium text-[var(--color-text-muted)] transition hover:bg-[var(--color-danger-soft)] hover:text-[var(--color-danger)]"
          onClick={() => {
            logout();
            window.location.href = "/login";
          }}
        >
          <LogOut className="h-4 w-4 text-[var(--color-text-subtle)] transition group-hover:text-[var(--color-danger)]" />
          <span>Sign Out</span>
        </button>
      </div>
    </div>
  );
}
