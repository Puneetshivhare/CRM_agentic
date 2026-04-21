"use client";

import React, { useRef } from 'react';
import { usePathname } from 'next/navigation';
import { gsap } from 'gsap';
import { useGSAP } from '@gsap/react';
import Sidebar from './Sidebar';
import Navbar from './Navbar';
import { cn } from '@/lib/utils';

export default function MainLayout({ children }: { children: React.ReactNode }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const pathname = usePathname();
  const [isSidebarCollapsed, setIsSidebarCollapsed] = React.useState<boolean>(false);
  const [isMounted, setIsMounted] = React.useState(false);

  // Persistence management
  React.useEffect(() => {
    try {
      const saved = localStorage.getItem("crm-sidebar-collapsed");
      if (saved !== null) {
        setIsSidebarCollapsed(saved === "true");
      }
    } catch (e) {
      console.error("Failed to load sidebar state", e);
    }
    setIsMounted(true);
  }, []);

  React.useEffect(() => {
    if (isMounted) {
      try {
        localStorage.setItem("crm-sidebar-collapsed", String(isSidebarCollapsed));
      } catch (e) {
        console.error("Failed to save sidebar state", e);
      }
    }
  }, [isSidebarCollapsed, isMounted]);

  useGSAP(() => {
    if (!isMounted) return;
    gsap.fromTo(".reveal-animation",
      { opacity: 0, y: 10 },
      { opacity: 1, y: 0, duration: 0.5, ease: "power2.out", delay: 0.1 }
    );
  }, { scope: containerRef, dependencies: [pathname, isMounted] });

  if (!isMounted) return <div className="h-screen w-full bg-[#f9fafb]" />;

  const sidebarWidth = isSidebarCollapsed ? 96 : 280;

  return (
    <div ref={containerRef} className="min-h-screen bg-[#f9fafb] font-sans overflow-x-hidden">
      {/* ── Fixed Sidebar ────────────────────────────────────────────── */}
      <aside 
        className="fixed left-0 top-0 h-screen z-50 transition-all duration-350 ease-in-out bg-[#f9fafb]"
        style={{ width: `${sidebarWidth}px` }}
      >
        <Sidebar isCollapsed={isSidebarCollapsed} />
      </aside>

      {/* ── Content Wrapper (Pushed by Sidebar) ────────────────────────── */}
      <div 
        className="min-h-screen flex flex-col transition-all duration-350 ease-in-out"
        style={{ paddingLeft: `${sidebarWidth}px` }}
      >
        {/* ── Fixed Navbar (Aligned with content) ──────────────────────── */}
        <header 
          className="fixed top-0 right-0 h-20 z-40 transition-all duration-350 ease-in-out"
          style={{ left: `${sidebarWidth}px` }}
        >
          <Navbar onToggleSidebar={() => setIsSidebarCollapsed(!isSidebarCollapsed)} />
        </header>

        {/* ── Main Content Area (Spaced for Navbar) ────────────────────── */}
        <main className="flex-1 p-4 md:p-8 pt-[104px] md:pt-[104px] overflow-x-hidden no-scrollbar">
          <div className="max-w-[1600px] mx-auto w-full reveal-animation">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
