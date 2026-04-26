"use client";

import { useState } from "react";
import { Bell, Database, Globe, Key, Lock, Save, Shield, User } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { FeedbackBanner } from "@/components/ui/FeedbackBanner";
import { Input } from "@/components/ui/Input";
import { PageHeader } from "@/components/ui/PageHeader";
import { Panel } from "@/components/ui/Panel";
import { cn } from "@/lib/utils";

const tabs = [
  { id: "general", name: "Profile & account", icon: User, description: "Personal identity and workspace defaults" },
  { id: "notifications", name: "Notifications", icon: Bell, description: "Signal delivery and alert preferences" },
  { id: "security", name: "Security", icon: Shield, description: "Authentication and access posture" },
  { id: "api", name: "API & connections", icon: Key, description: "Integration and API key management" },
  { id: "data", name: "Data controls", icon: Database, description: "Data handling and export rules" },
] as const;

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<(typeof tabs)[number]["id"]>("general");
  const [saved, setSaved] = useState(false);

  const active = tabs.find((tab) => tab.id === activeTab)!;

  return (
    <div className="space-y-6 reveal-animation">
      <PageHeader
        eyebrow="Settings"
        title="Workspace configuration"
        description="A cleaner enterprise settings surface aligned with the rest of the operating system."
      />

      {saved ? <FeedbackBanner tone="success" message="Settings saved locally for this UI standardization pass." /> : null}

      <div className="grid gap-6 xl:grid-cols-[320px_minmax(0,1fr)]">
        <Panel className="p-4">
          <p className="px-3 text-xs font-semibold uppercase tracking-[0.12em] text-[var(--color-text-subtle)]">Preference areas</p>
          <div className="mt-4 space-y-1">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={cn(
                  "flex w-full items-start gap-3 rounded-2xl px-3 py-3 text-left transition",
                  activeTab === tab.id
                    ? "border border-[var(--color-accent-border)] bg-[var(--color-accent-soft)] text-[var(--color-accent)]"
                    : "text-[var(--color-text-muted)] hover:bg-[var(--color-surface-subtle)] hover:text-[var(--color-text)]",
                )}
              >
                <div className="rounded-xl border border-[var(--color-border)] bg-white p-2">
                  <tab.icon className="h-4 w-4" />
                </div>
                <div>
                  <p className="text-sm font-semibold">{tab.name}</p>
                  <p className="mt-1 text-sm opacity-80">{tab.description}</p>
                </div>
              </button>
            ))}
          </div>
        </Panel>

        <Panel className="p-6">
          <p className="text-xs font-semibold uppercase tracking-[0.12em] text-[var(--color-text-subtle)]">{active.name}</p>
          <h2 className="mt-2 text-2xl font-semibold tracking-[-0.03em] text-[var(--color-text)]">{active.description}</h2>

          {activeTab === "general" ? (
            <div className="mt-6 grid gap-6 lg:grid-cols-2">
              <div className="space-y-4">
                <Input defaultValue="Puneet Shivhare" placeholder="Full name" />
                <Input defaultValue="Growth Intelligence Officer" placeholder="Role" />
              </div>
              <div className="space-y-4">
                <div className="flex items-center rounded-xl border border-[var(--color-border-strong)] bg-white px-3.5 py-2.5">
                  <span className="mr-2 text-sm text-[var(--color-text-subtle)]">agent.crm/</span>
                  <input defaultValue="puneet-alpha" className="w-full border-none bg-transparent text-sm font-medium text-[var(--color-text)] outline-none" />
                </div>
                <div className="flex items-center gap-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-subtle)] px-4 py-3 text-sm text-[var(--color-text-muted)]">
                  <Globe className="h-4 w-4 text-[var(--color-accent)]" />
                  English (United States)
                </div>
              </div>
            </div>
          ) : activeTab === "notifications" ? (
            <div className="mt-6 space-y-4">
              {[
                "Email digests for agent completions",
                "Browser push notifications for high lead scores",
                "Weekly automation performance reports",
                "Real-time alerts for enrichment errors"
              ].map((label, i) => (
                <div key={i} className="flex items-center justify-between rounded-xl border border-[var(--color-border)] bg-white p-4">
                  <span className="text-sm font-medium text-[var(--color-text)]">{label}</span>
                  <div className="h-5 w-10 rounded-full bg-[var(--color-accent)] p-1">
                    <div className="h-3 w-3 translate-x-5 rounded-full bg-white transition" />
                  </div>
                </div>
              ))}
            </div>
          ) : activeTab === "security" ? (
            <div className="mt-6 space-y-6">
              <div className="grid gap-4 lg:grid-cols-2">
                <div className="space-y-4">
                  <p className="text-sm font-semibold text-[var(--color-text)]">Change password</p>
                  <Input type="password" placeholder="Current password" />
                  <Input type="password" placeholder="New password" />
                  <Input type="password" placeholder="Confirm new password" />
                </div>
                <div className="space-y-4">
                  <p className="text-sm font-semibold text-[var(--color-text)]">Two-factor authentication</p>
                  <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-subtle)] p-4">
                    <p className="text-sm text-[var(--color-text-muted)]">2FA is currently disabled. Protect your account with an additional security layer.</p>
                    <Button variant="secondary" className="mt-3 w-full">Enable 2FA</Button>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="mt-6 rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface-subtle)] p-5">
              <div className="flex items-start gap-3">
                <Lock className="mt-0.5 h-5 w-5 text-[var(--color-accent)]" />
                <div>
                  <p className="font-semibold text-[var(--color-text)]">Enterprise access required.</p>
                  <p className="mt-1 text-sm text-[var(--color-text-muted)]">
                    The {active.name.toLowerCase()} controls are available on Enterprise plans. Contact your administrator to upgrade your workspace.
                  </p>
                </div>
              </div>
            </div>
          )}

          <div className="mt-8 flex justify-end">
            <Button onClick={() => setSaved(true)}>
              <Save className="h-4 w-4" />
              Save settings
            </Button>
          </div>
        </Panel>
      </div>
    </div>
  );
}
