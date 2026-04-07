"use client";

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { isAuthenticated, getCurrentUserFromToken, refreshAccessToken, logout as apiLogout } from '@/lib/api';

interface User {
  id: string;
  email?: string;
  full_name?: string;
  role?: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: (accessToken: string, refreshToken?: string, fullName?: string) => void;
  logout: () => void;
  refreshUser: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const REFRESH_AHEAD_MS = 2 * 60 * 1000; // refresh 2 minutes before expiry

function getTokenExpiryMs(token: string): number | null {
  try {
    const payload = token.split('.')[1];
    if (!payload) return null;
    const normalized = payload.replace(/-/g, '+').replace(/_/g, '/');
    const decoded = JSON.parse(atob(normalized)) as { exp?: number };
    if (!decoded.exp || typeof decoded.exp !== 'number') return null;
    return decoded.exp * 1000;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshUser = useCallback(() => {
    void (async () => {
      const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
      const hasRefreshToken = typeof window !== 'undefined' ? !!localStorage.getItem('refresh_token') : false;

      if (!isAuthenticated()) {
        // Access token appears expired/missing — try silent refresh first.
        const refreshed = hasRefreshToken ? await refreshAccessToken() : false;
        if (!refreshed) {
          // Keep user if we can still decode identity from existing token.
          // Avoid abrupt signout on transient refresh/network failures.
          const fallbackUser = token ? getCurrentUserFromToken() : null;
          setUser(prev => {
            if (fallbackUser) {
              return {
                id: fallbackUser.sub || '',
                email: fallbackUser.email,
                full_name: fallbackUser.full_name,
                role: fallbackUser.role as string | undefined,
              };
            }
            return prev;
          });
          setLoading(false);
          return;
        }
      }

      const userData = getCurrentUserFromToken();
      setUser(userData ? { id: userData.sub || '', email: userData.email, full_name: userData.full_name, role: userData.role as string | undefined } : null);
      setLoading(false);
    })();
  }, []);

  useEffect(() => {
    try {
      // Backward compatibility migration
      // Phase 2: Migrate old token names to new standardized names
      const oldToken = localStorage.getItem('osool_jwt');
      const oldUserId = localStorage.getItem('osool_user_id');

      if (oldToken && !localStorage.getItem('access_token')) {
        localStorage.setItem('access_token', oldToken);
        localStorage.removeItem('osool_jwt');
      }

      if (oldUserId && !localStorage.getItem('user_id')) {
        localStorage.setItem('user_id', oldUserId);
        localStorage.removeItem('osool_user_id');
      }
    } catch {
      // localStorage unavailable (e.g. Safari private browsing)
    }

    const timer = setTimeout(() => {
      refreshUser();
    }, 0);

    return () => clearTimeout(timer);
  }, [refreshUser]);

  useEffect(() => {
    if (typeof window === 'undefined') return;

    const maybeRefreshSession = async () => {
      const token = localStorage.getItem('access_token');
      if (!token) return;

      const expMs = getTokenExpiryMs(token);
      if (!expMs) return;

      const msRemaining = expMs - Date.now();
      if (msRemaining <= REFRESH_AHEAD_MS) {
        const refreshed = await refreshAccessToken();
        if (refreshed) {
          refreshUser();
        }
      }
    };

    const intervalId = window.setInterval(() => {
      void maybeRefreshSession();
    }, 60_000);

    const onVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        void maybeRefreshSession();
      }
    };

    document.addEventListener('visibilitychange', onVisibilityChange);
    void maybeRefreshSession();

    return () => {
      window.clearInterval(intervalId);
      document.removeEventListener('visibilitychange', onVisibilityChange);
    };
  }, [refreshUser]);

  useEffect(() => {
    if (typeof window === 'undefined') return;

    const onStorage = (event: StorageEvent) => {
      if (event.key === 'access_token' || event.key === 'refresh_token' || event.key === null) {
        refreshUser();
      }
    };

    window.addEventListener('storage', onStorage);
    return () => window.removeEventListener('storage', onStorage);
  }, [refreshUser]);

  const login = (accessToken: string, refreshToken?: string, fullName?: string) => {
    localStorage.setItem('access_token', accessToken);
    if (refreshToken) {
      localStorage.setItem('refresh_token', refreshToken);
    }
    if (fullName) {
      localStorage.setItem('user_full_name', fullName);
    }
    // Set non-httpOnly cookie so middleware can detect auth state
    document.cookie = 'osool_auth_active=1; path=/; max-age=' + (30 * 24 * 60 * 60) + '; samesite=lax';
    refreshUser();
  };

  const logout = () => {
    setUser(null);
    // Clear the auth indicator cookie
    document.cookie = 'osool_auth_active=; path=/; max-age=0';
    // Also clear httpOnly cookies via server route
    fetch('/api/auth/logout', { method: 'POST' }).catch(() => {});
    apiLogout();
  };

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, loading, login, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
