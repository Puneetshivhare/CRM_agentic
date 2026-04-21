"use client";

import React, { useState, useEffect } from 'react';
import {
  Mail,
  Plus,
  MoreHorizontal,
  AlertCircle,
  CheckCircle2,
  Clock,
  Zap,
  TrendingUp,
  ChevronLeft,
  ChevronRight,
  Target,
  BarChart3
} from 'lucide-react';
import { cn } from '@/lib/utils';
import CreateCampaignModal from '@/components/CreateCampaignModal';

interface SequenceStep {
  day: number;
  subject: string;
  body: string;
}

interface Campaign {
  campaign_id: number;
  name: string;
  description?: string;
  sequence_steps: SequenceStep[];
  target_criteria?: Record<string, any>;
  is_active: boolean;
  enrolled_count: number;
  opened_count: number;
  clicked_count: number;
  replied_count: number;
  conversion_rate: number;
  created_at: string;
  updated_at: string;
}

interface CampaignsData {
  total: number;
  page: number;
  per_page: number;
  items: Campaign[];
}

const CampaignStatusBadge = ({ isActive }: { isActive: boolean }) => {
  return (
    <div className={cn(
      "inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-[11px] font-bold uppercase tracking-wider border transition-all",
      isActive 
        ? "bg-[#ecfdf5] text-[#059669] border-[#d1fae5]" 
        : "bg-[#f9fafb] text-[#6b7280] border-[#e5e7eb]"
    )}>
      <div className={cn("w-2 h-2 rounded-full", isActive ? "bg-[#10b981] shadow-[0_0_8px_rgba(16,185,129,0.5)]" : "bg-[#9ca3af]")} />
      {isActive ? "Active" : "Paused"}
    </div>
  );
};

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<CampaignsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [creatingCampaign, setCreatingCampaign] = useState(false);

  useEffect(() => {
    const fetchCampaigns = async () => {
      try {
        setLoading(true);
        const token = localStorage.getItem('crm_token');
        if (!token) {
          window.location.href = '/login';
          return;
        }

        const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8005/api';
        const response = await fetch(`${baseUrl}/campaigns?page=${page}&per_page=10`, {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (response.status === 401) {
          localStorage.removeItem('crm_token');
          window.location.href = '/login';
          return;
        }

        if (!response.ok) throw new Error('Failed to load campaigns');

        const data = await response.json();
        setCampaigns(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load campaigns');
        setCampaigns(null);
      } finally {
        setLoading(false);
      }
    };

    fetchCampaigns();
  }, [page]);

  const handleCreateCampaign = async (formData: { name: string; description: string; sequence_steps: SequenceStep[] }) => {
    setCreatingCampaign(true);
    try {
      const token = localStorage.getItem('crm_token');
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8005/api';
      const response = await fetch(`${baseUrl}/campaigns`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ ...formData, is_active: true })
      });

      if (!response.ok) throw new Error('Failed to create campaign');
      setShowCreateModal(false);
      setPage(1);
    } catch (err) {
      alert('Error: ' + (err instanceof Error ? err.message : 'Failed to create campaign'));
    } finally {
      setCreatingCampaign(false);
    }
  };

  const handleDeleteCampaign = async (campaignId: number) => {
    if (!confirm('Permanently delete this campaign?')) return;
    try {
      const token = localStorage.getItem('crm_token');
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8005/api';
      await fetch(`${baseUrl}/campaigns/${campaignId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setPage(1);
    } catch (err) {
      alert('Error: ' + (err instanceof Error ? err.message : 'Failed to delete campaign'));
    }
  };

  return (
    <div className="space-y-8">
      {/* Header Section */}
      <div className="flex items-end justify-between border-b border-[#e5e7eb] pb-6">
        <div>
          <h1 className="text-3xl font-bold text-[#111827] tracking-tight">Messaging Sequences</h1>
          <p className="text-[#6b7280] mt-1.5 font-medium">Automated workflows for conversion-led outreach.</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 bg-[#2563eb] text-white px-5 py-2.5 rounded-xl text-sm font-bold shadow-[0_8px_20px_-4px_rgba(37,99,235,0.3)] hover:scale-[1.02] active:scale-[0.98] transition-all"
        >
          <Plus size={18} strokeWidth={2.5} />
          <span>New Sequence</span>
        </button>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-4 gap-6">
        {[
          { label: 'Active Sequences', value: campaigns?.total || 0, icon: Target, color: 'text-[#2563eb]', bg: 'bg-[#eff6ff]' },
          { label: 'Avg. Open Rate', value: '42.5%', icon: Mail, color: 'text-[#8b5cf6]', bg: 'bg-[#f5f3ff]' },
          { label: 'Total Enrolled', value: '1,420', icon: CheckCircle2, color: 'text-[#10b981]', bg: 'bg-[#ecfdf5]' },
          { label: 'Avg. Conversion', value: '8.2%', icon: BarChart3, color: 'text-[#f59e0b]', bg: 'bg-[#fffbeb]' },
        ].map((stat, i) => (
          <div key={i} className="bg-white border border-[#e5e7eb] p-6 rounded-[24px] shadow-sm flex flex-col gap-4">
            <div className={cn("w-10 h-10 rounded-xl flex items-center justify-center", stat.bg, stat.color)}>
              <stat.icon size={20} />
            </div>
            <div>
              <p className="text-2xl font-bold text-[#111827]">{stat.value}</p>
              <p className="text-xs font-bold text-[#9ca3af] uppercase tracking-wider mt-1">{stat.label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Main Content Card */}
      <div className="bg-white border border-[#e5e7eb] rounded-[32px] shadow-[0_8px_30px_rgb(0,0,0,0.02)] overflow-hidden">
        <div className="p-6 border-b border-[#f3f4f6] bg-[#fcfcfd]/50">
          <p className="text-[11px] font-bold text-[#9ca3af] uppercase tracking-wider">
             {campaigns ? `${campaigns.items.length} of ${campaigns.total} Sequences` : 'Loading Sequences...'}
          </p>
        </div>

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
                <th className="py-4 text-[11px] font-bold text-[#9ca3af] uppercase tracking-wider">Sequence</th>
                <th className="py-4 text-[11px] font-bold text-[#9ca3af] uppercase tracking-wider">Status</th>
                <th className="py-4 text-[11px] font-bold text-[#9ca3af] uppercase tracking-wider">Structure</th>
                <th className="py-4 text-[11px] font-bold text-[#9ca3af] uppercase tracking-wider">Performance</th>
                <th className="py-4 text-[11px] font-bold text-[#9ca3af] uppercase tracking-wider text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#f3f4f6]">
              {loading ? (
                <tr>
                  <td colSpan={5} className="py-20 text-center">
                    <div className="flex flex-col items-center gap-2">
                       <div className="w-8 h-8 border-3 border-[#f3f4f6] border-t-[#2563eb] rounded-full animate-spin" />
                       <p className="text-sm font-bold text-[#9ca3af]">Synching workflows...</p>
                    </div>
                  </td>
                </tr>
              ) : campaigns && campaigns.items.length > 0 ? (
                campaigns.items.map((campaign) => (
                  <tr key={campaign.campaign_id} className="group hover:bg-[#fcfcfd] transition-colors">
                    <td className="py-6">
                      <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-[#f8fafc] to-[#f1f5f9] border border-[#e5e7eb] flex items-center justify-center text-[#2563eb] shadow-sm transform transition-transform group-hover:scale-110">
                          <Zap size={24} />
                        </div>
                        <div>
                          <p className="font-bold text-[#111827] text-sm leading-none mb-1.5">
                            {campaign.name}
                          </p>
                          <p className="text-xs text-[#9ca3af] font-medium max-w-[240px] truncate">
                            {campaign.description || 'No description provided'}
                          </p>
                        </div>
                      </div>
                    </td>
                    <td className="py-6">
                      <CampaignStatusBadge isActive={campaign.is_active} />
                    </td>
                    <td className="py-6">
                      <div className="flex items-center gap-3">
                         <div className="flex -space-x-2">
                           {[...Array(Math.min(campaign.sequence_steps.length, 3))].map((_, i) => (
                             <div key={i} className="w-7 h-7 rounded-full bg-white border-2 border-[#f1f5f9] flex items-center justify-center shadow-sm">
                               <div className="w-4 h-4 rounded-full bg-[#eff6ff] ring-1 ring-[#dbeafe] flex items-center justify-center">
                                  <span className="text-[8px] font-black text-[#2563eb]">{i+1}</span>
                               </div>
                             </div>
                           ))}
                         </div>
                         <span className="text-sm font-bold text-[#111827]">{campaign.sequence_steps.length} Steps</span>
                      </div>
                    </td>
                    <td className="py-6">
                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-[10px] font-black text-[#6b7280] uppercase tracking-widest">
                          <span>Progress</span>
                          <span className="text-[#2563eb]">{campaign.conversion_rate > 0 ? `${(campaign.conversion_rate * 100).toFixed(1)}%` : '0%'}</span>
                        </div>
                        <div className="w-32 h-1.5 bg-[#f3f4f6] rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-[#2563eb] rounded-full shadow-[0_0_8px_rgba(37,99,235,0.4)] transition-all duration-1000" 
                            style={{ width: `${Math.max(campaign.conversion_rate * 100, 4)}%` }} 
                          />
                        </div>
                      </div>
                    </td>
                    <td className="py-6">
                      <div className="flex items-center justify-end gap-1">
                        <button className="p-2 rounded-xl bg-white border border-transparent text-[#9ca3af] hover:text-[#111827] hover:bg-[#f9fafb] hover:border-[#e5e7eb] transition-all">
                          <BarChart3 size={18} />
                        </button>
                        <button
                          onClick={() => handleDeleteCampaign(campaign.campaign_id)}
                          className="p-2 rounded-xl bg-white border border-transparent text-[#9ca3af] hover:text-[#ef4444] hover:bg-[#fef2f2] hover:border-[#fee2e2] transition-all"
                        >
                          <MoreHorizontal size={18} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5} className="py-20 text-center">
                    <div className="flex flex-col items-center gap-3 opacity-40">
                       <Mail size={48} className="text-[#9ca3af]" />
                       <p className="text-lg font-bold text-[#111827]">No active sequences</p>
                       <p className="text-sm text-[#6b7280]">Design your first automated sequence to start outreach.</p>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Footer / Pagination */}
        {campaigns && (
          <div className="p-6 border-t border-[#f3f4f6] bg-[#fcfcfd]/50 flex items-center justify-between">
            <p className="text-[11px] font-bold text-[#9ca3af] uppercase tracking-wider">
               Active Workflows: {campaigns.items.length}
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
                disabled={page * campaigns.per_page >= campaigns.total || loading}
                onClick={() => setPage(page + 1)}
              >
                <ChevronRight size={18} />
              </button>
            </div>
          </div>
        )}
      </div>

      <CreateCampaignModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSubmit={handleCreateCampaign}
        loading={creatingCampaign}
      />
    </div>
  );
}
