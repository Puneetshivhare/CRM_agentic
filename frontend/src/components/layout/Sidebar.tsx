"use client";

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  Users,
  Settings,
  Zap,
  FileText,
  BarChart3,
  LogOut,
  Building2,
  Mail,
  Workflow,
  Sparkles,
} from 'lucide-react';
import { cn } from '@/lib/utils';

const navItems = [
  { name: 'Dashboard', icon: LayoutDashboard, href: '/dashboard' },
  { name: 'Prospects', icon: Users, href: '/dashboard/prospects' },
  { name: 'Companies', icon: Building2, href: '/dashboard/companies' },
  { name: 'Campaigns', icon: Mail, href: '/dashboard/campaigns' },
  { name: 'Enrichment', icon: Sparkles, href: '/dashboard/enrichment' },
  { name: 'Rules', icon: Workflow, href: '/dashboard/rules' },
  { name: 'Analytics', icon: BarChart3, href: '/dashboard/analytics' },
  { name: 'Settings', icon: Settings, href: '/dashboard/settings' },
];

export default function Sidebar({ isCollapsed }: { isCollapsed: boolean }) {
  const pathname = usePathname();

  return (
    <div className={cn(
      "flex flex-col h-full bg-white transition-all duration-300 ease-in-out overflow-hidden m-2 rounded-[24px] shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-[#f3f4f6]"
    )}>
      {/* Logo Section */}
      <div className={cn(
        "p-6 transition-all duration-300 ease-in-out",
        isCollapsed ? "px-4 pb-8" : "p-8 pb-10"
      )}>
        <Link href="/dashboard" className="flex items-center gap-3 group">
          <div className="w-10 h-10 min-w-[40px] rounded-[14px] bg-gradient-to-br from-[#2563eb] to-[#1e40af] flex items-center justify-center transition-all duration-500 group-hover:rotate-[10deg] group-hover:scale-110 shadow-[0_8px_20px_-4px_rgba(37,99,235,0.3)]">
            <Zap className="w-5 h-5 text-white fill-white" />
          </div>
          {!isCollapsed && (
            <div className="flex flex-col whitespace-nowrap opacity-100 transition-opacity duration-300">
              <span className="font-display text-xl font-bold tracking-tight text-[#111827] leading-none">
                Clay<span className="text-[#2563eb]">CRM</span>
              </span>
              <span className="text-[10px] font-bold text-[#9ca3af] uppercase tracking-[0.1em] mt-1">Intelligence OS</span>
            </div>
          )}
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 space-y-1 overflow-y-auto no-scrollbar">
        {!isCollapsed && (
          <div className="text-[10px] font-bold text-[#9ca3af] uppercase tracking-[0.2em] px-4 mb-4 mt-2 whitespace-nowrap">
            Intelligence
          </div>
        )}
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center rounded-xl transition-all duration-200 group relative",
                isCollapsed ? "justify-center px-0 py-2.5" : "gap-3 px-4 py-2.5",
                isActive
                  ? "bg-white text-[#111827] font-semibold border border-[#e5e7eb] shadow-[0_2px_4px_rgba(0,0,0,0.02)]"
                  : "text-[#6b7280] hover:text-[#111827] hover:bg-[#f9fafb]"
              )}
              title={isCollapsed ? item.name : undefined}
            >
              <item.icon className={cn(
                "w-[18px] h-[18px] transition-colors duration-200 shrink-0",
                isActive ? "text-[#2563eb]" : "text-[#9ca3af] group-hover:text-[#4b5563]"
              )} />
              {!isCollapsed && (
                <span className="text-[13px] tracking-tight whitespace-nowrap opacity-100 transition-opacity duration-300">{item.name}</span>
              )}
              {isActive && (
                <div className="absolute left-0 w-1 h-5 bg-[#2563eb] rounded-r-full" />
              )}
            </Link>
          );
        })}
      </nav>

      {/* Footer / User Area */}
      <div className={cn(
        "p-4 border-t border-[#f3f4f6] transition-all duration-300",
        isCollapsed ? "px-2" : "p-6"
      )}>
        <button
          className={cn(
            "w-full flex items-center rounded-xl text-[#6b7280] hover:text-[#ef4444] hover:bg-[#fef2f2] transition-all text-[13px] font-medium group",
            isCollapsed ? "justify-center p-3" : "gap-3 px-4 py-3"
          )}
          onClick={() => {
            localStorage.removeItem('crm_token');
            window.location.href = '/login';
          }}
          title={isCollapsed ? "Sign Out" : undefined}
        >
          <LogOut className="w-[18px] h-[18px] text-[#9ca3af] group-hover:text-[#ef4444] transition-colors shrink-0" />
          {!isCollapsed && (
            <span className="whitespace-nowrap">Sign Out</span>
          )}
        </button>
      </div>
    </div>
  );
}
