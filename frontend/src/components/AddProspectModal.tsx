"use client";

import React, { useState } from 'react';
import { X, User, Mail, Briefcase, Plus } from 'lucide-react';

interface AddProspectModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: { first_name: string; last_name?: string; email: string; title?: string }) => void;
  loading?: boolean;
}

export default function AddProspectModal({ isOpen, onClose, onSubmit, loading }: AddProspectModalProps) {
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    title: '',
  });
  const [error, setError] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!formData.first_name.trim()) {
      setError('First name is required');
      return;
    }
    if (!formData.email.trim()) {
      setError('Email is required');
      return;
    }
    if (!formData.email.includes('@')) {
      setError('Please enter a valid email');
      return;
    }

    onSubmit({
      first_name: formData.first_name,
      last_name: formData.last_name || undefined,
      email: formData.email,
      title: formData.title || undefined,
    });

    setFormData({ first_name: '', last_name: '', email: '', title: '' });
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/30 backdrop-blur-[2px] flex items-center justify-center z-[100] p-4 animate-in fade-in duration-300">
      <div className="bg-white rounded-[32px] border border-[#e5e7eb] w-full max-w-lg shadow-[0_32px_64px_-12px_rgba(0,0,0,0.1)] overflow-hidden scale-in-center animate-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="px-8 pt-8 pb-6 border-b border-[#f3f4f6] relative">
          <div className="w-12 h-12 rounded-2xl bg-[#f0f7ff] flex items-center justify-center mb-4">
             <Plus className="text-[#2563eb] w-6 h-6" strokeWidth={2.5} />
          </div>
          <h2 className="text-2xl font-bold text-[#111827] tracking-tight">Add New Prospect</h2>
          <p className="text-[#6b7280] text-sm font-medium mt-1">Fill in the details to start the intelligence workflow.</p>
          
          <button
            onClick={onClose}
            disabled={loading}
            className="absolute top-6 right-6 p-2 text-[#9ca3af] hover:text-[#111827] hover:bg-[#f3f4f6] rounded-xl transition-all disabled:opacity-50"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-8 space-y-6">
          <div className="grid grid-cols-2 gap-6">
            <div className="space-y-2">
              <label className="text-[11px] font-bold text-[#9ca3af] uppercase tracking-wider ml-1">
                First Name <span className="text-[#ef4444]">*</span>
              </label>
              <div className="relative">
                <User size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-[#9ca3af]" />
                <input
                  type="text"
                  placeholder="John"
                  value={formData.first_name}
                  onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                  disabled={loading}
                  className="w-full bg-[#f9fafb] border border-[#e5e7eb] rounded-2xl pl-11 pr-4 py-3 text-[#111827] text-sm font-medium placeholder:text-[#9ca3af] focus:bg-white focus:ring-4 focus:ring-[#2563eb]/5 focus:border-[#2563eb]/30 outline-none transition-all disabled:opacity-50 text-[13px]"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-[11px] font-bold text-[#9ca3af] uppercase tracking-wider ml-1">
                Last Name
              </label>
              <input
                type="text"
                placeholder="Doe"
                value={formData.last_name}
                onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                disabled={loading}
                className="w-full bg-[#f9fafb] border border-[#e5e7eb] rounded-2xl px-4 py-3 text-[#111827] text-sm font-medium placeholder:text-[#9ca3af] focus:bg-white focus:ring-4 focus:ring-[#2563eb]/5 focus:border-[#2563eb]/30 outline-none transition-all disabled:opacity-50 text-[13px]"
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-[11px] font-bold text-[#9ca3af] uppercase tracking-wider ml-1">
              Work Email <span className="text-[#ef4444]">*</span>
            </label>
            <div className="relative">
              <Mail size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-[#9ca3af]" />
              <input
                type="email"
                placeholder="john@stripe.com"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                disabled={loading}
                className="w-full bg-[#f9fafb] border border-[#e5e7eb] rounded-2xl pl-11 pr-4 py-3 text-[#111827] text-sm font-medium placeholder:text-[#9ca3af] focus:bg-white focus:ring-4 focus:ring-[#2563eb]/5 focus:border-[#2563eb]/30 outline-none transition-all disabled:opacity-50 text-[13px]"
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-[11px] font-bold text-[#9ca3af] uppercase tracking-wider ml-1">
              Job Title
            </label>
            <div className="relative">
              <Briefcase size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-[#9ca3af]" />
              <input
                type="text"
                placeholder="VP of Sales Intelligence"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                disabled={loading}
                className="w-full bg-[#f9fafb] border border-[#e5e7eb] rounded-2xl pl-11 pr-4 py-3 text-[#111827] text-sm font-medium placeholder:text-[#9ca3af] focus:bg-white focus:ring-4 focus:ring-[#2563eb]/5 focus:border-[#2563eb]/30 outline-none transition-all disabled:opacity-50 text-[13px]"
              />
            </div>
          </div>

          {error && (
            <div className="p-4 bg-[#fef2f2] border border-[#fee2e2] rounded-2xl text-xs font-bold text-[#991b1b] flex items-center gap-2">
              <div className="w-1.5 h-1.5 rounded-full bg-[#ef4444]" />
              {error}
            </div>
          )}

          <div className="flex gap-4 pt-4">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="flex-1 px-6 py-3 bg-white border border-[#e5e7eb] rounded-2xl text-sm font-bold text-[#4b5563] hover:bg-[#f9fafb] active:scale-[0.98] transition-all disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-[1.5] px-6 py-3 bg-[#2563eb] text-white rounded-2xl text-sm font-bold shadow-[0_8px_20px_-4px_rgba(37,99,235,0.3)] hover:scale-[1.02] active:scale-[0.98] transition-all disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Adding...</span>
                </>
              ) : 'Create Prospect'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
