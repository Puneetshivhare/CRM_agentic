"use client";

import React, { useState } from 'react';
import { Zap, Mail, Lock, ArrowRight, AlertCircle } from 'lucide-react';

export default function LoginPage() {
  const [loading, setLoading] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isSignup, setIsSignup] = useState(false);

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const endpoint = isSignup ? '/auth/signup' : '/auth/login';
    const url = `http://localhost:8005/api${endpoint}`;

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        let errorMessage = 'Authentication failed';
        if (typeof errorData.detail === 'string') {
          errorMessage = errorData.detail;
        } else if (Array.isArray(errorData.detail)) {
          errorMessage = errorData.detail.map((err: any) => err.msg).join(', ');
        }
        throw new Error(errorMessage);
      }

      const data = await response.json();
      localStorage.setItem('crm_token', data.token);
      window.location.href = '/dashboard';
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Request failed');
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6 relative overflow-hidden bg-[#020202]">
      {/* Background Ambience */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-accent-cyan/5 rounded-full blur-[150px] -z-10" />
      <div className="absolute top-[20%] right-[10%] w-[300px] h-[300px] bg-accent-magenta/5 rounded-full blur-[100px] -z-10" />

      <div className="w-full max-w-md space-y-8 reveal-animation">
        {/* Logo Section */}
        <div className="text-center space-y-4">
          <div className="inline-flex w-16 h-16 rounded-2xl bg-gradient-to-br from-accent-cyan to-accent-magenta p-[1px] shadow-[0_0_30px_rgba(0,242,255,0.2)]">
            <div className="w-full h-full bg-background rounded-[15px] flex items-center justify-center">
              <Zap className="w-8 h-8 text-accent-cyan" fill="currentColor" />
            </div>
          </div>
          <div>
            <h1 className="text-4xl font-bold font-display tracking-tight">
              {isSignup ? 'Join' : 'Welcome Back'} <span className="text-accent-cyan">{isSignup ? 'SalesAI Pro' : ''}</span>
            </h1>
            <p className="text-foreground/40 mt-2 font-medium">
              {isSignup ? 'Create your account to get started with AI sales intelligence.' : 'Log in to manage your AI sales intelligence.'}
            </p>
          </div>
        </div>

        {/* Login Form */}
        <div className="glass-effect rounded-[32px] p-8 spatial-depth-2">
          {error && (
            <div className="mb-6 p-4 rounded-xl bg-accent-red/10 border border-accent-red/20 flex items-center gap-3">
              <AlertCircle className="w-5 h-5 text-accent-red flex-shrink-0" />
              <span className="text-sm text-accent-red">{error}</span>
            </div>
          )}
          <form className="space-y-6" onSubmit={handleAuth}>
            <div className="space-y-2">
              <label className="text-xs font-bold text-foreground/40 uppercase tracking-widest ml-1">Email Address</label>
              <div className="relative group">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-foreground/20 group-focus-within:text-accent-cyan transition-colors" />
                <input 
                  type="email" 
                  required
                  placeholder="name@company.com"
                  className="w-full bg-white/5 border border-white/5 rounded-2xl py-4 pl-12 pr-4 text-sm outline-none focus:bg-white/10 focus:border-white/10 transition-all font-medium"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between items-center ml-1">
                <label className="text-xs font-bold text-foreground/40 uppercase tracking-widest">Password</label>
                {!isSignup && <button type="button" className="text-[10px] font-bold text-accent-cyan/60 hover:text-accent-cyan transition-colors">Forgot Password?</button>}
              </div>
              <div className="relative group">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-foreground/20 group-focus-within:text-accent-cyan transition-colors" />
                <input
                  type="password"
                  required
                  minLength={isSignup ? 8 : undefined}
                  placeholder={isSignup ? "Minimum 8 characters" : "••••••••"}
                  className="w-full bg-white/5 border border-white/5 rounded-2xl py-4 pl-12 pr-4 text-sm outline-none focus:bg-white/10 focus:border-white/10 transition-all font-medium"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-accent-cyan text-background py-4 rounded-2xl font-bold flex items-center justify-center gap-2 hover:opacity-90 active:scale-[0.98] transition-all shadow-[0_4px_20px_rgba(0,242,255,0.3)] disabled:opacity-50"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-background/30 border-t-background rounded-full animate-spin" />
              ) : (
                <>
                  {isSignup ? 'Create Account' : 'Sign In'} <ArrowRight className="w-5 h-5" />
                </>
              )}
            </button>
          </form>

          <div className="mt-8 pt-6 border-t border-white/5 text-center">
            <p className="text-sm text-foreground/40 font-medium">
              {isSignup ? (
                <>
                  Already have an account? <button
                    type="button"
                    onClick={() => { setIsSignup(false); setError(''); }}
                    className="text-accent-cyan font-bold hover:underline"
                  >
                    Sign In
                  </button>
                </>
              ) : (
                <>
                  Don't have an account? <button
                    type="button"
                    onClick={() => { setIsSignup(true); setError(''); }}
                    className="text-accent-cyan font-bold hover:underline"
                  >
                    Create Account
                  </button>
                </>
              )}
            </p>
          </div>
        </div>

        {/* Footer Info */}
        <p className="text-center text-[10px] font-bold text-white/5 uppercase tracking-[0.3em]">
          Secured by SalesAI Intelligence Network
        </p>
      </div>
    </div>
  );
}
