"use client";

import React, { useState, useRef, useEffect } from 'react';
import { Mail, Trash2, Zap, MoreHorizontal } from 'lucide-react';
import { cn } from '@/lib/utils';

const LinkedinIcon = ({ className }: { className?: string }) => (
  <svg 
    className={className}
    xmlns="http://www.w3.org/2000/svg" 
    viewBox="0 0 24 24" 
    fill="currentColor"
  >
    <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452z" />
  </svg>
);

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
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleEnrich = async () => {
    try {
      await onEnrich(prospectId);
      setIsOpen(false);
    } catch (err) {
      // Error handled in parent
    }
  };

  const handleDelete = async () => {
    if (!confirm(`Delete ${firstName || 'prospect'}?`)) return;
    try {
      setIsDeleting(true);
      await onDelete(prospectId);
      setIsOpen(false);
    } catch (err) {
      // Error handled in parent
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="relative" ref={menuRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          "p-2 rounded-xl border transition-all duration-200",
          isOpen 
            ? "bg-[#f3f4f6] border-[#e5e7eb] text-[#111827]" 
            : "bg-white border-transparent text-[#9ca3af] hover:text-[#111827] hover:bg-[#f9fafb] hover:border-[#e5e7eb]"
        )}
      >
        <MoreHorizontal className="w-4 h-4" />
      </button>

      {isOpen && (
        <div className="absolute right-0 top-full mt-2 bg-white border border-[#e5e7eb] rounded-2xl shadow-[0_12px_40px_-12px_rgba(0,0,0,0.12)] z-[100] w-56 overflow-hidden animate-in fade-in zoom-in-95 duration-200 origin-top-right">
          <div className="px-4 py-3 border-b border-[#f3f4f6] bg-[#fcfcfd]">
            <p className="text-[11px] font-bold text-[#9ca3af] uppercase tracking-wider">Prospect Actions</p>
          </div>
          
          <div className="p-1.5">
            <button
              onClick={() => {
                if (email) window.alert(`📧 Email: ${email}`);
                setIsOpen(false);
              }}
              className="w-full text-left px-3 py-2 text-sm text-[#4b5563] hover:text-[#111827] hover:bg-[#f9fafb] rounded-xl flex items-center gap-3 transition-colors"
            >
              <div className="w-8 h-8 rounded-lg bg-[#f0f9ff] flex items-center justify-center text-[#2563eb]">
                <Mail className="w-4 h-4" />
              </div>
              <span className="font-semibold">Copy Email</span>
            </button>

            <button
              onClick={() => {
                alert('🔗 LinkedIn integration coming soon');
                setIsOpen(false);
              }}
              className="w-full text-left px-3 py-2 text-sm text-[#4b5563] hover:text-[#111827] hover:bg-[#f9fafb] rounded-xl flex items-center gap-3 transition-colors"
            >
              <div className="w-8 h-8 rounded-lg bg-[#f0fdf4] flex items-center justify-center text-[#16a34a]">
                <LinkedinIcon className="w-4 h-4" />
              </div>
              <span className="font-semibold">LinkedIn Profile</span>
            </button>

            <button
              onClick={handleEnrich}
              disabled={isEnriching}
              className="w-full text-left px-3 py-2 text-sm text-[#2563eb] hover:bg-[#eff6ff] rounded-xl flex items-center gap-3 transition-colors disabled:opacity-50"
            >
              <div className="w-8 h-8 rounded-lg bg-[#2563eb] flex items-center justify-center text-white">
                <Zap className="w-4 h-4" />
              </div>
              <span className="font-bold">{isEnriching ? 'Enriching...' : 'Quick Enrich'}</span>
            </button>
          </div>

          <div className="p-1.5 border-t border-[#f3f4f6]">
            <button
              onClick={handleDelete}
              disabled={isDeleting}
              className="w-full text-left px-3 py-2 text-sm text-[#ef4444] hover:bg-[#fef2f2] rounded-xl flex items-center gap-3 transition-colors disabled:opacity-50"
            >
              <div className="w-8 h-8 rounded-lg bg-[#fef2f2] flex items-center justify-center text-[#ef4444]">
                <Trash2 className="w-4 h-4" />
              </div>
              <span className="font-bold">Delete Lead</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
