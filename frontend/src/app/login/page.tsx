"use client";

import { useMemo, useState } from "react";
import { ArrowRight, Lock, Mail, ShieldCheck } from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import { AuthGuard } from "@/components/auth/AuthGuard";
import { FeedbackBanner } from "@/components/ui/FeedbackBanner";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useAuth } from "@/contexts/AuthContext";
import { ApiError } from "@/lib/api";

function LoginContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login, signup, clearError, error, isLoading } = useAuth();
  const [isRegisterMode, setIsRegisterMode] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    email: "",
    password: "",
    confirmPassword: "",
  });

  const nextPath = useMemo(() => searchParams.get("next") || "/dashboard/prospects", [searchParams]);

  const submitLabel = isRegisterMode ? "Create account" : "Sign in";

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    clearError();
    setSuccessMessage(null);

    if (isRegisterMode && formData.password !== formData.confirmPassword) {
      setSuccessMessage(null);
      return;
    }

    try {
      if (isRegisterMode) {
        await signup(formData.email, formData.password);
        setSuccessMessage("Account created. Your workspace is ready.");
      } else {
        await login(formData.email, formData.password);
      }

      router.replace(nextPath);
    } catch (submitError) {
      if (!(submitError instanceof ApiError)) {
        setSuccessMessage("We hit an unexpected error. Please try again.");
      }
    }
  };

  return (
    <div className="grid min-h-screen bg-[var(--color-page)] lg:grid-cols-[1.15fr_0.85fr]">
      <section className="hidden border-r border-[var(--color-border)] bg-white lg:flex lg:flex-col lg:justify-between lg:px-14 lg:py-12">
        <div className="space-y-6">
          <div className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-[var(--color-accent)] shadow-sm">
            <ShieldCheck className="h-6 w-6 text-white" />
          </div>
          <div className="space-y-4">
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[var(--color-text-subtle)]">Enterprise workspace</p>
            <h1 className="max-w-xl text-5xl font-semibold tracking-[-0.04em] text-[var(--color-text)]">
              Standardized frontend for operator-first CRM workflows.
            </h1>
            <p className="max-w-xl text-lg leading-8 text-[var(--color-text-muted)]">
              Sign in to manage prospects, companies, and enrichment activity from one Clay-inspired workspace built for dense, reliable daily use.
            </p>
          </div>
        </div>

        <div className="grid gap-4">
          {[
            "Centralized auth and guarded navigation",
            "Shared enterprise-grade tables for prospects and companies",
            "Consistent empty, loading, and mutation feedback states",
          ].map((item) => (
            <div key={item} className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface-subtle)] px-5 py-4 text-sm text-[var(--color-text-muted)]">
              {item}
            </div>
          ))}
        </div>
      </section>

      <section className="flex items-center justify-center px-4 py-10 sm:px-6 lg:px-10">
        <div className="w-full max-w-md rounded-[32px] border border-[var(--color-border)] bg-white p-8 shadow-[var(--shadow-elevated)] sm:p-10">
          <div className="space-y-3">
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[var(--color-text-subtle)]">
              {isRegisterMode ? "Create workspace access" : "Welcome back"}
            </p>
            <h2 className="text-3xl font-semibold tracking-[-0.03em] text-[var(--color-text)]">
              {isRegisterMode ? "Create your account" : "Sign in to continue"}
            </h2>
            <p className="text-sm text-[var(--color-text-muted)]">
              {isRegisterMode
                ? "Use your work email to create a disposable or permanent login for this environment."
                : "Use the account credentials for this CRM environment."}
            </p>
          </div>

          <div className="mt-8 grid grid-cols-2 rounded-2xl bg-[var(--color-surface-subtle)] p-1">
            <button
              type="button"
              onClick={() => {
                clearError();
                setSuccessMessage(null);
                setIsRegisterMode(false);
              }}
              className={`rounded-2xl px-4 py-2.5 text-sm font-semibold transition ${
                !isRegisterMode ? "bg-white text-[var(--color-text)] shadow-sm" : "text-[var(--color-text-muted)]"
              }`}
            >
              Sign in
            </button>
            <button
              type="button"
              onClick={() => {
                clearError();
                setSuccessMessage(null);
                setIsRegisterMode(true);
              }}
              className={`rounded-2xl px-4 py-2.5 text-sm font-semibold transition ${
                isRegisterMode ? "bg-white text-[var(--color-text)] shadow-sm" : "text-[var(--color-text-muted)]"
              }`}
            >
              Register
            </button>
          </div>

          <form className="mt-8 space-y-5" onSubmit={handleSubmit}>
            <label className="grid gap-2">
              <span className="text-xs font-semibold uppercase tracking-[0.12em] text-[var(--color-text-subtle)]">Email</span>
              <div className="relative">
                <Mail className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--color-text-subtle)]" />
                <Input
                  type="email"
                  value={formData.email}
                  onChange={(event) => setFormData((current) => ({ ...current, email: event.target.value }))}
                  placeholder="name@company.com"
                  autoComplete="email"
                  className="pl-10"
                  required
                />
              </div>
            </label>

            <label className="grid gap-2">
              <span className="text-xs font-semibold uppercase tracking-[0.12em] text-[var(--color-text-subtle)]">Password</span>
              <div className="relative">
                <Lock className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--color-text-subtle)]" />
                <Input
                  type="password"
                  value={formData.password}
                  onChange={(event) => setFormData((current) => ({ ...current, password: event.target.value }))}
                  placeholder="Minimum 8 characters"
                  autoComplete={isRegisterMode ? "new-password" : "current-password"}
                  className="pl-10"
                  required
                  minLength={8}
                />
              </div>
            </label>

            {isRegisterMode ? (
              <label className="grid gap-2">
                <span className="text-xs font-semibold uppercase tracking-[0.12em] text-[var(--color-text-subtle)]">Confirm password</span>
                <Input
                  type="password"
                  value={formData.confirmPassword}
                  onChange={(event) => setFormData((current) => ({ ...current, confirmPassword: event.target.value }))}
                  placeholder="Repeat your password"
                  autoComplete="new-password"
                  required
                />
                {formData.confirmPassword && formData.confirmPassword !== formData.password ? (
                  <span className="text-sm text-[var(--color-danger)]">Passwords do not match yet.</span>
                ) : null}
              </label>
            ) : null}

            {error ? <FeedbackBanner tone="error" message={error} /> : null}
            {successMessage ? <FeedbackBanner tone="success" message={successMessage} /> : null}

            <Button type="submit" className="w-full" disabled={isLoading || (isRegisterMode && formData.password !== formData.confirmPassword)}>
              {isLoading ? (
                <>
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                  <span>{isRegisterMode ? "Creating account..." : "Signing in..."}</span>
                </>
              ) : (
                <>
                  <span>{submitLabel}</span>
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </Button>
          </form>

          <p className="mt-6 text-sm text-[var(--color-text-muted)]">
            {isRegisterMode
              ? "Registration uses the existing backend auth contract: email + password only."
              : "Session state is restored automatically on refresh and protected routes are guarded centrally."}
          </p>
        </div>
      </section>
    </div>
  );
}

export default function LoginPage() {
  return (
    <AuthGuard requireAuth={false} fallbackPath="/dashboard/prospects">
      <LoginContent />
    </AuthGuard>
  );
}
