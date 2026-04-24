"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";

function FullScreenState({ message }: { message: string }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-[var(--color-page)]">
      <div className="flex items-center gap-3 rounded-2xl border border-[var(--color-border)] bg-white px-5 py-4 shadow-[var(--shadow-card)]">
        <div className="h-5 w-5 animate-spin rounded-full border-2 border-[var(--color-border-strong)] border-t-[var(--color-accent)]" />
        <p className="text-sm font-medium text-[var(--color-text-muted)]">{message}</p>
      </div>
    </div>
  );
}

export function AuthGuard({
  children,
  requireAuth = true,
  fallbackPath,
}: {
  children: React.ReactNode;
  requireAuth?: boolean;
  fallbackPath?: string;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const { isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    if (isLoading) return;

    if (requireAuth && !isAuthenticated) {
      router.replace(fallbackPath ?? `/login?next=${encodeURIComponent(pathname || "/dashboard/prospects")}`);
    }

    if (!requireAuth && isAuthenticated) {
      router.replace(fallbackPath ?? "/dashboard/prospects");
    }
  }, [fallbackPath, isAuthenticated, isLoading, pathname, requireAuth, router]);

  if (isLoading) {
    return <FullScreenState message="Restoring your workspace..." />;
  }

  if (requireAuth && !isAuthenticated) {
    return <FullScreenState message="Redirecting to sign in..." />;
  }

  if (!requireAuth && isAuthenticated) {
    return <FullScreenState message="Opening your workspace..." />;
  }

  return <>{children}</>;
}
