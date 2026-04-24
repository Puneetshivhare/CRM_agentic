"use client";

import React, { useEffect, useState } from "react";
import { Building2, Globe, TrendingUp, Users, X } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { FeedbackBanner } from "@/components/ui/FeedbackBanner";
import { Input } from "@/components/ui/Input";

interface AddCompanyModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: { name: string; domain?: string; industry?: string; headcount?: number; funding_stage?: string }) => Promise<void> | void;
  loading?: boolean;
}

const initialState = {
  name: "",
  domain: "",
  industry: "",
  headcount: "",
  funding_stage: "",
};

export default function AddCompanyModal({ isOpen, onClose, onSubmit, loading }: AddCompanyModalProps) {
  const [formData, setFormData] = useState(initialState);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!isOpen) {
      setFormData(initialState);
      setError("");
    }
  }, [isOpen]);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError("");

    if (!formData.name.trim()) {
      setError("Company name is required.");
      return;
    }

    try {
      await onSubmit({
        name: formData.name.trim(),
        domain: formData.domain.trim() || undefined,
        industry: formData.industry.trim() || undefined,
        headcount: formData.headcount ? parseInt(formData.headcount, 10) : undefined,
        funding_stage: formData.funding_stage.trim() || undefined,
      });
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Unable to create company.");
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-950/20 p-4 backdrop-blur-sm">
      <div className="w-full max-w-xl rounded-[28px] border border-[var(--color-border)] bg-white shadow-[var(--shadow-elevated)]">
        <div className="flex items-start justify-between border-b border-[var(--color-border)] px-6 py-5">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.12em] text-[var(--color-text-subtle)]">New company</p>
            <h2 className="mt-2 text-2xl font-semibold tracking-[-0.03em] text-[var(--color-text)]">Track an account</h2>
            <p className="mt-1 text-sm text-[var(--color-text-muted)]">Create a company record and include the operating context your team needs immediately.</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-xl p-2 text-[var(--color-text-subtle)] transition hover:bg-[var(--color-surface-subtle)] hover:text-[var(--color-text)]"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5 px-6 py-6">
          <label className="grid gap-2">
            <span className="text-xs font-semibold uppercase tracking-[0.12em] text-[var(--color-text-subtle)]">Company name</span>
            <div className="relative">
              <Building2 className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--color-text-subtle)]" />
              <Input
                value={formData.name}
                onChange={(event) => setFormData((current) => ({ ...current, name: event.target.value }))}
                placeholder="Acme Corporation"
                className="pl-10"
              />
            </div>
          </label>

          <div className="grid gap-4 sm:grid-cols-2">
            <label className="grid gap-2">
              <span className="text-xs font-semibold uppercase tracking-[0.12em] text-[var(--color-text-subtle)]">Domain</span>
              <div className="relative">
                <Globe className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--color-text-subtle)]" />
                <Input
                  value={formData.domain}
                  onChange={(event) => setFormData((current) => ({ ...current, domain: event.target.value }))}
                  placeholder="acme.com"
                  className="pl-10"
                />
              </div>
            </label>

            <label className="grid gap-2">
              <span className="text-xs font-semibold uppercase tracking-[0.12em] text-[var(--color-text-subtle)]">Headcount</span>
              <div className="relative">
                <Users className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--color-text-subtle)]" />
                <Input
                  type="number"
                  value={formData.headcount}
                  onChange={(event) => setFormData((current) => ({ ...current, headcount: event.target.value }))}
                  placeholder="250"
                  className="pl-10"
                />
              </div>
            </label>
          </div>

          <label className="grid gap-2">
            <span className="text-xs font-semibold uppercase tracking-[0.12em] text-[var(--color-text-subtle)]">Industry</span>
            <Input
              value={formData.industry}
              onChange={(event) => setFormData((current) => ({ ...current, industry: event.target.value }))}
              placeholder="Enterprise software"
            />
          </label>

          <label className="grid gap-2">
            <span className="text-xs font-semibold uppercase tracking-[0.12em] text-[var(--color-text-subtle)]">Funding stage</span>
            <div className="relative">
              <TrendingUp className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--color-text-subtle)]" />
              <Input
                value={formData.funding_stage}
                onChange={(event) => setFormData((current) => ({ ...current, funding_stage: event.target.value }))}
                placeholder="Series B"
                className="pl-10"
              />
            </div>
          </label>

          {error ? <FeedbackBanner tone="error" message={error} /> : null}

          <div className="flex flex-col-reverse gap-2 pt-2 sm:flex-row sm:justify-end">
            <Button type="button" variant="secondary" onClick={onClose} disabled={loading}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? "Creating..." : "Create company"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
