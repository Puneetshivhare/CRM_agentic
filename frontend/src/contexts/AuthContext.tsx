"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import api, { ApiError } from "@/lib/api";
import { clearStoredToken, getStoredToken, setStoredToken } from "@/lib/session";
import type { AuthResponse, AuthUser } from "@/lib/types";

interface AuthContextValue {
  user: AuthUser | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshSession: () => Promise<void>;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

function getErrorMessage(error: unknown) {
  if (error instanceof ApiError) return error.message;
  if (error instanceof Error) return error.message;
  return "Something went wrong. Please try again.";
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const logout = useCallback(() => {
    clearStoredToken();
    setToken(null);
    setUser(null);
    setError(null);
  }, []);

  const refreshSession = useCallback(async () => {
    const nextToken = getStoredToken();
    if (!nextToken) {
      setToken(null);
      setUser(null);
      setIsLoading(false);
      return;
    }

    try {
      setToken(nextToken);
      const response = await api.auth.me();
      setUser(response);
      setError(null);
    } catch (sessionError) {
      logout();
      setError(getErrorMessage(sessionError));
    } finally {
      setIsLoading(false);
    }
  }, [logout]);

  useEffect(() => {
    void refreshSession();
  }, [refreshSession]);

  const applyAuth = useCallback((response: AuthResponse) => {
    setStoredToken(response.token);
    setToken(response.token);
    setUser({
      user_id: response.user_id,
      email: response.email,
    });
    setError(null);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    try {
      setIsLoading(true);
      const response = await api.auth.login(email, password);
      applyAuth(response);
    } catch (loginError) {
      setError(getErrorMessage(loginError));
      throw loginError;
    } finally {
      setIsLoading(false);
    }
  }, [applyAuth]);

  const signup = useCallback(async (email: string, password: string) => {
    try {
      setIsLoading(true);
      const response = await api.auth.signup(email, password);
      applyAuth(response);
    } catch (signupError) {
      setError(getErrorMessage(signupError));
      throw signupError;
    } finally {
      setIsLoading(false);
    }
  }, [applyAuth]);

  const value = useMemo<AuthContextValue>(() => ({
    user,
    token,
    isAuthenticated: Boolean(user && token),
    isLoading,
    error,
    login,
    signup,
    logout,
    refreshSession,
    clearError: () => setError(null),
  }), [user, token, isLoading, error, login, signup, logout, refreshSession]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
