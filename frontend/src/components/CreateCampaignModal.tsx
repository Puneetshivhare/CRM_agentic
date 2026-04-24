"use client";

import React, { useEffect, useState } from "react";
import { Mail, Plus, Send, Trash2, X } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { FeedbackBanner } from "@/components/ui/FeedbackBanner";
import { Input } from "@/components/ui/Input";
import type { SequenceStep } from "@/lib/types";

interface CreateCampaignModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (formData: { name: string; description: string; sequence_steps: SequenceStep[] }) => Promise<void>;
  loading: boolean;
}

const initialSteps: SequenceStep[] = [{ day: 0, subject: "", body: "" }];

export default function CreateCampaignModal({ isOpen, onClose, onSubmit, loading }: CreateCampaignModalProps) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [steps, setSteps] = useState<SequenceStep[]>(initialSteps);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) {
      setName("");
      setDescription("");
      setSteps(initialSteps);
      setError(null);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleAddStep = () => {
    setSteps((current) => [...current, { day: current.length * 2, subject: "", body: "" }]);
  };

  const handleRemoveStep = (index: number) => {
    setSteps((current) => (current.length === 1 ? current : current.filter((_, itemIndex) => itemIndex !== index)));
  };

  const handleStepChange = (index: number, field: keyof SequenceStep, value: string | number) => {
    setSteps((current) =>
      current.map((step, itemIndex) => (itemIndex === index ? { ...step, [field]: value } : step)),
    );
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);

    if (!name.trim()) {
      setError("Campaign name is required.");
      return;
    }

    if (steps.some((step) => !step.subject.trim() || !step.body.trim())) {
      setError("Each sequence step needs both a subject and a message body.");
      return;
    }

    try {
      await onSubmit({
        name: name.trim(),
        description: description.trim(),
        sequence_steps: steps,
      });
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Unable to create campaign.");
    }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-950/20 p-4 backdrop-blur-sm">
      <div className="w-full max-w-4xl rounded-[28px] border border-[var(--color-border)] bg-white shadow-[var(--shadow-elevated)]">
        <div className="flex items-start justify-between border-b border-[var(--color-border)] px-6 py-5">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.12em] text-[var(--color-text-subtle)]">New campaign</p>
            <h2 className="mt-2 text-2xl font-semibold tracking-[-0.03em] text-[var(--color-text)]">Create a messaging sequence</h2>
            <p className="mt-1 text-sm text-[var(--color-text-muted)]">Build a reusable outreach sequence with clear timing and message steps.</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-xl p-2 text-[var(--color-text-subtle)] transition hover:bg-[var(--color-surface-subtle)] hover:text-[var(--color-text)]"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6 px-6 py-6">
          <div className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
            <label className="grid gap-2">
              <span className="text-xs font-semibold uppercase tracking-[0.12em] text-[var(--color-text-subtle)]">Campaign name</span>
              <Input
                value={name}
                onChange={(event) => setName(event.target.value)}
                placeholder="Q2 Enterprise Growth"
              />
            </label>
            <label className="grid gap-2">
              <span className="text-xs font-semibold uppercase tracking-[0.12em] text-[var(--color-text-subtle)]">Description</span>
              <Input
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                placeholder="High-intent outbound sequence"
              />
            </label>
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.12em] text-[var(--color-text-subtle)]">Sequence steps</p>
                <p className="mt-1 text-sm text-[var(--color-text-muted)]">Define the touchpoints and delays used for enrollment.</p>
              </div>
              <Button type="button" variant="secondary" onClick={handleAddStep}>
                <Plus className="h-4 w-4" />
                Add step
              </Button>
            </div>

            <div className="space-y-4">
              {steps.map((step, index) => (
                <div key={index} className="rounded-3xl border border-[var(--color-border)] bg-[var(--color-surface-subtle)] p-5">
                  <div className="mb-4 flex items-center justify-between gap-4">
                    <div className="flex items-center gap-3">
                      <div className="flex h-9 w-9 items-center justify-center rounded-2xl border border-[var(--color-border)] bg-white text-sm font-semibold text-[var(--color-text)]">
                        {index + 1}
                      </div>
                      <span className="text-sm font-semibold text-[var(--color-text)]">Step {index + 1}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Input
                        type="number"
                        value={step.day}
                        onChange={(event) => handleStepChange(index, "day", parseInt(event.target.value || "0", 10))}
                        className="w-24"
                      />
                      <span className="text-sm text-[var(--color-text-muted)]">days</span>
                      {steps.length > 1 ? (
                        <Button type="button" variant="ghost" onClick={() => handleRemoveStep(index)}>
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      ) : null}
                    </div>
                  </div>

                  <div className="space-y-4">
                    <label className="grid gap-2">
                      <span className="text-xs font-semibold uppercase tracking-[0.12em] text-[var(--color-text-subtle)]">Subject</span>
                      <div className="relative">
                        <Mail className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--color-text-subtle)]" />
                        <Input
                          value={step.subject}
                          onChange={(event) => handleStepChange(index, "subject", event.target.value)}
                          placeholder="Thought this might help your team"
                          className="pl-10"
                        />
                      </div>
                    </label>
                    <label className="grid gap-2">
                      <span className="text-xs font-semibold uppercase tracking-[0.12em] text-[var(--color-text-subtle)]">Message body</span>
                      <textarea
                        value={step.body}
                        onChange={(event) => handleStepChange(index, "body", event.target.value)}
                        placeholder="Write the message body for this touchpoint."
                        rows={4}
                        className="w-full rounded-2xl border border-[var(--color-border-strong)] bg-white px-3.5 py-3 text-sm text-[var(--color-text)] outline-none transition placeholder:text-[var(--color-text-subtle)] focus:border-[var(--color-accent)] focus:ring-4 focus:ring-[var(--color-accent-ring)]"
                      />
                    </label>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {error ? <FeedbackBanner tone="error" message={error} /> : null}

          <div className="flex flex-col-reverse gap-2 border-t border-[var(--color-border)] pt-4 sm:flex-row sm:justify-end">
            <Button type="button" variant="secondary" onClick={onClose} disabled={loading}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? "Creating..." : (
                <>
                  <Send className="h-4 w-4" />
                  Create campaign
                </>
              )}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
