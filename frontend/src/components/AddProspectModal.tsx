"use client";

import React, { useEffect, useState } from "react";
import { Briefcase, Mail, User, X } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { FeedbackBanner } from "@/components/ui/FeedbackBanner";
import { Input } from "@/components/ui/Input";

interface AddProspectModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: { first_name: string; last_name?: string; email: string; title?: string }) => Promise<void> | void;
  loading?: boolean;
}

const initialState = {
  first_name: "",
  last_name: "",
  email: "",
  title: "",
};

export default function AddProspectModal({ isOpen, onClose, onSubmit, loading }: AddProspectModalProps) {
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

    if (!formData.first_name.trim()) {
      setError("First name is required.");
      return;
    }

    if (!formData.email.includes("@")) {
      setError("Enter a valid work email.");
      return;
    }

    try {
      await onSubmit({
        first_name: formData.first_name.trim(),
        last_name: formData.last_name.trim() || undefined,
        email: formData.email.trim(),
        title: formData.title.trim() || undefined,
      });
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Unable to create prospect.");
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-950/20 p-4 backdrop-blur-sm">
      <div className="w-full max-w-xl rounded-[28px] border border-[var(--color-border)] bg-white shadow-[var(--shadow-elevated)]">
        <div className="flex items-start justify-between border-b border-[var(--color-border)] px-6 py-5">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.12em] text-[var(--color-text-subtle)]">New prospect</p>
            <h2 className="mt-2 text-2xl font-semibold tracking-[-0.03em] text-[var(--color-text)]">Create a prospect record</h2>
            <p className="mt-1 text-sm text-[var(--color-text-muted)]">Add a person to the shared revenue workspace and queue them for enrichment.</p>
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
          <div className="grid gap-4 sm:grid-cols-2">
            <label className="grid gap-2">
              <span className="text-xs font-semibold uppercase tracking-[0.12em] text-[var(--color-text-subtle)]">First name</span>
              <div className="relative">
                <User className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--color-text-subtle)]" />
                <Input
                  value={formData.first_name}
                  onChange={(event) => setFormData((current) => ({ ...current, first_name: event.target.value }))}
                  placeholder="Avery"
                  className="pl-10"
                />
              </div>
            </label>

            <label className="grid gap-2">
              <span className="text-xs font-semibold uppercase tracking-[0.12em] text-[var(--color-text-subtle)]">Last name</span>
              <Input
                value={formData.last_name}
                onChange={(event) => setFormData((current) => ({ ...current, last_name: event.target.value }))}
                placeholder="Morgan"
              />
            </label>
          </div>

          <label className="grid gap-2">
            <span className="text-xs font-semibold uppercase tracking-[0.12em] text-[var(--color-text-subtle)]">Work email</span>
            <div className="relative">
              <Mail className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--color-text-subtle)]" />
              <Input
                type="email"
                value={formData.email}
                onChange={(event) => setFormData((current) => ({ ...current, email: event.target.value }))}
                placeholder="avery@company.com"
                className="pl-10"
              />
            </div>
          </label>

          <label className="grid gap-2">
            <span className="text-xs font-semibold uppercase tracking-[0.12em] text-[var(--color-text-subtle)]">Role</span>
            <div className="relative">
              <Briefcase className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--color-text-subtle)]" />
              <Input
                value={formData.title}
                onChange={(event) => setFormData((current) => ({ ...current, title: event.target.value }))}
                placeholder="VP of Sales"
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
              {loading ? "Creating..." : "Create prospect"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
