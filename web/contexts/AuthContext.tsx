"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
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

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshUser = () => {
    void (async () => {
      if (!isAuthenticated()) {
        // Access token is missing or expired — try a silent refresh first
        const refreshed = await refreshAccessToken();
        if (!refreshed) {
          setUser(null);
          setLoading(false);
          return;
        }
      }
      const userData = getCurrentUserFromToken();
      setUser(userData ? { id: userData.sub || '', email: userData.email, full_name: userData.full_name, role: userData.role as string | undefined } : null);
      setLoading(false);
    })();
  };

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
  }, []);

  const login = (accessToken: string, refreshToken?: string, fullName?: string) => {
    localStorage.setItem('access_token', accessToken);
    if (refreshToken) {
      localStorage.setItem('refresh_token', refreshToken);
    }
    if (fullName) {
      localStorage.setItem('user_full_name', fullName);
    }
    refreshUser();
  };

  const logout = () => {
    setUser(null);
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
