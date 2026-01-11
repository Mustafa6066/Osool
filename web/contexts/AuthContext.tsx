"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { isAuthenticated, getCurrentUserFromToken, logout as apiLogout } from '@/lib/api';

interface User {
  id: string;
  email?: string;
  wallet_address?: string;
  full_name?: string;
  role?: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: (accessToken: string, refreshToken?: string) => void;
  logout: () => void;
  refreshUser: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshUser = () => {
    if (isAuthenticated()) {
      const userData = getCurrentUserFromToken();
      setUser(userData);
    } else {
      setUser(null);
    }
    setLoading(false);
  };

  useEffect(() => {
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

    refreshUser();
  }, []);

  const login = (accessToken: string, refreshToken?: string) => {
    localStorage.setItem('access_token', accessToken);
    if (refreshToken) {
      localStorage.setItem('refresh_token', refreshToken);
    }
    refreshUser();
  };

  const logout = () => {
    apiLogout();
    setUser(null);
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
