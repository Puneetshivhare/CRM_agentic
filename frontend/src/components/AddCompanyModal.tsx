"use client";

import React, { useState } from 'react';
import { X, Building2, Globe, Users, TrendingUp, Sparkles } from 'lucide-react';
import { cn } from '@/lib/utils';

interface AddCompanyModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: { name: string; domain?: string; industry?: string; headcount?: number; funding_stage?: string }) => void;
  loading?: boolean;
}

export default function AddCompanyModal({ isOpen, onClose, onSubmit, loading }: AddCompanyModalProps) {
  const [formData, setFormData] = useState({
    name: '',
    domain: '',
    industry: '',
    headcount: '',
    funding_stage: '',
  });
  const [error, setError] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!formData.name.trim()) {
      setError('Company name is required to begin tracking');
      return;
    }

    onSubmit({
      name: formData.name,
      domain: formData.domain || undefined,
      industry: formData.industry || undefined,
      headcount: formData.headcount ? parseInt(formData.headcount) : undefined,
      funding_stage: formData.funding_stage || undefined,
    });

    setFormData({ name: '', domain: '', industry: '', headcount: '', funding_stage: '' });
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div 
        className="absolute inset-0 bg-[#0f172a]/40 backdrop-blur-sm transition-opacity animate-in fade-in duration-300" 
        onClick={onClose} 
      />
      
      <div className="relative bg-white w-full max-w-lg rounded-[32px] shadow-[0_24px_80px_rgba(0,0,0,0.18)] overflow-hidden animate-in zoom-in-95 slide-in-from-bottom-4 duration-400">
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-[#2563eb] via-[#3b82f6] to-[#06b6d4]" />
        
        {/* Header */}
        <div className="px-10 pt-10 pb-6 flex items-start justify-between">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-[#eff6ff] flex items-center justify-center text-[#2563eb] shadow-sm transform rotate-3">
               <Building2 size={24} />
            </div>
            <div>
              <h2 className="text-xl font-black text-[#111827] tracking-tight">Track New Entity</h2>
              <p className="text-[13px] text-[#6b7280] font-medium leading-none mt-1">Start monitoring buying signals for this account.</p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-2.5 hover:bg-[#f3f4f6] rounded-2xl text-[#9ca3af] hover:text-[#111827] transition-all"
          >
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="px-10 pb-10 space-y-6">
          <div className="space-y-5">
            <div>
              <label className="block text-[11px] font-black text-[#9ca3af] uppercase tracking-[0.2em] mb-2.5 ml-1">
                Company Name <span className="text-[#ef4444]">*</span>
              </label>
              <div className="relative group">
                 <Building2 className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-[#9ca3af] group-focus-within:text-[#2563eb] transition-colors" />
                 <input
                   type="text"
                   placeholder="e.g. Acme Corporation"
                   value={formData.name}
                   onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                   disabled={loading}
                   className="w-full bg-[#f9fafb] border border-[#e5e7eb] rounded-2xl py-3.5 pl-11 pr-4 text-sm font-bold text-[#111827] placeholder:text-[#9ca3af] outline-none focus:bg-white focus:ring-4 focus:ring-[#2563eb]/5 focus:border-[#2563eb]/40 transition-all disabled:opacity-50"
                 />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-[11px] font-black text-[#9ca3af] uppercase tracking-[0.2em] mb-2.5 ml-1">
                  Domain (Optional)
                </label>
                <div className="relative group">
                   <Globe className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-[#9ca3af] group-focus-within:text-[#2563eb] transition-colors" />
                   <input
                     type="text"
                     placeholder="acme.com"
                     value={formData.domain}
                     onChange={(e) => setFormData({ ...formData, domain: e.target.value })}
                     disabled={loading}
                     className="w-full bg-[#f9fafb] border border-[#e5e7eb] rounded-2xl py-3.5 pl-11 pr-4 text-sm font-bold text-[#111827] placeholder:text-[#9ca3af] outline-none focus:bg-white focus:ring-4 focus:ring-[#2563eb]/5 focus:border-[#2563eb]/40 transition-all disabled:opacity-50"
                   />
                </div>
              </div>
              <div>
                <label className="block text-[11px] font-black text-[#9ca3af] uppercase tracking-[0.2em] mb-2.5 ml-1">
                  Headcount
                </label>
                <div className="relative group">
                   <Users className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-[#9ca3af] group-focus-within:text-[#2563eb] transition-colors" />
                   <input
                     type="number"
                     placeholder="150"
                     value={formData.headcount}
                     onChange={(e) => setFormData({ ...formData, headcount: e.target.value })}
                     disabled={loading}
                     className="w-full bg-[#f9fafb] border border-[#e5e7eb] rounded-2xl py-3.5 pl-11 pr-4 text-sm font-bold text-[#111827] placeholder:text-[#9ca3af] outline-none focus:bg-white focus:ring-4 focus:ring-[#2563eb]/5 focus:border-[#2563eb]/40 transition-all disabled:opacity-50"
                   />
                </div>
              </div>
            </div>

            <div>
              <label className="block text-[11px] font-black text-[#9ca3af] uppercase tracking-[0.2em] mb-2.5 ml-1">
                Industry
              </label>
              <input
                type="text"
                placeholder="Enterprise Software, FinTech, etc."
                value={formData.industry}
                onChange={(e) => setFormData({ ...formData, industry: e.target.value })}
                disabled={loading}
                className="w-full bg-[#f9fafb] border border-[#e5e7eb] rounded-2xl py-3.5 px-5 text-sm font-bold text-[#111827] placeholder:text-[#9ca3af] outline-none focus:bg-white focus:ring-4 focus:ring-[#2563eb]/5 focus:border-[#2563eb]/40 transition-all disabled:opacity-50"
              />
            </div>

            <div>
              <label className="block text-[11px] font-black text-[#9ca3af] uppercase tracking-[0.2em] mb-2.5 ml-1">
                Funding Stage
              </label>
              <div className="relative group">
                 <TrendingUp className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-[#9ca3af]" />
                 <input
                   type="text"
                   placeholder="Series B, Seed, Public..."
                   value={formData.funding_stage}
                   onChange={(e) => setFormData({ ...formData, funding_stage: e.target.value })}
                   disabled={loading}
                   className="w-full bg-[#f9fafb] border border-[#e5e7eb] rounded-2xl py-3.5 pl-11 pr-4 text-sm font-bold text-[#111827] outline-none focus:bg-white focus:ring-4 focus:ring-[#2563eb]/5 focus:border-[#2563eb]/40 transition-all disabled:opacity-50"
                 />
              </div>
            </div>
          </div>

          {error && (
            <div className="p-4 bg-[#fef2f2] border border-[#fee2e2] rounded-2xl text-[12px] font-bold text-[#ef4444] flex items-center gap-2 animate-in slide-in-from-top-1">
               <div className="w-1.5 h-1.5 rounded-full bg-[#ef4444]" />
               {error}
            </div>
          )}

          <div className="flex gap-4 pt-6">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="flex-1 px-6 py-4 border border-[#e5e7eb] rounded-2xl text-sm font-black text-[#6b7280] hover:bg-[#fcfcfd] active:scale-[0.98] transition-all disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 px-6 py-4 bg-[#2563eb] text-white rounded-2xl text-sm font-black shadow-[0_12px_28px_-6px_rgba(37,99,235,0.4)] hover:scale-[1.02] active:scale-[0.98] transition-all disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Tracking...</span>
                </>
              ) : (
                <>
                  <Sparkles size={18} strokeWidth={2.5} />
                  <span>Start Monitoring</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
