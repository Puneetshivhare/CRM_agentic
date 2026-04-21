"use client";

import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { 
  Play, 
  CheckCircle, 
  XCircle, 
  Clock, 
  Zap, 
  Activity, 
  Cpu, 
  ShieldCheck 
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface Execution {
  execution_id: number;
  agent_type: string;
  status: string;
  start_time: string;
  end_time: string | null;
  duration_ms: number | null;
  confidence_score: number;
}

export default function EnrichmentPage() {
  const [executions, setExecutions] = useState<Execution[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchExecutions = async () => {
      try {
        const token = localStorage.getItem('crm_token');
        if (!token) {
          window.location.href = '/login';
          return;
        }

        const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8005/api';
        const response = await axios.get(`${baseUrl}/enrichment/executions`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        
        setExecutions(response.data.items || []);
      } catch (error) {
        console.error('Error fetching executions:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchExecutions();
  }, []);

  return (
    <div className="space-y-10">
      {/* ── Header ── */}
      <div className="flex items-end justify-between border-b border-[#e5e7eb] pb-6 reveal-animation">
        <div>
          <h1 className="text-3xl font-bold text-[#111827] tracking-tight">Enrichment Hub</h1>
          <p className="text-[#6b7280] mt-1.5 font-medium">Monitor and orchestrate your autonomous agent workflows.</p>
        </div>
        <button className="flex items-center gap-2 bg-[#2563eb] text-white px-5 py-2.5 rounded-xl text-sm font-bold shadow-[0_8px_20px_-4px_rgba(37,99,235,0.3)] hover:scale-[1.02] active:scale-[0.98] transition-all">
          <Play size={18} fill="currentColor" strokeWidth={3} />
          <span>Launch Agent</span>
        </button>
      </div>

      {/* ── Agent Stats ── */}
      <div className="grid grid-cols-4 gap-6 reveal-animation">
        {[
          { label: 'Active Agents', value: '12', icon: Activity, color: 'text-[#2563eb]', bg: 'bg-[#2563eb]/5' },
          { label: 'Total Enriched', value: '2.4k', icon: ShieldCheck, color: 'text-[#059669]', bg: 'bg-[#059669]/5' },
          { label: 'Avg Confidence', value: '94%', icon: Cpu, color: 'text-[#7c3aed]', bg: 'bg-[#7c3aed]/5' },
          { label: 'Success Rate', value: '99.2%', icon: CheckCircle, color: 'text-[#ea580c]', bg: 'bg-[#ea580c]/5' },
        ].map((stat, i) => (
          <div key={i} className="bg-white border border-[#e5e7eb] p-6 rounded-2xl shadow-sm hover:shadow-md transition-all group">
            <div className="flex items-center justify-between mb-4">
              <div className={cn("p-2.5 rounded-xl", stat.bg)}>
                <stat.icon className={cn("w-5 h-5", stat.color)} />
              </div>
              <div className="text-[10px] font-bold text-[#9ca3af] uppercase tracking-wider">Metric</div>
            </div>
            <div className="text-2xl font-bold text-[#111827] mb-1">{stat.value}</div>
            <div className="text-[12px] font-medium text-[#6b7280]">{stat.label}</div>
          </div>
        ))}
      </div>

      {/* ── Table Container ── */}
      <div className="bg-white border border-[#e5e7eb] rounded-2xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] overflow-hidden reveal-animation">
        <div className="px-8 py-5 border-b border-[#f3f4f6] flex items-center justify-between">
          <div className="text-[11px] font-bold text-[#9ca3af] uppercase tracking-[0.15em]">
            Agent Execution Logs
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-[#f9fafb] border-b border-[#e5e7eb]">
                <th className="px-8 py-4 text-[11px] font-bold text-[#9ca3af] uppercase tracking-[0.2em]">Agent Workflow</th>
                <th className="px-6 py-4 text-[11px] font-bold text-[#9ca3af] uppercase tracking-[0.2em]">Status</th>
                <th className="px-6 py-4 text-[11px] font-bold text-[#9ca3af] uppercase tracking-[0.2em]">Initialized</th>
                <th className="px-6 py-4 text-[11px] font-bold text-[#9ca3af] uppercase tracking-[0.2em]">Duration</th>
                <th className="px-8 py-4 text-[11px] font-bold text-[#9ca3af] uppercase tracking-[0.2em] text-right">Confidence</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#f3f4f6]">
              {loading ? (
                [...Array(6)].map((_, i) => (
                  <tr key={i} className="animate-pulse">
                    <td colSpan={5} className="px-8 py-6">
                      <div className="h-4 bg-[#f3f4f6] rounded-md w-3/4 mb-2" />
                      <div className="h-3 bg-[#f3f4f6] rounded-md w-1/2 opacity-50" />
                    </td>
                  </tr>
                ))
              ) : executions.length > 0 ? (
                executions.map((exe) => (
                  <tr key={exe.execution_id} className="group hover:bg-[#f9fafb] transition-all duration-200">
                    <td className="px-8 py-5">
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 rounded-xl bg-[#2563eb]/5 flex items-center justify-center border border-[#2563eb]/10 group-hover:bg-[#2563eb]/10 transition-all">
                          <Zap size={18} className="text-[#2563eb]" />
                        </div>
                        <span className="text-[14px] font-bold text-[#111827]">{exe.agent_type}</span>
                      </div>
                    </td>
                    <td className="px-6 py-5">
                      <span className={cn(
                        "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[12px] font-bold border transition-all",
                        exe.status === 'success' ? "bg-[#f0fdf4] text-[#166534] border-[#166534]/10" :
                        exe.status === 'failed' ? "bg-[#fef2f2] text-[#991b1b] border-[#991b1b]/10" :
                        "bg-[#eff6ff] text-[#1e40af] border-[#1e40af]/10"
                      )}>
                        {exe.status === 'success' && <CheckCircle size={14} />}
                        {exe.status === 'failed' && <XCircle size={14} />}
                        {exe.status === 'running' && <Clock size={14} className="animate-spin" />}
                        <span className="capitalize">{exe.status}</span>
                      </span>
                    </td>
                    <td className="px-6 py-5 text-[13px] text-[#64748b] font-medium">
                      {new Date(exe.start_time).toLocaleString(undefined, {
                        month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
                      })}
                    </td>
                    <td className="px-6 py-5 text-[13px] text-[#64748b] font-medium">
                      <div className="flex items-center gap-2">
                        <Clock size={14} className="text-[#94a3b8]" />
                        <span>{exe.duration_ms ? `${(exe.duration_ms / 1000).toFixed(1)}s` : '—'}</span>
                      </div>
                    </td>
                    <td className="px-8 py-5 text-right">
                      <div className="inline-flex items-center justify-end gap-3">
                        <div className="w-20 h-1.5 bg-[#f1f5f9] rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-[#2563eb] rounded-full transition-all duration-1000" 
                            style={{ width: `${exe.confidence_score * 100}%` }} 
                          />
                        </div>
                        <span className="text-[14px] font-bold text-[#111827] min-w-[36px]">
                          {(exe.confidence_score * 100).toFixed(0)}%
                        </span>
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5} className="px-8 py-24 text-center">
                    <div className="flex flex-col items-center gap-4">
                      <div className="w-16 h-16 rounded-3xl bg-[#f9fafb] flex items-center justify-center border border-[#e5e7eb]">
                        <Activity size={32} className="text-[#9ca3af]" />
                      </div>
                      <div>
                        <p className="text-[#111827] text-[15px] font-bold">No execution history</p>
                        <p className="text-[#6b7280] text-[13px] font-medium mt-1">Autonomous workflows will appear here once launched.</p>
                      </div>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

