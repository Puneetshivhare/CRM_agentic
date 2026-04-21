"use client";

import React, { useState } from 'react';
import { X, Plus, Trash2, Mail, MessageSquare, Send, Zap, Sparkles, Clock } from 'lucide-react';
import { cn } from '@/lib/utils';

interface Step {
  day: number;
  subject: string;
  body: string;
}

interface CreateCampaignModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (formData: { name: string; description: string; sequence_steps: Step[] }) => Promise<void>;
  loading: boolean;
}

export default function CreateCampaignModal({ isOpen, onClose, onSubmit, loading }: CreateCampaignModalProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [steps, setSteps] = useState<Step[]>([{ day: 0, subject: '', body: '' }]);

  if (!isOpen) return null;

  const handleAddStep = () => {
    setSteps([...steps, { day: steps.length * 2, subject: '', body: '' }]);
  };

  const handleRemoveStep = (index: number) => {
    if (steps.length === 1) return;
    setSteps(steps.filter((_, i) => i !== index));
  };

  const handleStepChange = (index: number, field: keyof Step, value: string | number) => {
    const newSteps = [...steps];
    newSteps[index] = { ...newSteps[index], [field]: value };
    setSteps(newSteps);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    await onSubmit({ name, description, sequence_steps: steps });
    setName('');
    setDescription('');
    setSteps([{ day: 0, subject: '', body: '' }]);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div 
        className="absolute inset-0 bg-[#0f172a]/40 backdrop-blur-sm transition-opacity animate-in fade-in duration-300" 
        onClick={onClose} 
      />
      
      <div className="relative bg-white w-full max-w-3xl rounded-[32px] shadow-[0_24px_80px_rgba(0,0,0,0.18)] overflow-hidden flex flex-col max-h-[92vh] animate-in zoom-in-95 slide-in-from-bottom-4 duration-400">
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-[#2563eb] via-[#8b5cf6] to-[#ec4899]" />
        
        {/* Header */}
        <div className="px-10 py-8 border-b border-[#f3f4f6] flex items-center justify-between bg-[#fcfcfd]/50">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-[#eff6ff] flex items-center justify-center text-[#2563eb] shadow-sm transform rotate-3">
               <Send size={24} />
            </div>
            <div>
              <h2 className="text-xl font-black text-[#111827] tracking-tight">Orchestrate Sequence</h2>
              <p className="text-[13px] text-[#6b7280] font-medium mt-0.5">Design multi-stage automated outreach workflows.</p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-2.5 hover:bg-[#f3f4f6] rounded-2xl text-[#9ca3af] hover:text-[#111827] transition-all"
          >
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-10 space-y-10 custom-scrollbar">
          {/* Basic Info */}
          <section className="space-y-6">
            <div className="px-4 text-[11px] font-black text-[#2563eb] uppercase tracking-[0.25em]">Global Parameters</div>
            
            <div className="grid grid-cols-2 gap-6">
              <div className="col-span-2 space-y-2">
                <label className="block text-[11px] font-black text-[#9ca3af] uppercase tracking-wider ml-1">Sequence Designation</label>
                <div className="relative group">
                   <Zap className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-[#9ca3af] group-focus-within:text-[#2563eb] transition-colors" />
                   <input
                     type="text"
                     required
                     placeholder="e.g. Q2 Enterprise Growth Sequence"
                     className="w-full bg-[#f9fafb] border border-[#e5e7eb] rounded-2xl py-3.5 pl-11 pr-4 text-sm font-bold text-[#111827] outline-none focus:bg-white focus:ring-4 focus:ring-[#2563eb]/5 focus:border-[#2563eb]/40 transition-all shadow-sm"
                     value={name}
                     onChange={(e) => setName(e.target.value)}
                   />
                </div>
              </div>
              
              <div className="col-span-2 space-y-2">
                <label className="block text-[11px] font-black text-[#9ca3af] uppercase tracking-wider ml-1">Strategic Objective</label>
                <textarea
                  rows={2}
                  placeholder="Define the core intent of this automated orchestration..."
                  className="w-full bg-[#f9fafb] border border-[#e5e7eb] rounded-2xl px-5 py-3.5 text-sm font-bold text-[#111827] outline-none focus:bg-white focus:ring-4 focus:ring-[#2563eb]/5 focus:border-[#2563eb]/40 transition-all shadow-sm resize-none"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                />
              </div>
            </div>
          </section>

          {/* Steps */}
          <section className="space-y-6">
            <div className="flex items-center justify-between px-4">
              <div className="text-[11px] font-black text-[#2563eb] uppercase tracking-[0.25em]">Workflow Architecture</div>
              <button 
                type="button"
                onClick={handleAddStep}
                className="text-[11px] font-black text-[#2563eb] flex items-center gap-2 px-4 py-2 bg-[#eff6ff] hover:bg-[#dbeafe] rounded-xl transition-all shadow-sm border border-[#2563eb]/10"
              >
                <Plus size={14} strokeWidth={3} /> Append Step
              </button>
            </div>

            <div className="space-y-6">
              {steps.map((step, idx) => (
                <div key={idx} className="group relative bg-[#fcfcfd] border border-[#e5e7eb] rounded-[28px] p-8 space-y-6 hover:border-[#2563eb]/30 hover:shadow-[0_8px_30px_rgb(0,0,0,0.03)] transition-all">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 rounded-xl bg-white border border-[#e5e7eb] flex items-center justify-center text-[14px] font-black text-[#111827] shadow-sm transform group-hover:scale-110 transition-transform">
                        {idx + 1}
                      </div>
                      <div className="flex items-center gap-3 bg-white border border-[#e5e7eb] rounded-xl px-4 py-2 shadow-sm">
                        <Clock size={14} className="text-[#9ca3af]" />
                        <span className="text-[12px] font-bold text-[#4b5563]">Delay Distribution:</span>
                        <input
                          type="number"
                          className="w-12 bg-transparent border-none text-[12px] font-black text-[#2563eb] outline-none"
                          value={step.day}
                          onChange={(e) => handleStepChange(idx, 'day', parseInt(e.target.value) || 0)}
                        />
                        <span className="text-[12px] font-bold text-[#4b5563]">Days</span>
                      </div>
                    </div>
                    {steps.length > 1 && (
                      <button 
                        type="button"
                        onClick={() => handleRemoveStep(idx)}
                        className="p-2.5 opacity-0 group-hover:opacity-100 text-[#9ca3af] hover:text-[#ef4444] hover:bg-[#fef2f2] rounded-xl transition-all"
                      >
                        <Trash2 size={18} />
                      </button>
                    )}
                  </div>

                  <div className="space-y-4">
                    <div className="relative group/input">
                      <div className="absolute left-4 top-1/2 -translate-y-1/2 w-8 h-8 rounded-lg bg-[#f9fafb] border border-[#e5e7eb] flex items-center justify-center text-[#9ca3af] group-focus-within/input:text-[#2563eb] group-focus-within/input:bg-[#eff6ff] transition-all">
                        <Mail size={14} strokeWidth={2.5} />
                      </div>
                      <input
                        type="text"
                        placeholder="Subject Line Hook"
                        className="w-full bg-white border border-[#e5e7eb] rounded-2xl pl-16 pr-4 py-3.5 text-sm font-bold text-[#111827] outline-none focus:ring-4 focus:ring-[#2563eb]/5 focus:border-[#2563eb]/40 transition-all shadow-sm"
                        value={step.subject}
                        onChange={(e) => handleStepChange(idx, 'subject', e.target.value)}
                      />
                    </div>
                    <div className="relative">
                      <div className="absolute left-4 top-4 w-8 h-8 rounded-lg bg-[#f9fafb] border border-[#e5e7eb] flex items-center justify-center text-[#9ca3af]">
                        <MessageSquare size={14} strokeWidth={2.5} />
                      </div>
                      <textarea
                        rows={5}
                        placeholder="Core Message Payload..."
                        className="w-full bg-white border border-[#e5e7eb] rounded-2xl pl-16 pr-4 py-4 text-sm font-medium text-[#4b5563] outline-none focus:ring-4 focus:ring-[#2563eb]/5 focus:border-[#2563eb]/40 transition-all shadow-sm resize-none"
                        value={step.body}
                        onChange={(e) => handleStepChange(idx, 'body', e.target.value)}
                      />
                      <div className="absolute right-4 bottom-4 flex items-center gap-2">
                        <span className="text-[9px] font-black text-[#9ca3af] uppercase tracking-widest bg-[#f9fafb] px-2 py-1 rounded border border-[#e5e7eb]">
                           Use {'{first_name}'} variables
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </form>

        {/* Footer */}
        <div className="px-10 py-8 border-t border-[#f3f4f6] bg-[#fcfcfd]/80 backdrop-blur-md flex items-center justify-between gap-4">
           <div className="flex items-center gap-3 text-[#9ca3af]">
              <Sparkles size={16} />
              <span className="text-[11px] font-black uppercase tracking-[0.15em]">AI Compliance check active</span>
           </div>
           <div className="flex gap-4">
            <button
              type="button"
              onClick={onClose}
              className="px-8 py-3.5 rounded-2xl text-sm font-black text-[#6b7280] hover:bg-[#f3f4f6] active:scale-[0.98] transition-all"
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              disabled={loading || !name.trim()}
              className="px-10 py-3.5 bg-[#2563eb] text-white rounded-2xl text-sm font-black shadow-[0_12px_28px_-6px_rgba(37,99,235,0.4)] hover:scale-[1.02] active:scale-[0.98] transition-all disabled:opacity-50 flex items-center gap-2"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Provisioning...</span>
                </>
              ) : (
                <>
                  <Send size={18} strokeWidth={2.5} />
                  <span>Launch Sequence</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
