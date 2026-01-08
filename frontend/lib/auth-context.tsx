'use client';

/**
 * Authentication Context Provider
 *
 * Provides auth state and functions throughout the app.
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import {
  User,
  ConnectionStatus,
  getCurrentUser,
  getConnectionStatus,
  login as apiLogin,
  signup as apiSignup,
  logout as apiLogout,
  chooseConnection as apiChooseConnection,
  disconnectDatabase as apiDisconnect,
  updateMCPStatus as apiUpdateMCPStatus,
  isAuthenticated as checkAuth,
  LoginData,
  SignupData,
  ConnectionChoice,
} from './auth-api';

// ============================================================================
// Types
// ============================================================================

interface AuthContextType {
  // State
  user: User | null;
  connectionStatus: ConnectionStatus | null;
  isLoading: boolean;
  isAuthenticated: boolean;

  // Auth actions
  login: (data: LoginData) => Promise<void>;
  signup: (data: SignupData) => Promise<void>;
  logout: () => Promise<void>;

  // Connection actions
  chooseConnection: (data: ConnectionChoice) => Promise<void>;
  disconnectDatabase: () => Promise<void>;
  updateMCPStatus: (status: string, sessionId?: string) => Promise<void>;
  refreshConnectionStatus: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

// ============================================================================
// Context
// ============================================================================

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Check authentication on mount
  useEffect(() => {
    const initAuth = async () => {
      if (checkAuth()) {
        try {
          const [userInfo, connStatus] = await Promise.all([
            getCurrentUser(),
            getConnectionStatus().catch(() => null),
          ]);
          setUser(userInfo);
          setConnectionStatus(connStatus);
        } catch (e) {
          console.error('[Auth] Init failed:', e);
        }
      }
      setIsLoading(false);
    };

    initAuth();
  }, []);

  const refreshUser = useCallback(async () => {
    if (checkAuth()) {
      try {
        const userInfo = await getCurrentUser();
        setUser(userInfo);
      } catch (e) {
        console.error('[Auth] Refresh user failed:', e);
      }
    }
  }, []);

  const refreshConnectionStatus = useCallback(async () => {
    if (checkAuth()) {
      try {
        const status = await getConnectionStatus();
        setConnectionStatus(status);
      } catch (e) {
        console.error('[Auth] Refresh connection status failed:', e);
      }
    }
  }, []);

  const login = useCallback(async (data: LoginData) => {
    await apiLogin(data);
    const [userInfo, connStatus] = await Promise.all([
      getCurrentUser(),
      getConnectionStatus().catch(() => null),
    ]);
    setUser(userInfo);
    setConnectionStatus(connStatus);
  }, []);

  const signup = useCallback(async (data: SignupData) => {
    await apiSignup(data);
    const userInfo = await getCurrentUser();
    setUser(userInfo);
    setConnectionStatus(null); // New user has no connection
  }, []);

  const logout = useCallback(async () => {
    await apiLogout();
    setUser(null);
    setConnectionStatus(null);
  }, []);

  const chooseConnection = useCallback(async (data: ConnectionChoice) => {
    await apiChooseConnection(data);
    await refreshConnectionStatus();
    await refreshUser();
  }, [refreshConnectionStatus, refreshUser]);

  const disconnectDatabase = useCallback(async () => {
    await apiDisconnect();
    setConnectionStatus(null);
    await refreshUser();
  }, [refreshUser]);

  const updateMCPStatus = useCallback(async (status: string, sessionId?: string) => {
    await apiUpdateMCPStatus(status, sessionId);
    await refreshConnectionStatus();
    await refreshUser();
  }, [refreshConnectionStatus, refreshUser]);

  const value: AuthContextType = {
    user,
    connectionStatus,
    isLoading,
    isAuthenticated: !!user,

    login,
    signup,
    logout,

    chooseConnection,
    disconnectDatabase,
    updateMCPStatus,
    refreshConnectionStatus,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// ============================================================================
// Hook
// ============================================================================

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

// ============================================================================
// Protected Route Component
// ============================================================================

export function RequireAuth({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    // Redirect to login
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
    return null;
  }

  return <>{children}</>;
}
