"use client";

import React from 'react';
import { Search, Bell, User, HelpCircle, Menu } from 'lucide-react';
import { cn } from '@/lib/utils';

export default function Navbar({ onToggleSidebar }: { onToggleSidebar: () => void }) {
  return (
    <div className="h-full px-6 flex items-center justify-between bg-white/70 backdrop-blur-xl border border-white/40 m-2 rounded-[24px] shadow-[0_8px_30px_rgba(0,0,0,0.02)]">
      {/* Left Section: Toggle & Search */}
      <div className="flex items-center gap-6">
        <button 
          onClick={onToggleSidebar}
          className="p-2.5 rounded-xl hover:bg-[#f3f4f6] transition-all text-[#6b7280] hover:text-[#111827] active:scale-95"
          aria-label="Toggle Sidebar"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-3 bg-[#f3f4f6]/50 px-4 py-2 rounded-xl border border-[#e5e7eb] w-[350px] group focus-within:bg-white focus-within:ring-4 focus-within:ring-[#2563eb]/5 focus-within:border-[#2563eb]/30 transition-all duration-300">
          <Search className="w-4 h-4 text-[#9ca3af] group-focus-within:text-[#2563eb] transition-colors" />
          <input
            type="text"
            placeholder="Search CRM..."
            className="bg-transparent border-none shadow-none outline-none text-[13px] text-[#111827] w-full placeholder:text-[#9ca3af] font-medium"
          />
        </div>
      </div>

      {/* Right Section */}
      <div className="flex items-center gap-2">
        <button className="p-2.5 rounded-xl hover:bg-[#f3f4f6] transition-all group text-[#6b7280]">
          <HelpCircle className="w-[18px] h-[18px]" />
        </button>
        
        <button className="p-2.5 rounded-xl hover:bg-[#f3f4f6] transition-all group relative text-[#6b7280]">
          <Bell className="w-[18px] h-[18px]" />
          <span className="absolute top-3 right-3 w-2 h-2 bg-[#ef4444] border-2 border-white rounded-full" />
        </button>

        <div className="w-[1px] h-6 bg-[#e5e7eb] mx-3" />

        <button className="flex items-center gap-3 pl-2 pr-1.5 py-1.5 rounded-xl hover:bg-[#f3f4f6] transition-all">
          <div className="text-right hidden md:block">
            <p className="text-[12px] font-bold text-[#111827] leading-none mb-0.5">Puneet Shivhare</p>
            <p className="text-[10px] font-medium text-[#6b7280]">Sales Intelligence</p>
          </div>
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[#2563eb]/10 to-[#2563eb]/20 flex items-center justify-center border border-[#2563eb]/10 overflow-hidden shadow-sm">
            <User className="w-5 h-5 text-[#2563eb]" />
          </div>
        </button>
      </div>
    </div>
  );
}
