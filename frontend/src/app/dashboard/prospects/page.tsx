"use client";

import React, { useState, useEffect } from 'react';
import {
  Search,
  Filter,
  Download,
  UserPlus,
  Zap,
  CheckCircle2,
  Clock,
  AlertCircle,
  ChevronLeft,
  ChevronRight,
  ShieldCheck
} from 'lucide-react';
import { cn } from '@/lib/utils';
import AddProspectModal from '@/components/AddProspectModal';
import ProspectActionsMenu from '@/components/ProspectActionsMenu';

interface Prospect {
  prospect_id: number;
  first_name?: string;
  last_name?: string;
  title?: string;
  email?: string;
  enrichment_status: string;
  enrichment_confidence: number;
  created_at: string;
}

interface ProspectsData {
  total: number;
  page: number;
  per_page: number;
  items: Prospect[];
}

const StatusBadge = ({ status }: { status: string }) => {
  const configs: Record<string, any> = {
    enriched: { icon: ShieldCheck, color: 'text-[#059669]', bg: 'bg-[#ecfdf5] border-[#d1fae5]', label: 'Enriched' },
    pending: { icon: Clock, color: 'text-[#6b7280]', bg: 'bg-[#f9fafb] border-[#e5e7eb]', label: 'Queued' },
    enriching: { icon: Zap, color: 'text-[#2563eb]', bg: 'bg-[#eff6ff] border-[#dbeafe]', label: 'Enriching', animate: true },
    failed: { icon: AlertCircle, color: 'text-[#ef4444]', bg: 'bg-[#fef2f2] border-[#fee2e2]', label: 'Failed' },
  };

  const config = configs[status] || configs.pending;
  const Icon = config.icon;

  return (
    <div className={cn("inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-bold uppercase tracking-wider border", config.bg, config.color)}>
      <Icon className={cn("w-3.5 h-3.5", config.animate && "animate-pulse")} />
      {config.label}
    </div>
  );
};

export default function ProspectsPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [page, setPage] = useState(1);
  const [data, setData] = useState<ProspectsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [addingProspect, setAddingProspect] = useState(false);
  const [enrichingIds, setEnrichingIds] = useState<Set<number>>(new Set());

  const fetchProspects = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('crm_token');
      if (!token) {
        window.location.href = '/login';
        return;
      }

      const params = new URLSearchParams();
      if (searchTerm) params.append('search', searchTerm);
      params.append('page', page.toString());
      params.append('per_page', '10');

      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8005/api';
      const response = await fetch(`${baseUrl}/prospects?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.status === 401) {
        localStorage.removeItem('crm_token');
        window.location.href = '/login';
        return;
      }

      if (!response.ok) throw new Error('Failed to load prospects');

      const result = await response.json();
      setData(result);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load prospects');
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const debounceTimer = setTimeout(fetchProspects, 300);
    return () => clearTimeout(debounceTimer);
  }, [searchTerm, page]);

  const handleAddProspect = async (formData: { first_name: string; last_name?: string; email: string; title?: string }) => {
    setAddingProspect(true);
    try {
      const token = localStorage.getItem('crm_token');
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8005/api';
      
      const response = await fetch(`${baseUrl}/prospects`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          ...formData,
          enrichment_status: 'pending',
          enrichment_confidence: 0
        })
      });

      if (!response.ok) throw new Error('Failed to create prospect');
      setShowAddModal(false);
      fetchProspects();
    } catch (err) {
      alert('Error: ' + (err instanceof Error ? err.message : 'Failed to create prospect'));
    } finally {
      setAddingProspect(false);
    }
  };

  const handleEnrichProspect = async (prospectId: number) => {
    setEnrichingIds(new Set([...enrichingIds, prospectId]));
    try {
      const token = localStorage.getItem('crm_token');
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8005/api';
      
      const response = await fetch(`${baseUrl}/enrichment/trigger`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ prospect_id: prospectId })
      });

      if (!response.ok) throw new Error('Failed to trigger enrichment');
      fetchProspects();
    } catch (err) {
      alert('Error: ' + (err instanceof Error ? err.message : 'Failed to trigger enrichment'));
    } finally {
      setEnrichingIds(prev => {
        const next = new Set(prev);
        next.delete(prospectId);
        return next;
      });
    }
  };

  const handleDeleteProspect = async (prospectId: number) => {
    try {
      const token = localStorage.getItem('crm_token');
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8005/api';
      
      const response = await fetch(`${baseUrl}/prospects/${prospectId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        fetchProspects();
      } else {
        throw new Error('Failed to delete');
      }
    } catch (err) {
      alert('Error: ' + (err instanceof Error ? err.message : 'Failed to delete prospect'));
    }
  };

  return (
    <div className="space-y-8">
      {/* Header Section */}
      <div className="flex items-end justify-between border-b border-[#e5e7eb] pb-6">
        <div>
          <h1 className="text-3xl font-bold text-[#111827] tracking-tight">Prospect Directory</h1>
          <p className="text-[#6b7280] mt-1.5 font-medium">Manage and monitor {data?.total || 0} intelligence targets.</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => {
              const csv = data?.items.map(p => `${p.first_name},${p.last_name},${p.email}`).join('\n') || '';
              const blob = new Blob([csv], { type: 'text/csv' });
              const url = URL.createObjectURL(blob);
              window.open(url);
            }}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl border border-[#e5e7eb] bg-white text-[#4b5563] text-sm font-bold hover:bg-[#f9fafb] transition-all"
          >
            <Download size={18} />
            <span>Export CSV</span>
          </button>
          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-2 bg-[#2563eb] text-white px-5 py-2.5 rounded-xl text-sm font-bold shadow-[0_8px_20px_-4px_rgba(37,99,235,0.3)] hover:scale-[1.02] active:scale-[0.98] transition-all"
          >
            <UserPlus size={18} strokeWidth={2.5} />
            <span>Add Prospect</span>
          </button>
        </div>
      </div>

      {/* Main Content Card */}
      <div className="bg-white border border-[#e5e7eb] rounded-[32px] shadow-[0_8px_30px_rgb(0,0,0,0.02)] overflow-hidden">
        {/* Search Bar */}
        <div className="p-6 border-b border-[#f3f4f6] bg-[#fcfcfd]/50 flex items-center gap-4">
          <div className="relative flex-1 group">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-[#9ca3af] group-focus-within:text-[#2563eb] transition-colors" />
            <input
              type="text"
              placeholder="Search by name, email, or job title..."
              className="w-full bg-white border border-[#e5e7eb] rounded-2xl py-3 pl-11 pr-4 text-[13px] text-[#111827] font-medium placeholder:text-[#9ca3af] outline-none focus:ring-4 focus:ring-[#2563eb]/5 focus:border-[#2563eb]/30 transition-all"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              disabled={loading}
            />
          </div>
          <button className="p-3 rounded-2xl bg-white border border-[#e5e7eb] text-[#6b7280] hover:text-[#111827] hover:bg-[#f9fafb] transition-all shadow-sm">
            <Filter size={18} />
          </button>
        </div>

        {/* Error Banner */}
        {error && (
          <div className="m-6 p-4 bg-[#fef2f2] border border-[#fee2e2] rounded-2xl flex items-center gap-3 text-[#991b1b] text-sm font-bold">
            <AlertCircle size={18} />
            {error}
          </div>
        )}

        {/* Table */}
        <div className="overflow-x-auto px-6">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-[#f3f4f6]">
                <th className="py-4 text-[11px] font-bold text-[#9ca3af] uppercase tracking-wider">Prospect</th>
                <th className="py-4 text-[11px] font-bold text-[#9ca3af] uppercase tracking-wider">Email</th>
                <th className="py-4 text-[11px] font-bold text-[#9ca3af] uppercase tracking-wider">Status</th>
                <th className="py-4 text-[11px] font-bold text-[#9ca3af] uppercase tracking-wider text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#f3f4f6]">
              {loading ? (
                <tr>
                  <td colSpan={4} className="py-20 text-center">
                    <div className="flex flex-col items-center gap-2">
                       <div className="w-8 h-8 border-3 border-[#f3f4f6] border-t-[#2563eb] rounded-full animate-spin" />
                       <p className="text-sm font-bold text-[#9ca3af]">Scanning directory...</p>
                    </div>
                  </td>
                </tr>
              ) : data && data.items.length > 0 ? (
                data.items.map((prospect) => (
                  <tr key={prospect.prospect_id} className="group hover:bg-[#fcfcfd] transition-colors">
                    <td className="py-5">
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#f8fafc] to-[#f1f5f9] border border-[#e5e7eb] flex items-center justify-center text-[13px] font-bold text-[#2563eb] shadow-sm transform transition-transform group-hover:scale-110">
                          {(prospect.first_name?.[0] || '')}{(prospect.last_name?.[0] || '')}
                        </div>
                        <div>
                          <p className="font-bold text-[#111827] text-sm leading-none mb-1">
                            {prospect.first_name} {prospect.last_name}
                          </p>
                          <p className="text-xs text-[#9ca3af] font-medium">{prospect.title || 'Lead Prospect'}</p>
                        </div>
                      </div>
                    </td>
                    <td className="py-5">
                      <div className="flex items-center gap-2">
                         <span className="text-sm font-medium text-[#4b5563]">{prospect.email || '—'}</span>
                      </div>
                    </td>
                    <td className="py-5">
                      <StatusBadge status={prospect.enrichment_status} />
                    </td>
                    <td className="py-5">
                      <div className="flex items-center justify-end">
                        <ProspectActionsMenu
                          prospectId={prospect.prospect_id}
                          email={prospect.email}
                          firstName={prospect.first_name}
                          onEnrich={handleEnrichProspect}
                          onDelete={handleDeleteProspect}
                          isEnriching={enrichingIds.has(prospect.prospect_id)}
                        />
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={4} className="py-20 text-center">
                    <div className="flex flex-col items-center gap-3 opacity-40">
                       <Search size={48} className="text-[#9ca3af]" />
                       <p className="text-lg font-bold text-[#111827]">No prospects discovered</p>
                       <p className="text-sm text-[#6b7280]">Try adjusting your search or add a new prospect.</p>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Footer / Pagination */}
        {data && (
          <div className="p-6 border-t border-[#f3f4f6] bg-[#fcfcfd]/50 flex items-center justify-between">
            <p className="text-[11px] font-bold text-[#9ca3af] uppercase tracking-wider">
               Showing {data.items.length} of {data.total} targets
            </p>
            <div className="flex gap-2">
              <button
                className="p-2 rounded-xl border border-[#e5e7eb] bg-white text-[#6b7280] hover:text-[#111827] hover:bg-[#f9fafb] shadow-sm disabled:opacity-40 transition-all"
                disabled={page === 1 || loading}
                onClick={() => setPage(page - 1)}
              >
                <ChevronLeft size={18} />
              </button>
              <div className="flex items-center px-4 py-2 text-sm font-bold text-[#111827] bg-white border border-[#e5e7eb] rounded-xl shadow-sm">
                {page}
              </div>
              <button
                className="p-2 rounded-xl border border-[#e5e7eb] bg-white text-[#6b7280] hover:text-[#111827] hover:bg-[#f9fafb] shadow-sm disabled:opacity-40 transition-all"
                disabled={page * data.per_page >= data.total || loading}
                onClick={() => setPage(page + 1)}
              >
                <ChevronRight size={18} />
              </button>
            </div>
          </div>
        )}
      </div>

      <AddProspectModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        onSubmit={handleAddProspect}
        loading={addingProspect}
      />
    </div>
  );
}
