"use client";

import React, { useState, useEffect } from 'react';
import {
  Search,
  Filter,
  Plus,
  MoreHorizontal,
  Zap,
  Building2,
  Users,
  TrendingUp,
  AlertCircle,
  ChevronLeft,
  ChevronRight,
  Globe,
  PieChart
} from 'lucide-react';
import { cn } from '@/lib/utils';
import AddCompanyModal from '@/components/AddCompanyModal';

interface Company {
  company_id: number;
  name: string;
  domain?: string;
  industry?: string;
  headcount?: number;
  funding_stage?: string;
  tech_stack?: string[];
  monitoring_enabled: boolean;
  prospects_count: number;
  created_at: string;
}

interface CompaniesData {
  total: number;
  page: number;
  per_page: number;
  items: Company[];
}

const MonitoringBadge = ({ enabled }: { enabled: boolean }) => (
  <div className={cn(
    "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-bold uppercase tracking-wider border transition-all",
    enabled
      ? "bg-[#ecfdf5] text-[#059669] border-[#d1fae5]"
      : "bg-[#f9fafb] text-[#6b7280] border-[#e5e7eb]"
  )}>
    <Zap className={cn("w-3.5 h-3.5", enabled && "fill-[#059669]")} />
    {enabled ? "Active" : "Paused"}
  </div>
);

export default function CompaniesPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [page, setPage] = useState(1);
  const [data, setData] = useState<CompaniesData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [addingCompany, setAddingCompany] = useState(false);

  const fetchCompanies = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('crm_token');
      if (!token) {
        window.location.href = '/login';
        return;
      }

      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8005/api';
      const params = new URLSearchParams();
      if (searchTerm) params.append('search', searchTerm);
      params.append('page', page.toString());
      params.append('per_page', '10');

      const response = await fetch(`${baseUrl}/companies?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.status === 401) {
        localStorage.removeItem('crm_token');
        window.location.href = '/login';
        return;
      }

      if (!response.ok) throw new Error('Failed to load companies');

      const result = await response.json();
      setData(result);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load companies');
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const debounceTimer = setTimeout(fetchCompanies, 300);
    return () => clearTimeout(debounceTimer);
  }, [searchTerm, page]);

  const handleAddCompany = async (formData: { name: string; domain?: string; industry?: string; headcount?: number; funding_stage?: string }) => {
    setAddingCompany(true);
    try {
      const token = localStorage.getItem('crm_token');
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8005/api';
      
      const response = await fetch(`${baseUrl}/companies`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(formData)
      });

      if (!response.ok) throw new Error('Failed to create company');
      setShowAddModal(false);
      fetchCompanies();
    } catch (err) {
      alert('Error: ' + (err instanceof Error ? err.message : 'Failed to create company'));
    } finally {
      setAddingCompany(false);
    }
  };

  const handleToggleMonitoring = async (companyId: number) => {
    try {
      const token = localStorage.getItem('crm_token');
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8005/api';
      
      await fetch(`${baseUrl}/companies/${companyId}/monitor`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      fetchCompanies();
    } catch (err) {
      console.error('Error toggling monitoring:', err);
    }
  };

  return (
    <div className="space-y-8">
      {/* Header Section */}
      <div className="flex items-end justify-between border-b border-[#e5e7eb] pb-6">
        <div>
          <h1 className="text-3xl font-bold text-[#111827] tracking-tight">Accounts & Entities</h1>
          <p className="text-[#6b7280] mt-1.5 font-medium">Monitoring {data?.total || 0} organizations for buying signals.</p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="flex items-center gap-2 bg-[#2563eb] text-white px-5 py-2.5 rounded-xl text-sm font-bold shadow-[0_8px_20px_-4px_rgba(37,99,235,0.3)] hover:scale-[1.02] active:scale-[0.98] transition-all"
        >
          <Plus size={18} strokeWidth={2.5} />
          <span>Track Company</span>
        </button>
      </div>

      {/* Main Content Card */}
      <div className="bg-white border border-[#e5e7eb] rounded-[32px] shadow-[0_8px_30px_rgb(0,0,0,0.02)] overflow-hidden">
        {/* Search Bar */}
        <div className="p-6 border-b border-[#f3f4f6] bg-[#fcfcfd]/50 flex items-center gap-4">
          <div className="relative flex-1 group">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-[#9ca3af] group-focus-within:text-[#2563eb] transition-colors" />
            <input
              type="text"
              placeholder="Search by company name, industry, or domain..."
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
                <th className="py-4 text-[11px] font-bold text-[#9ca3af] uppercase tracking-wider">Company</th>
                <th className="py-4 text-[11px] font-bold text-[#9ca3af] uppercase tracking-wider">Industry & Scaling</th>
                <th className="py-4 text-[11px] font-bold text-[#9ca3af] uppercase tracking-wider">Status</th>
                <th className="py-4 text-[11px] font-bold text-[#9ca3af] uppercase tracking-wider">Prospects</th>
                <th className="py-4 text-[11px] font-bold text-[#9ca3af] uppercase tracking-wider text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#f3f4f6]">
              {loading ? (
                <tr>
                  <td colSpan={5} className="py-20 text-center">
                    <div className="flex flex-col items-center gap-2">
                       <div className="w-8 h-8 border-3 border-[#f3f4f6] border-t-[#2563eb] rounded-full animate-spin" />
                       <p className="text-sm font-bold text-[#9ca3af]">Indexing entities...</p>
                    </div>
                  </td>
                </tr>
              ) : data && data.items.length > 0 ? (
                data.items.map((company) => (
                  <tr key={company.company_id} className="group hover:bg-[#fcfcfd] transition-colors">
                    <td className="py-5">
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#f8fafc] to-[#f1f5f9] border border-[#e5e7eb] flex items-center justify-center text-[#2563eb] shadow-sm transform transition-transform group-hover:scale-110">
                          <Building2 size={20} />
                        </div>
                        <div>
                          <p className="font-bold text-[#111827] text-sm leading-none mb-1">
                            {company.name}
                          </p>
                          <div className="flex items-center gap-1.5 text-[#9ca3af]">
                            <Globe size={12} />
                            <span className="text-[11px] font-medium tracking-wide uppercase">{company.domain || 'no domain'}</span>
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="py-5">
                      <div className="space-y-1.5">
                        <p className="text-xs font-bold text-[#4b5563]">{company.industry || 'Unknown Sector'}</p>
                        <div className="flex items-center gap-3">
                          <span className="text-[10px] font-bold text-[#2563eb] bg-[#eff6ff] px-1.5 py-0.5 rounded uppercase">{company.headcount || '0'} HC</span>
                          <span className="text-[10px] font-bold text-[#6b7280] bg-[#f9fafb] px-1.5 py-0.5 rounded border border-[#e5e7eb] uppercase">{company.funding_stage || 'N/A'}</span>
                        </div>
                      </div>
                    </td>
                    <td className="py-5">
                      <MonitoringBadge enabled={company.monitoring_enabled} />
                    </td>
                    <td className="py-5">
                      <div className="flex items-center gap-2 text-[#111827]">
                        <div className="w-6 h-6 rounded-lg bg-[#f3f4f6] flex items-center justify-center">
                          <Users size={12} className="text-[#6b7280]" />
                        </div>
                        <span className="text-sm font-bold">{company.prospects_count}</span>
                      </div>
                    </td>
                    <td className="py-5">
                      <div className="flex items-center justify-end gap-1">
                        <button
                          onClick={() => handleToggleMonitoring(company.company_id)}
                          className={cn(
                            "p-2 rounded-xl border transition-all",
                            company.monitoring_enabled
                              ? "bg-[#eff6ff] border-[#dbeafe] text-[#2563eb]"
                              : "bg-white border-transparent text-[#9ca3af] hover:text-[#111827] hover:bg-[#f9fafb] hover:border-[#e5e7eb]"
                          )}
                          title={company.monitoring_enabled ? "Pause Monitoring" : "Resume Monitoring"}
                        >
                          <Zap size={16} />
                        </button>
                        <button className="p-2 rounded-xl bg-white border border-transparent text-[#9ca3af] hover:text-[#111827] hover:bg-[#f9fafb] hover:border-[#e5e7eb] transition-all">
                          <MoreHorizontal size={16} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5} className="py-20 text-center">
                    <div className="flex flex-col items-center gap-3 opacity-40">
                       <Building2 size={48} className="text-[#9ca3af]" />
                       <p className="text-lg font-bold text-[#111827]">No organizations found</p>
                       <p className="text-sm text-[#6b7280]">Start tracking companies to monitor intelligence signals.</p>
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
               Showing {data.items.length} of {data.total} organizations
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

      <AddCompanyModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        onSubmit={handleAddCompany}
        loading={addingCompany}
      />
    </div>
  );
}
