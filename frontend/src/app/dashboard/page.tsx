"use client";

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  Users,
  Target,
  TrendingUp,
  Activity,
  ArrowUpRight,
  Plus,
  AlertCircle,
  Zap,
  Globe,
  MessageSquare,
  Search
} from 'lucide-react';
import { cn } from '@/lib/utils';
import AddProspectModal from '@/components/AddProspectModal';

interface DashboardStats {
  total_prospects: number;
  enriched_prospects: number;
  enrichment_rate: number;
  pending_prospects: number;
}

interface AgentExecution {
  execution_id: number;
  agent_type: string;
  status: string;
  duration_ms?: number;
  created_at: string;
  decision_description?: string;
}

interface ExecutionsData {
  total: number;
  items: AgentExecution[];
}

export default function DashboardPage() {
  const router = useRouter();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [executions, setExecutions] = useState<AgentExecution[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [addingProspect, setAddingProspect] = useState(false);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        setLoading(true);
        const token = localStorage.getItem('crm_token');
        if (!token) {
          window.location.href = '/login';
          return;
        }

        const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8005/api';
        const [prospectsRes, executionsRes] = await Promise.all([
          fetch(`${baseUrl}/prospects?per_page=100`, {
            headers: { Authorization: `Bearer ${token}` },
          }),
          fetch(`${baseUrl}/enrichment/executions?per_page=10`, {
            headers: { Authorization: `Bearer ${token}` },
          })
        ]);

        if (prospectsRes.status === 401 || executionsRes.status === 401) {
          localStorage.removeItem('crm_token');
          window.location.href = '/login';
          return;
        }

        if (!prospectsRes.ok) {
          throw new Error(`Failed to fetch prospects`);
        }

        const prospectsData = await prospectsRes.json();
        const total = prospectsData.total || 0;
        const items = prospectsData.items || [];
        const enriched = items.filter((p: any) => p.enrichment_status === 'enriched').length;
        const pending = items.filter((p: any) => p.enrichment_status === 'pending').length;

        setStats({
          total_prospects: total,
          enriched_prospects: enriched,
          enrichment_rate: total > 0 ? (enriched / total) * 100 : 0,
          pending_prospects: pending,
        });

        if (executionsRes.ok) {
          const execData = await executionsRes.json();
          setExecutions((execData.items || []).slice(0, 4));
        }

        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load intelligence');
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  const handleAddProspect = async (data: { first_name: string; last_name?: string; email: string; title?: string }) => {
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
          ...data,
          enrichment_status: 'pending',
          enrichment_confidence: 0
        })
      });

      if (!response.ok) throw new Error('Failed to create prospect');
      setShowAddModal(false);
      window.location.reload();
    } catch (err) {
      alert('Error: ' + (err instanceof Error ? err.message : 'Failed to create prospect'));
    } finally {
      setAddingProspect(false);
    }
  };

  const statConfig = [
    { name: 'Total Prospects', value: stats?.total_prospects ?? 0, icon: Users, color: 'text-[#2563eb]', bg: 'bg-[#2563eb]/10' },
    { name: 'Enriched', value: stats?.enriched_prospects ?? 0, icon: Target, color: 'text-[#059669]', bg: 'bg-[#059669]/10' },
    { name: 'Intelligence Rate', value: `${(stats?.enrichment_rate ?? 0).toFixed(1)}%`, icon: Zap, color: 'text-[#7c3aed]', bg: 'bg-[#7c3aed]/10' },
    { name: 'Action Items', value: stats?.pending_prospects ?? 0, icon: Activity, color: 'text-[#ea580c]', bg: 'bg-[#ea580c]/10' },
  ];

  return (
    <div className="space-y-12 pb-12">
      {/* ── Header ── */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div className="reveal-animation">
          <h1 className="text-4xl font-extrabold text-[#111827] tracking-tight">Intelligence Dashboard</h1>
          <p className="text-[#6b7280] mt-2 font-medium text-lg leading-relaxed">Monitoring {stats?.total_prospects || 0} active leads across your agents.</p>
        </div>
        <div className="flex gap-4">
          <button
            onClick={() => router.push('/dashboard/enrichment')}
            className="px-6 py-3 rounded-2xl border border-[#e5e7eb] bg-white text-[#4b5563] text-sm font-bold shadow-[0_4px_12px_rgba(0,0,0,0.03)] hover:bg-[#f9fafb] hover:-translate-y-0.5 transition-all active:translate-y-0"
          >
            Launch Runner
          </button>
          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-2 bg-[#2563eb] text-white px-6 py-3 rounded-2xl text-sm font-bold shadow-[0_8px_30px_-4px_rgba(37,99,235,0.4)] hover:shadow-[0_12px_40px_-4px_rgba(37,99,235,0.5)] hover:-translate-y-0.5 active:scale-[0.98] transition-all"
          >
            <Plus size={18} strokeWidth={3} />
            <span>New Prospect</span>
          </button>
        </div>
      </div>

      {/* ── Error ── */}
      {error && (
        <div className="p-4 rounded-xl bg-[#fef2f2] border border-[#fee2e2] flex items-center gap-3 text-[#991b1b] text-sm font-medium">
          <AlertCircle size={18} />
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statConfig.map((stat) => (
          <div key={stat.name} className="relative overflow-hidden bg-white border border-[#e5e7eb] p-8 rounded-[32px] shadow-[0_8px_30px_rgb(0,0,0,0.02)] hover:shadow-[0_25px_50px_-12px_rgba(0,0,0,0.06)] transition-all duration-500 group border-b-4 border-b-transparent hover:border-b-[#2563eb]/20">
            <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-transparent to-[#f1f5f9] -mr-16 -mt-16 rounded-full group-hover:scale-125 transition-transform duration-700" />
            
            <div className="flex items-center gap-5 mb-6 relative z-10">
              <div className={cn("w-14 h-14 rounded-[20px] flex items-center justify-center transition-all group-hover:rotate-6 duration-300 shadow-sm", stat.bg)}>
                <stat.icon className={cn("w-7 h-7", stat.color)} />
              </div>
              <div className="flex flex-col min-w-0">
                <span className="text-[11px] font-bold text-[#9ca3af] uppercase tracking-[0.2em] truncate">{stat.name}</span>
                <div className="mt-1.5 flex items-center gap-1.5 text-[10px] font-bold text-[#16a34a] bg-[#f0fdf4] px-2 py-0.5 rounded-full w-fit">
                   <ArrowUpRight size={10} strokeWidth={3} />
                   <span>+12.5%</span>
                </div>
              </div>
            </div>
            
            <div className="relative z-10 flex items-baseline gap-1.5">
              {loading ? (
                <div className="h-10 w-24 bg-[#f3f4f6] animate-pulse rounded-xl" />
              ) : (
                <div className="flex items-baseline gap-2 overflow-hidden">
                  <span className="text-4xl font-extrabold text-[#111827] tracking-tight truncate">
                    {stat.value}
                  </span>
                  {typeof stat.value === 'number' && <span className="text-sm font-bold text-[#9ca3af] tracking-tight shrink-0 uppercase">leads</span>}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* ── Content ── */}
      <div className="grid grid-cols-12 gap-8">
        {/* Agent Activity Tracker */}
        <div className="col-span-12 lg:col-span-8 bg-white border border-[#e5e7eb] rounded-[32px] p-8 shadow-[0_8px_30px_rgb(0,0,0,0.03)] flex flex-col">
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-2xl bg-[#eff6ff] flex items-center justify-center">
                 <Zap className="text-[#2563eb] w-6 h-6" />
              </div>
              <div>
                <h3 className="text-xl font-bold text-[#111827]">Active Workflows</h3>
                <p className="text-[13px] text-[#6b7280] font-medium">Real-time status of your intelligence runners.</p>
              </div>
            </div>
            <button onClick={() => router.push('/dashboard/enrichment')} className="text-[#2563eb] text-sm font-bold hover:bg-[#2563eb]/5 px-4 py-2 rounded-xl transition-all">Manage Agents</button>
          </div>
          
          <div className="space-y-4">
            {executions.length > 0 ? (
              executions.map((exec) => (
                <div key={exec.execution_id} className="p-6 rounded-2xl border border-[#f3f4f6] bg-[#f9fafb]/30 group hover:bg-[#f9fafb] hover:shadow-sm transition-all border-l-4 border-l-transparent hover:border-l-[#2563eb]">
                  <div className="flex justify-between items-center mb-4">
                    <div className="flex items-center gap-3">
                      <div className={cn(
                        "w-2.5 h-2.5 rounded-full",
                        exec.status === 'running' ? 'bg-[#2563eb] animate-pulse shadow-[0_0_12px_rgba(37,99,235,0.5)]' : 
                        exec.status === 'success' ? 'bg-[#16a34a]' : 'bg-[#ef4444]'
                      )} />
                      <span className="text-[15px] font-bold text-[#111827]">{exec.agent_type} Explorer</span>
                    </div>
                    <span className="text-[12px] font-bold text-[#9ca3af] bg-white px-2.5 py-1 rounded-lg border border-gray-100 uppercase tracking-wider">
                      {exec.duration_ms ? `${(exec.duration_ms/1000).toFixed(1)}s` : 'Runner Started'}
                    </span>
                  </div>
                  <p className="text-[14px] text-[#6b7280] font-medium line-clamp-2 min-h-[40px] leading-relaxed mb-4">
                    {exec.decision_description || `Currently executing high-fidelity data enrichment for incoming prospect signals.`}
                  </p>
                  <div className="w-full h-2 bg-[#f1f5f9] rounded-full overflow-hidden shadow-inner">
                    <div
                      className={cn(
                        "h-full transition-all duration-1000 ease-out",
                        exec.status === 'success' ? 'bg-gradient-to-r from-[#16a34a] to-[#22c55e]' : 'bg-gradient-to-r from-[#2563eb] to-[#60a5fa]'
                      )}
                      style={{ width: exec.status === 'success' ? '100%' : '78%' }}
                    />
                  </div>
                </div>
              ))
            ) : (
              <div className="py-20 text-center bg-[#f9fafb]/50 border-2 border-dashed border-[#e5e7eb] rounded-[24px]">
                <div className="w-16 h-16 rounded-full bg-white border border-[#e5e7eb] flex items-center justify-center mx-auto mb-4 shadow-sm">
                  <Activity className="w-8 h-8 text-[#9ca3af]/40" />
                </div>
                <p className="font-bold text-[#9ca3af] text-lg">No active intelligence runners</p>
                <p className="text-sm text-[#6b7280] font-medium mt-1">Ready to process your next prospect signals.</p>
              </div>
            )}
          </div>
        </div>

        {/* Intelligence Feed */}
        <div className="col-span-4 bg-white border border-[#e5e7eb] rounded-[32px] p-8 shadow-[0_8px_30px_rgb(0,0,0,0.02)] flex flex-col h-full">
          <div className="flex items-center gap-3 mb-8">
            <div className="w-10 h-10 rounded-xl bg-[#ecf2ff] flex items-center justify-center">
               <Globe className="text-[#2563eb] w-5 h-5" />
            </div>
            <h3 className="text-xl font-bold text-[#111827]">Global Insights</h3>
          </div>

          <div className="flex-1 space-y-6">
             {[
               { title: 'Prospect Qualified', body: 'Sarah @ Stripe enriched with Series C funding data.', time: '2m', type: 'enrichment', icon: Zap },
               { title: 'New Signal', body: 'Supabase hiring 5 new Sales Intelligence reps.', time: '1h', type: 'signal', icon: Search },
               { title: 'Intent Match', body: 'Linear ICP signals match via LinkedIn activity.', time: '3h', type: 'match', icon: MessageSquare },
             ].map((alert, i) => (
                <div key={i} className="flex gap-4 group cursor-pointer">
                  <div className="flex flex-col items-center">
                    <div className={cn(
                      "w-10 h-10 rounded-xl flex items-center justify-center border-2 border-white shadow-sm z-10 transition-transform group-hover:scale-110",
                      alert.type === 'enrichment' ? 'bg-[#f0fdf4] text-[#16a34a]' :
                      alert.type === 'signal' ? 'bg-[#eff6ff] text-[#2563eb]' : 'bg-[#faf5ff] text-[#7c3aed]'
                    )}>
                      <alert.icon size={18} />
                    </div>
                    {i < 2 && <div className="w-[1px] h-full bg-[#f3f4f6] my-1" />}
                  </div>
                  <div className="flex-1 pt-0.5">
                    <div className="flex justify-between items-start mb-1">
                      <p className="text-[13px] font-bold text-[#111827] group-hover:text-[#2563eb] transition-colors">{alert.title}</p>
                      <span className="text-[10px] font-bold text-[#9ca3af]">{alert.time}</span>
                    </div>
                    <p className="text-[12px] text-[#6b7280] font-medium leading-relaxed group-hover:text-[#4b5563]">{alert.body}</p>
                  </div>
                </div>
             ))}
          </div>
          
          <div className="mt-8 p-5 bg-[#f8fafc] rounded-2xl border border-[#e5e7eb] space-y-3">
             <div className="flex justify-between items-center text-[11px] font-bold text-[#9ca3af] uppercase tracking-wider">
                <span>Agent Load</span>
                <span className="text-[#2563eb]">Optimal</span>
             </div>
             <div className="h-2 w-full bg-[#e2e8f0] rounded-full overflow-hidden">
                <div className="h-full w-[45%] bg-[#2563eb] rounded-full" />
             </div>
          </div>
        </div>
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
