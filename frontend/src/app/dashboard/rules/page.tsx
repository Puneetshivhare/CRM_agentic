"use client";

import React, { useState, useEffect } from 'react';
import {
  Zap,
  Plus,
  AlertCircle,
  CheckCircle2,
  Clock,
  Trash2,
  Eye,
  Activity,
  ArrowRight,
  Settings2,
  ChevronRight
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface Rule {
  rule_id: number;
  name: string;
  description?: string;
  trigger_event: string;
  conditions: Record<string, any>;
  actions: Array<{ action_type: string; action_params: Record<string, any> }>;
  is_active: boolean;
  execution_count: number;
  last_executed_at?: string;
  created_at: string;
  updated_at: string;
}

interface RulesData {
  total: number;
  page: number;
  per_page: number;
  items: Rule[];
}

const RuleStatusBadge = ({ isActive }: { isActive: boolean }) => {
  return (
    <div className={cn(
      "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[12px] font-bold border transition-all",
      isActive 
        ? "bg-[#f0fdf4] text-[#166534] border-[#166534]/10 shadow-[0_2px_10px_-4px_rgba(22,101,52,0.2)]" 
        : "bg-[#f9fafb] text-[#6b7280] border-[#e5e7eb]"
    )}>
      <div className={cn("w-1.5 h-1.5 rounded-full shadow-sm", isActive ? "bg-[#166534] animate-pulse" : "bg-[#9ca3af]")} />
      {isActive ? "Active" : "Paused"}
    </div>
  );
};

export default function RulesPage() {
  const [rules, setRules] = useState<RulesData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newRule, setNewRule] = useState({
    name: '',
    description: '',
    trigger_event: 'enrichment_complete',
    actions: [{ action_type: 'send_email', action_params: {} }],
  });

  const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8005/api';

  useEffect(() => {
    const fetchRules = async () => {
      try {
        setLoading(true);
        const token = localStorage.getItem('crm_token');
        if (!token) {
          window.location.href = '/login';
          return;
        }

        const response = await fetch(`${baseUrl}/rules?page=${page}&per_page=20`, {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (response.status === 401) {
          localStorage.removeItem('crm_token');
          window.location.href = '/login';
          return;
        }

        if (!response.ok) throw new Error('Failed to load rules');

        const data = await response.json();
        setRules(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load rules');
        setRules(null);
      } finally {
        setLoading(false);
      }
    };

    fetchRules();
  }, [page, baseUrl]);

  const handleCreateRule = async () => {
    if (!newRule.name) {
      alert('Rule name is required');
      return;
    }

    try {
      const token = localStorage.getItem('crm_token');
      if (!token) {
        window.location.href = '/login';
        return;
      }

      const response = await fetch(`${baseUrl}/rules`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          name: newRule.name,
          description: newRule.description,
          trigger_event: newRule.trigger_event,
          conditions: {},
          actions: newRule.actions,
          is_active: true,
        })
      });

      if (!response.ok) throw new Error('Failed to create rule');

      setShowCreateModal(false);
      setNewRule({
        name: '',
        description: '',
        trigger_event: 'enrichment_complete',
        actions: [{ action_type: 'send_email', action_params: {} }],
      });
      setPage(1);
    } catch (err) {
      alert('❌ Error: ' + (err instanceof Error ? err.message : 'Failed to create rule'));
    }
  };

  const handleDeleteRule = async (ruleId: number) => {
    if (!confirm('Delete this automation rule?')) return;

    try {
      const token = localStorage.getItem('crm_token');
      if (!token) {
        window.location.href = '/login';
        return;
      }

      const response = await fetch(`${baseUrl}/rules/${ruleId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        setPage(1);
      } else {
        throw new Error('Failed to delete');
      }
    } catch (err) {
      alert('❌ Error: ' + (err instanceof Error ? err.message : 'Failed to delete rule'));
    }
  };

  return (
    <div className="space-y-10">
      {/* ── Header ── */}
      <div className="flex items-end justify-between border-b border-[#e5e7eb] pb-6 reveal-animation">
        <div>
          <h1 className="text-3xl font-bold text-[#111827] tracking-tight">Automation Rules</h1>
          <p className="text-[#6b7280] mt-1.5 font-medium">Build event-triggered workflows to automate prospect management.</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 bg-[#2563eb] text-white px-5 py-2.5 rounded-xl text-sm font-bold shadow-[0_8px_20px_-4px_rgba(37,99,235,0.3)] hover:scale-[1.02] active:scale-[0.98] transition-all"
        >
          <Plus size={18} strokeWidth={3} />
          <span>New Rule</span>
        </button>
      </div>

      {/* ── Table Container ── */}
      <div className="bg-white border border-[#e5e7eb] rounded-2xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] overflow-hidden reveal-animation">
        <div className="px-8 py-5 border-b border-[#f3f4f6] flex items-center justify-between">
          <div className="text-[11px] font-bold text-[#9ca3af] uppercase tracking-[0.15em]">
            Active Workflows ({rules?.total || 0})
          </div>
        </div>

        {error && (
          <div className="m-6 p-4 bg-[#fef2f2] border border-[#fca5a5]/30 rounded-xl flex items-center gap-3 text-[#991b1b] text-sm font-medium">
            <AlertCircle size={18} />
            {error}
          </div>
        )}

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-[#f9fafb] border-b border-[#e5e7eb]">
                <th className="px-8 py-4 text-[11px] font-bold text-[#9ca3af] uppercase tracking-[0.2em]">Rule Identifier</th>
                <th className="px-6 py-4 text-[11px] font-bold text-[#9ca3af] uppercase tracking-[0.2em]">Trigger</th>
                <th className="px-6 py-4 text-[11px] font-bold text-[#9ca3af] uppercase tracking-[0.2em]">Status</th>
                <th className="px-6 py-4 text-[11px] font-bold text-[#9ca3af] uppercase tracking-[0.2em]">Runs</th>
                <th className="px-8 py-4 text-[11px] font-bold text-[#9ca3af] uppercase tracking-[0.2em] text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#f3f4f6]">
              {loading ? (
                [...Array(5)].map((_, i) => (
                  <tr key={i} className="animate-pulse">
                    <td colSpan={5} className="px-8 py-6">
                      <div className="h-4 bg-[#f3f4f6] rounded-md w-1/3 mb-2" />
                      <div className="h-3 bg-[#f3f4f6] rounded-md w-1/2 opacity-50" />
                    </td>
                  </tr>
                ))
              ) : rules && rules.items.length > 0 ? (
                rules.items.map((rule) => (
                  <tr key={rule.rule_id} className="group hover:bg-[#f9fafb] transition-all duration-200">
                    <td className="px-8 py-5">
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 rounded-xl bg-[#2563eb]/5 flex items-center justify-center border border-[#2563eb]/10 group-hover:bg-[#2563eb]/10 transition-all">
                          <Settings2 size={18} className="text-[#2563eb]" />
                        </div>
                        <div>
                          <p className="text-[14px] font-bold text-[#111827]">{rule.name}</p>
                          <p className="text-[12px] text-[#6b7280] font-medium mt-0.5">{rule.description || 'No description provided'}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-5">
                      <div className="flex items-center gap-2">
                        <Zap size={14} className="text-[#eab308] fill-[#eab308]/20" />
                        <span className="text-[13px] font-bold text-[#475569] bg-[#f1f5f9] px-2 py-0.5 rounded-md border border-[#e2e8f0]">
                          {rule.trigger_event}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-5">
                      <RuleStatusBadge isActive={rule.is_active} />
                    </td>
                    <td className="px-6 py-5">
                      <div className="flex items-center gap-2 text-[14px] font-bold text-[#111827]">
                        <Activity size={14} className="text-[#94a3b8]" />
                        {rule.execution_count}
                      </div>
                    </td>
                    <td className="px-8 py-5">
                      <div className="flex items-center justify-end gap-2 opacity-0 group-hover:opacity-100 transition-all">
                        <button
                          className="p-2 rounded-lg bg-white border border-[#e5e7eb] hover:bg-[#f9fafb] hover:border-[#d1d5db] text-[#64748b] transition-all"
                          title="View Details"
                        >
                          <Eye size={16} />
                        </button>
                        <button
                          onClick={() => handleDeleteRule(rule.rule_id)}
                          className="p-2 rounded-lg bg-white border border-[#e5e7eb] hover:bg-[#fef2f2] hover:border-[#fca5a5] text-[#94a3b8] hover:text-[#dc2626] transition-all"
                          title="Delete Rule"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5} className="px-8 py-24 text-center">
                    <div className="flex flex-col items-center gap-4">
                      <div className="w-16 h-16 rounded-3xl bg-[#f9fafb] flex items-center justify-center border border-[#e5e7eb]">
                        <Zap size={32} className="text-[#9ca3af]" />
                      </div>
                      <div>
                        <p className="text-[#111827] text-[15px] font-bold">No automation rules</p>
                        <p className="text-[#6b7280] text-[13px] font-medium mt-1">Automate your workflow by creating your first rule.</p>
                      </div>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {rules && rules.total > rules.per_page && (
          <div className="px-8 py-5 border-t border-[#f3f4f6] bg-[#f9fafb]/50 flex items-center justify-between">
            <div className="text-[12px] font-bold text-[#9ca3af] uppercase tracking-wider">
              Page {page} of {Math.ceil(rules.total / rules.per_page)}
            </div>
            <div className="flex gap-2">
              <button
                className="px-4 py-2 rounded-xl bg-white border border-[#e5e7eb] text-[13px] font-bold text-[#475569] hover:bg-[#f9fafb] transition-all disabled:opacity-50 disabled:grayscale"
                disabled={page === 1 || loading}
                onClick={() => setPage(page - 1)}
              >
                Previous
              </button>
              <button
                className="px-4 py-2 rounded-xl bg-white border border-[#e5e7eb] text-[13px] font-bold text-[#475569] hover:bg-[#f9fafb] transition-all disabled:opacity-50 disabled:grayscale"
                disabled={page * rules.per_page >= rules.total || loading}
                onClick={() => setPage(page + 1)}
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {/* ── Create Rule Modal ── */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-[#0f172a]/40 backdrop-blur-[4px] flex items-center justify-center z-[100] p-6 animate-in fade-in duration-300">
          <div className="bg-white rounded-[24px] border border-[#e5e7eb] shadow-[0_20px_40px_-15px_rgba(0,0,0,0.1)] w-full max-w-lg overflow-hidden transform transition-all scale-100">
            <div className="px-8 py-6 border-b border-[#f3f4f6]">
              <h2 className="text-xl font-bold text-[#111827]">Create Automation Rule</h2>
              <p className="text-[13px] text-[#6b7280] font-medium mt-1.5">Define a trigger and action to automate your CRM tasks.</p>
            </div>

            <div className="p-8 space-y-6">
              <div>
                <label className="block text-[12px] font-bold text-[#9ca3af] uppercase tracking-wider mb-2">Rule Identifier</label>
                <input
                  type="text"
                  value={newRule.name}
                  onChange={(e) => setNewRule({ ...newRule, name: e.target.value })}
                  placeholder="e.g., Forward High-Score Leads"
                  className="w-full bg-[#f9fafb] border border-[#e5e7eb] rounded-xl py-2.5 px-4 text-sm font-medium outline-none focus:bg-white focus:border-[#2563eb] transition-all placeholder:text-[#9ca3af]"
                />
              </div>

              <div>
                <label className="block text-[12px] font-bold text-[#9ca3af] uppercase tracking-wider mb-2">Detailed Description</label>
                <textarea
                  value={newRule.description}
                  onChange={(e) => setNewRule({ ...newRule, description: e.target.value })}
                  placeholder="What should happens when this rule is triggered?"
                  className="w-full bg-[#f9fafb] border border-[#e5e7eb] rounded-xl py-2.5 px-4 text-sm font-medium outline-none focus:bg-white focus:border-[#2563eb] transition-all resize-none min-h-[80px] placeholder:text-[#9ca3af]"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-[12px] font-bold text-[#9ca3af] uppercase tracking-wider mb-2">When this happens</label>
                  <select
                    value={newRule.trigger_event}
                    onChange={(e) => setNewRule({ ...newRule, trigger_event: e.target.value })}
                    className="w-full bg-[#f9fafb] border border-[#e5e7eb] rounded-xl py-2.5 px-4 text-sm font-bold text-[#111827] outline-none focus:bg-white focus:border-[#2563eb] transition-all appearance-none cursor-pointer"
                  >
                    <option value="enrichment_complete">Enrichment Done</option>
                    <option value="lead_score_high">Score &gt; 80</option>
                    <option value="email_opened">Email Opened</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[12px] font-bold text-[#9ca3af] uppercase tracking-wider mb-2">Execute this action</label>
                  <select
                    value={newRule.actions[0]?.action_type || 'send_email'}
                    onChange={(e) => {
                      const actions = [{ action_type: e.target.value, action_params: {} }];
                      setNewRule({ ...newRule, actions });
                    }}
                    className="w-full bg-[#f9fafb] border border-[#e5e7eb] rounded-xl py-2.5 px-4 text-sm font-bold text-[#111827] outline-none focus:bg-white focus:border-[#2563eb] transition-all appearance-none cursor-pointer"
                  >
                    <option value="send_email">Send Email</option>
                    <option value="create_task">Create Task</option>
                    <option value="add_to_campaign">Add to Campaign</option>
                  </select>
                </div>
              </div>
            </div>

            <div className="px-8 py-6 bg-[#f9fafb] border-t border-[#f3f4f6] flex gap-3">
              <button
                onClick={() => setShowCreateModal(false)}
                className="flex-1 px-4 py-2.5 rounded-xl bg-white border border-[#e5e7eb] text-sm font-bold text-[#475569] hover:bg-[#f3f4f6] transition-all"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateRule}
                className="flex-1 px-4 py-2.5 rounded-xl bg-[#2563eb] text-white text-sm font-bold hover:bg-[#1d4ed8] transition-all shadow-[0_8px_20px_-4px_rgba(37,99,235,0.3)]"
              >
                Deploy Rule
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

