"use client";

import { AuthGuard } from "@/components/auth/AuthGuard";

export default function Home() {
  return (
    <AuthGuard requireAuth={false} fallbackPath="/dashboard/prospects">
      <div className="flex min-h-screen items-center justify-center bg-[var(--color-page)]" />
    </AuthGuard>
  );
}
