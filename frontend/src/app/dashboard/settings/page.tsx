"use client";

import React, { useState } from 'react';
import { 
  User, 
  Bell, 
  Shield, 
  Key, 
  Database, 
  Save, 
  ExternalLink,
  ChevronRight,
  Globe,
  Lock,
  Cpu
} from 'lucide-react';
import { cn } from '@/lib/utils';

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState('general');

  const tabs = [
    { id: 'general', name: 'Profile & Account', icon: User, description: 'Personal info and branding' },
    { id: 'notifications', name: 'Intelligence Alerts', icon: Bell, description: 'Signal notification rules' },
    { id: 'security', name: 'Security & Access', icon: Shield, description: 'Authentication and logs' },
    { id: 'api', name: 'API & Connections', icon: Key, description: 'Third-party integrations' },
    { id: 'data', name: 'Data Foundry', icon: Database, description: 'Export and cleanup rules' },
  ];

  return (
    <div className="space-y-8 animate-in fade-in duration-700">
      {/* Header */}
      <div className="border-b border-[#e5e7eb] pb-6">
        <h1 className="text-3xl font-bold text-[#111827] tracking-tight">System Configuration</h1>
        <p className="text-[#6b7280] mt-1.5 font-medium">Fine-tune your workspace environment and research parameters.</p>
      </div>

      <div className="flex gap-10">
        {/* Navigation Sidebar */}
        <aside className="w-80 space-y-2 mt-4">
          <p className="px-4 text-[11px] font-black text-[#9ca3af] uppercase tracking-[0.2em] mb-4">Preference Layers</p>
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                "w-full group flex items-start gap-4 px-4 py-4 rounded-[20px] transition-all duration-300",
                activeTab === tab.id
                  ? 'bg-white text-[#2563eb] shadow-[0_8px_30px_rgba(0,0,0,0.04)] border border-[#e5e7eb]'
                  : 'text-[#6b7280] hover:bg-[#f3f4f6] hover:text-[#111827] border border-transparent'
              )}
            >
              <div className={cn(
                "p-2.5 rounded-xl transition-all",
                activeTab === tab.id ? "bg-[#eff6ff] text-[#2563eb]" : "bg-[#f9fafb] text-[#9ca3af] group-hover:text-[#111827]"
              )}>
                <tab.icon size={18} />
              </div>
              <div className="text-left">
                <p className="text-[13px] font-bold leading-tight mb-0.5">{tab.name}</p>
                <p className="text-[11px] font-medium text-[#9ca3af] group-hover:text-[#6b7280] transition-colors">{tab.description}</p>
              </div>
              {activeTab === tab.id && <ChevronRight size={14} className="ml-auto mt-1 opacity-40" />}
            </button>
          ))}
        </aside>

        {/* Content Area */}
        <main className="flex-1">
          <div className="bg-white border border-[#e5e7eb] rounded-[32px] shadow-[0_12px_40px_rgb(0,0,0,0.03)] overflow-hidden">
            {/* Tab Header */}
            <div className="px-10 py-8 border-b border-[#f3f4f6] bg-[#fcfcfd]/50">
               <h2 className="text-xl font-bold text-[#111827]">
                  {tabs.find(t => t.id === activeTab)?.name}
               </h2>
               <p className="text-[13px] text-[#6b7280] font-medium mt-1">
                  Manage your {activeTab} preferences and global system behaviors.
               </p>
            </div>

            {/* Tab Content */}
            <div className="p-10">
              {activeTab === 'general' ? (
                <div className="space-y-10 animate-in slide-in-from-bottom-2 duration-500">
                  <div className="grid grid-cols-2 gap-10">
                    <section className="space-y-6">
                       <div className="flex items-center gap-3 mb-2">
                          <div className="w-8 h-8 rounded-lg bg-[#eff6ff] flex items-center justify-center text-[#2563eb]">
                             <User size={16} />
                          </div>
                          <h3 className="font-bold text-[#111827]">Account Identity</h3>
                       </div>
                       
                       <div className="space-y-5">
                          <div className="space-y-2">
                            <label className="text-[11px] font-black text-[#9ca3af] uppercase tracking-widest ml-1">Full Identity</label>
                            <input 
                              type="text" 
                              defaultValue="Puneet Shivhare" 
                              className="w-full bg-[#f9fafb] border border-[#e5e7eb] rounded-2xl px-5 py-3.5 text-sm font-bold text-[#111827] focus:bg-white focus:ring-4 focus:ring-[#2563eb]/5 focus:border-[#2563eb]/40 outline-none transition-all shadow-sm"
                            />
                          </div>
                          
                          <div className="space-y-2">
                            <label className="text-[11px] font-black text-[#9ca3af] uppercase tracking-widest ml-1">Strategic Role</label>
                            <input 
                              type="text" 
                              defaultValue="Growth Intelligence Officer" 
                              className="w-full bg-[#f9fafb] border border-[#e5e7eb] rounded-2xl px-5 py-3.5 text-sm font-bold text-[#111827] focus:bg-white focus:ring-4 focus:ring-[#2563eb]/5 focus:border-[#2563eb]/40 outline-none transition-all shadow-sm"
                            />
                          </div>
                       </div>
                    </section>

                    <section className="space-y-6">
                       <div className="flex items-center gap-3 mb-2">
                          <div className="w-8 h-8 rounded-lg bg-[#fdf2f8] flex items-center justify-center text-[#db2777]">
                             <Globe size={16} />
                          </div>
                          <h3 className="font-bold text-[#111827]">Workspace Context</h3>
                       </div>

                       <div className="space-y-5">
                          <div className="space-y-2">
                            <label className="text-[11px] font-black text-[#9ca3af] uppercase tracking-widest ml-1">Dynamic Domain</label>
                            <div className="flex items-center gap-2">
                              <div className="flex-1 flex items-center bg-[#f9fafb] border border-[#e5e7eb] rounded-2xl px-5 py-3.5 group focus-within:bg-white focus-within:ring-4 focus-within:ring-[#2563eb]/5 focus-within:border-[#2563eb]/40 transition-all shadow-sm">
                                <span className="text-[#9ca3af] text-sm font-medium pr-1">agent.clay.io/</span>
                                <input 
                                  type="text" 
                                  defaultValue="puneet-alpha" 
                                  className="bg-transparent border-none outline-none text-sm font-bold text-[#111827] w-full"
                                />
                              </div>
                            </div>
                          </div>

                          <div className="space-y-2">
                             <label className="text-[11px] font-black text-[#9ca3af] uppercase tracking-widest ml-1">System Language</label>
                             <select className="w-full bg-[#f9fafb] border border-[#e5e7eb] rounded-2xl px-5 py-3.5 text-sm font-bold text-[#111827] outline-none appearance-none shadow-sm">
                                <option>English (United States)</option>
                                <option>English (United Kingdom)</option>
                             </select>
                          </div>
                       </div>
                    </section>
                  </div>

                  <div className="pt-8 border-t border-[#f3f4f6] flex items-center justify-between">
                    <div className="flex items-center gap-2.5 text-[#9ca3af]">
                       <Lock size={14} />
                       <span className="text-[11px] font-bold uppercase tracking-wider">End-to-end encrypted transfer</span>
                    </div>
                    <button className="bg-[#2563eb] text-white px-8 py-3.5 rounded-2xl text-sm font-black flex items-center gap-2 shadow-[0_12px_28px_-6px_rgba(37,99,235,0.4)] hover:scale-[1.02] active:scale-[0.98] transition-all">
                      <Save size={18} strokeWidth={2.5} />
                      Commit Changes
                    </button>
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-20 text-center space-y-5 animate-in zoom-in-95 duration-500">
                  <div className="w-20 h-20 rounded-[28px] bg-[#f9fafb] flex items-center justify-center border border-[#e5e7eb] shadow-sm transform -rotate-3">
                    <Cpu size={36} className="text-[#9ca3af]" />
                  </div>
                  <div className="max-w-xs">
                    <p className="text-lg font-black text-[#111827] tracking-tight">Security Gated Panel</p>
                    <p className="text-[13px] text-[#6b7280] font-medium leading-relaxed mt-1">
                      This configuration layer is locked to prevent unauthorized tampering with core intelligence logic.
                    </p>
                  </div>
                  <button className="text-[12px] font-bold text-[#2563eb] px-6 py-2 rounded-xl bg-white border border-[#e5e7eb] hover:bg-[#f3f4f6] transition-all">
                     Request Access
                  </button>
                </div>
              )}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
