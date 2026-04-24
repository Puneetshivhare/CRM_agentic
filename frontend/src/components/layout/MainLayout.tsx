"use client";

import React, { useEffect, useRef, useState } from "react";
import { usePathname } from "next/navigation";
import { gsap } from "gsap";
import { useGSAP } from "@gsap/react";
import Sidebar from "./Sidebar";
import Navbar from "./Navbar";

export default function MainLayout({ children }: { children: React.ReactNode }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const pathname = usePathname();
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  useGSAP(() => {
    if (!isMounted) return;

    gsap.fromTo(
      ".reveal-animation",
      { opacity: 0, y: 8 },
      { opacity: 1, y: 0, duration: 0.35, ease: "power2.out", delay: 0.03 },
    );
  }, { scope: containerRef, dependencies: [pathname, isMounted] });

  if (!isMounted) return <div className="h-screen w-full bg-[var(--color-page)]" />;

  return (
    <div
      ref={containerRef}
      className="flex min-h-screen bg-[var(--color-page)] font-sans selection:bg-[var(--color-accent-soft)] selection:text-[var(--color-accent)]"
    >
      <aside className="hidden w-72 flex-shrink-0 border-r border-[var(--color-border)] bg-white xl:block">
        <Sidebar />
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-30 flex-shrink-0 border-b border-[var(--color-border)] bg-white/95 backdrop-blur">
          <Navbar />
        </header>

        <main className="flex-1 overflow-x-hidden overflow-y-auto bg-[var(--color-page)]">
          <div className="mx-auto min-h-[calc(100vh-73px)] max-w-[1680px] px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
