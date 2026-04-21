"use client";

import React, { useEffect, useState } from 'react';
import {
  TrendingUp,
  Users,
  Target,
  Zap,
  AlertCircle,
  CheckCircle2,
  Clock,
  Activity,
  BarChart3,
  PieChart,
  ArrowRight
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface AnalyticsData {
  total_prospects: number;
  hot_leads: number;
  avg_lead_score: number;
  conversion_rate: number;
  grade_distribution: Record<string, number>;
  pipeline_velocity: number;
}

export default function AnalyticsPage() {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        setLoading(true);
        const token = localStorage.getItem('crm_token');
        if (!token) {
          window.location.href = '/login';
          return;
        }

        const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8005/api';
        
        // Simulate analytics aggregation from lead-scores
        const leadScoresRes = await fetch(`${baseUrl}/lead-scores?per_page=100`, {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (leadScoresRes.status === 401) {
          localStorage.removeItem('crm_token');
          window.location.href = '/login';
          return;
        }

        const leadScoresData = await leadScoresRes.json();
        const scores = leadScoresData.items || [];

        const hotLeads = scores.filter((s: any) => s.is_hot_lead).length;
        const avgScore = scores.length > 0
          ? (scores.reduce((sum: number, s: any) => sum + s.total_score, 0) / scores.length).toFixed(1)
          : 0;

        const gradeDistribution = {
          A: scores.filter((s: any) => s.grade === 'A').length,
          B: scores.filter((s: any) => s.grade === 'B').length,
          C: scores.filter((s: any) => s.grade === 'C').length,
          D: scores.filter((s: any) => s.grade === 'D').length,
          F: scores.filter((s: any) => s.grade === 'F').length,
        };

        setAnalytics({
          total_prospects: scores.length,
          hot_leads: hotLeads,
          avg_lead_score: parseFloat(avgScore as string),
          conversion_rate: (hotLeads / (scores.length || 1)) * 100,
          grade_distribution: gradeDistribution,
          pipeline_velocity: 12,
        });

        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load analytics');
        setAnalytics(null);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalytics();
  }, []);

  const StatCard = ({
    icon: Icon,
    label,
    value,
    subtext,
    color,
    bg
  }: {
    icon: React.ComponentType<any>;
    label: string;
    value: string | number;
    subtext?: string;
    color: string;
    bg: string;
  }) => (
    <div className="bg-white border border-[#e5e7eb] p-7 rounded-[24px] shadow-sm hover:shadow-md transition-all group reveal-animation relative overflow-hidden">
      <div className={cn("absolute top-0 right-0 w-24 h-24 blur-3xl opacity-10 rounded-full -mr-8 -mt-8", bg)} />
      <div className="flex items-center justify-between mb-4 relative z-10">
        <div className={cn("p-3 rounded-[14px]", bg)}>
          <Icon className={cn("w-5 h-5", color)} />
        </div>
        <div className="text-[10px] font-bold text-[#9ca3af] uppercase tracking-wider">Metrics</div>
      </div>
      <p className="text-[#64748b] text-[13px] font-bold mb-1 relative z-10">{label}</p>
      <h3 className="text-3xl font-bold tracking-tight text-[#111827] relative z-10">
        {loading ? "..." : value}
      </h3>
      {subtext && <p className="text-[11px] font-medium text-[#94a3b8] mt-2 relative z-10">{subtext}</p>}
    </div>
  );

  return (
    <div className="space-y-10">
      {/* ── Header ── */}
      <div className="flex items-end justify-between border-b border-[#e5e7eb] pb-6 reveal-animation">
        <div>
          <h1 className="text-3xl font-bold text-[#111827] tracking-tight tracking-tight">Intelligence Dashboard</h1>
          <p className="text-[#6b7280] mt-1.5 font-medium">Real-time performance metrics and lead health analytics.</p>
        </div>
        <div className="flex bg-[#f1f5f9] p-1 rounded-xl gap-1">
          {['Day', 'Week', 'Month'].map((p) => (
            <button key={p} className={cn(
              "px-4 py-1.5 rounded-lg text-[12px] font-bold transition-all",
              p === 'Week' ? "bg-white text-[#111827] shadow-sm" : "text-[#64748b] hover:text-[#111827]"
            )}>
              {p}
            </button>
          ))}
        </div>
      </div>

      {/* ── Error Alert ── */}
      {error && (
        <div className="p-4 rounded-xl bg-[#fef2f2] border border-[#fca5a5]/30 flex items-center gap-3 text-[#991b1b] text-sm font-medium">
          <AlertCircle size={18} />
          {error}
        </div>
      )}

      {/* ── Key Metrics Grid ── */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          icon={Users}
          label="Total Prospects"
          value={analytics?.total_prospects || '0'}
          color="text-[#2563eb]"
          bg="bg-[#2563eb]/5"
        />
        <StatCard
          icon={Zap}
          label="Hot Leads Identifier"
          value={analytics?.hot_leads || '0'}
          color="text-[#eab308]"
          bg="bg-[#eab308]/5"
        />
        <StatCard
          icon={Target}
          label="Quality Score"
          value={analytics?.avg_lead_score.toFixed(1) || '0'}
          subtext="Internal Quality Index"
          color="text-[#7c3aed]"
          bg="bg-[#7c3aed]/5"
        />
        <StatCard
          icon={TrendingUp}
          label="Success Probability"
          value={`${analytics?.conversion_rate.toFixed(1) || '0'}%`}
          color="text-[#059669]"
          bg="bg-[#059669]/5"
        />
      </div>

      {/* ── Visual Analytics ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Grade Distribution */}
        <div className="bg-white border border-[#e5e7eb] rounded-[32px] p-8 shadow-[0_8px_30px_rgb(0,0,0,0.04)] reveal-animation">
          <div className="flex items-center justify-between mb-8">
            <h3 className="text-xl font-bold text-[#111827]">Lead Grade <span className="text-[#2563eb]">Distribution</span></h3>
            <PieChart size={20} className="text-[#9ca3af]" />
          </div>

          <div className="space-y-6">
            {analytics && Object.entries(analytics.grade_distribution).map(([grade, count]) => {
              const total = analytics.total_prospects || 1;
              const percentage = (count / total) * 100;
              const gradeColors = {
                A: { bar: 'bg-[#2563eb]', label: 'text-[#2563eb]', bg: 'bg-[#2563eb]/5' },
                B: { bar: 'bg-[#059669]', label: 'text-[#059669]', bg: 'bg-[#059669]/5' },
                C: { bar: 'bg-[#eab308]', label: 'text-[#eab308]', bg: 'bg-[#eab308]/5' },
                D: { bar: 'bg-[#ea580c]', label: 'text-[#ea580c]', bg: 'bg-[#ea580c]/5' },
                F: { bar: 'bg-[#dc2626]', label: 'text-[#dc2626]', bg: 'bg-[#dc2626]/5' },
              };
              const colors = gradeColors[grade as keyof typeof gradeColors];

              return (
                <div key={grade}>
                  <div className="flex justify-between items-center mb-2">
                    <div className="flex items-center gap-3">
                      <div className={cn("w-7 h-7 rounded-lg flex items-center justify-center font-bold text-[12px]", colors.bg, colors.label)}>
                        {grade}
                      </div>
                      <span className="text-[13px] font-bold text-[#475569]">Performance Level</span>
                    </div>
                    <span className="text-[13px] font-bold text-[#111827]">{count} Records</span>
                  </div>
                  <div className="w-full h-2 bg-[#f1f5f9] rounded-full overflow-hidden">
                    <div
                      className={cn("h-full rounded-full transition-all duration-1000", colors.bar)}
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Pipeline Velocity */}
        <div className="bg-white border border-[#e5e7eb] rounded-[32px] p-8 shadow-[0_8px_30px_rgb(0,0,0,0.04)] reveal-animation">
          <div className="flex items-center justify-between mb-8">
            <h3 className="text-xl font-bold text-[#111827]">Network <span className="text-[#ea580c]">Velocity</span></h3>
            <Activity size={20} className="text-[#9ca3af]" />
          </div>

          <div className="space-y-4">
            <div className="p-6 bg-[#f9fafb] rounded-[20px] border border-[#f1f5f9] hover:border-[#2563eb]/20 transition-all">
              <div className="flex justify-between items-start mb-3">
                <p className="text-[13px] text-[#6b7280] font-bold uppercase tracking-wider">Weekly Influx</p>
                <div className="p-1 px-2 rounded-lg bg-[#f0fdf4] text-[#166534] text-[11px] font-bold">+12.4%</div>
              </div>
              <h2 className="text-4xl font-bold text-[#111827]">
                {analytics?.pipeline_velocity || '0'} <span className="text-[#94a3b8] text-lg">leads</span>
              </h2>
            </div>

            <div className="p-6 bg-[#f9fafb] rounded-[20px] border border-[#f1f5f9] hover:border-[#7c3aed]/20 transition-all">
              <p className="text-[13px] text-[#6b7280] font-bold uppercase tracking-wider mb-3">Avg Maturation Time</p>
              <h2 className="text-4xl font-bold text-[#111827]">
                3.2 <span className="text-[#94a3b8] text-lg font-medium tracking-normal">days / lead</span>
              </h2>
            </div>
            
            <div className="p-6 bg-[#f9fafb] rounded-[20px] border border-[#f1f5f9] hover:border-[#059669]/20 transition-all">
              <p className="text-[13px] text-[#6b7280] font-bold uppercase tracking-wider mb-3">Conversion Velocity</p>
              <h2 className="text-4xl font-bold text-[#111827]">
                24 <span className="text-[#94a3b8] text-lg font-medium tracking-normal">% / month</span>
              </h2>
            </div>
          </div>
        </div>
      </div>

      {/* ── Performance Details ── */}
      <div className="bg-white border border-[#e5e7eb] rounded-[32px] p-8 shadow-[0_8px_30px_rgb(0,0,0,0.04)] reveal-animation">
        <div className="flex items-center justify-between mb-8">
          <h3 className="text-xl font-bold text-[#111827]">Campaign <span className="text-[#2563eb]">Fidelity</span></h3>
          <BarChart3 size={20} className="text-[#9ca3af]" />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[
            { name: 'Q2 Strategic Outreach', enrolled: 45, opened: 18, clicked: 12, color: 'border-[#2563eb]/20' },
            { name: 'High-Impact Signals', enrolled: 32, opened: 16, clicked: 14, color: 'border-[#059669]/20' },
            { name: 'Autonomous Nurturing', enrolled: 28, opened: 14, clicked: 11, color: 'border-[#eab308]/20' },
          ].map((campaign, idx) => (
            <div key={idx} className={cn("p-6 bg-[#f9fafb] rounded-[24px] border border-[#f1f5f9] hover:bg-white transition-all group", `hover:${campaign.color}`)}>
              <div className="flex items-center justify-between mb-6">
                <p className="font-bold text-[#111827] text-[15px]">{campaign.name}</p>
                <div className="w-8 h-8 rounded-full bg-white border border-[#e5e7eb] flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all">
                  <ArrowRight size={14} className="text-[#2563eb]" />
                </div>
              </div>

              <div className="space-y-4">
                {[
                  { label: 'Engaged', value: campaign.opened, total: campaign.enrolled, color: 'bg-[#2563eb]' },
                  { label: 'Activated', value: campaign.clicked, total: campaign.enrolled, color: 'bg-[#059669]' },
                ].map((row, i) => (
                  <div key={i}>
                    <div className="flex justify-between text-[12px] font-bold mb-1.5 uppercase tracking-wider">
                      <span className="text-[#94a3b8]">{row.label}</span>
                      <span className="text-[#111827] text-[14px]">{(row.value / row.total * 100).toFixed(0)}%</span>
                    </div>
                    <div className="w-full h-1.5 bg-[#f1f5f9] rounded-full overflow-hidden">
                      <div className={cn("h-full rounded-full transition-all duration-1000", row.color)} style={{ width: `${(row.value / row.total * 100)}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

