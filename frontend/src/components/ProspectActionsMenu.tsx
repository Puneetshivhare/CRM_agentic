"use client";

import React, { useEffect, useRef, useState } from "react";
import { Copy, MoreHorizontal, Trash2, Zap } from "lucide-react";
import { Button } from "@/components/ui/Button";

interface ProspectActionsMenuProps {
  prospectId: number;
  email?: string;
  firstName?: string;
  onEnrich: (prospectId: number) => Promise<void>;
  onDelete: (prospectId: number) => Promise<void>;
  isEnriching: boolean;
}

export default function ProspectActionsMenu({
  prospectId,
  email,
  firstName,
  onEnrich,
  onDelete,
  isEnriching,
}: ProspectActionsMenuProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleCopyEmail = async () => {
    if (!email) return;
    await navigator.clipboard.writeText(email);
    setIsOpen(false);
  };

  const handleDelete = async () => {
    if (!window.confirm(`Delete ${firstName || "this prospect"} from the workspace?`)) return;
    setIsDeleting(true);

    try {
      await onDelete(prospectId);
      setIsOpen(false);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="relative inline-flex justify-end" ref={menuRef}>
      <Button variant="ghost" className="h-9 px-3" onClick={() => setIsOpen((current) => !current)}>
        <MoreHorizontal className="h-4 w-4" />
      </Button>

      {isOpen ? (
        <div className="absolute right-0 top-full z-20 mt-2 w-52 rounded-2xl border border-[var(--color-border)] bg-white p-1.5 shadow-[var(--shadow-elevated)]">
          <button
            type="button"
            onClick={handleCopyEmail}
            disabled={!email}
            className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm text-[var(--color-text-muted)] transition hover:bg-[var(--color-surface-subtle)] hover:text-[var(--color-text)] disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Copy className="h-4 w-4" />
            Copy email
          </button>
          <button
            type="button"
            onClick={() => onEnrich(prospectId).then(() => setIsOpen(false))}
            disabled={isEnriching}
            className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm text-[var(--color-accent)] transition hover:bg-[var(--color-accent-soft)] disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Zap className="h-4 w-4" />
            {isEnriching ? "Enriching..." : "Trigger enrichment"}
          </button>
          <button
            type="button"
            onClick={handleDelete}
            disabled={isDeleting}
            className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm text-[var(--color-danger)] transition hover:bg-[var(--color-danger-soft)] disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Trash2 className="h-4 w-4" />
            Delete prospect
          </button>
        </div>
      ) : null}
    </div>
  );
}
