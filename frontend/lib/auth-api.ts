/**
 * Authentication API Client
 *
 * Handles all auth-related API calls to the backend.
 */

import { API_BASE_URL } from './constants';

// ============================================================================
// Types
// ============================================================================

export interface User {
  id: number;
  email: string;
  full_name: string | null;
  is_active: boolean;
  created_at: string;
  last_login: string | null;
  has_connection: boolean;
  connection_type: 'own_database' | 'our_database' | null;
  mcp_status: 'connected' | 'disconnected' | 'connecting' | 'error' | null;
  database_connected: boolean;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface ConnectionStatus {
  has_connection: boolean;
  needs_setup: boolean;
  connection_type: 'own_database' | 'our_database' | 'schema_query_only' | null;
  connection_mode?: 'full_ims' | 'schema_query' | null;
  mcp_status: string | null;
  mcp_session_id: string | null;
  last_connected_at: string | null;
  database_uri_set: boolean;
  schema_status?: 'ready' | 'pending' | 'not_connected' | null;
  tables_count?: number;
}

export interface SignupData {
  email: string;
  password: string;
  full_name?: string;
}

export interface LoginData {
  email: string;
  password: string;
}

export interface ConnectionChoice {
  connection_type: 'own_database' | 'our_database' | 'schema_query_only';
  database_uri?: string;
}

// ============================================================================
// Token Storage
// ============================================================================

const TOKEN_KEY = 'ims_auth_tokens';

export function saveTokens(tokens: AuthTokens): void {
  if (typeof window !== 'undefined') {
    localStorage.setItem(TOKEN_KEY, JSON.stringify(tokens));
  }
}

export function getTokens(): AuthTokens | null {
  if (typeof window === 'undefined') return null;
  const stored = localStorage.getItem(TOKEN_KEY);
  if (!stored) return null;
  try {
    return JSON.parse(stored);
  } catch {
    return null;
  }
}

export function clearTokens(): void {
  if (typeof window !== 'undefined') {
    localStorage.removeItem(TOKEN_KEY);
  }
}

export function getAccessToken(): string | null {
  const tokens = getTokens();
  return tokens?.access_token || null;
}

// ============================================================================
// API Helper with Auto-Refresh on 401
// ============================================================================

// Flag to prevent multiple simultaneous refresh attempts
let isRefreshing = false;
let refreshPromise: Promise<AuthTokens | null> | null = null;

/**
 * Perform token refresh (singleton pattern to prevent race conditions)
 */
async function performTokenRefresh(): Promise<AuthTokens | null> {
  if (isRefreshing && refreshPromise) {
    return refreshPromise;
  }

  isRefreshing = true;
  refreshPromise = (async () => {
    const currentTokens = getTokens();
    if (!currentTokens?.refresh_token) {
      isRefreshing = false;
      return null;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: currentTokens.refresh_token }),
      });

      if (!response.ok) {
        clearTokens();
        isRefreshing = false;
        return null;
      }

      const tokens = await response.json();
      saveTokens(tokens);
      isRefreshing = false;
      return tokens;
    } catch {
      clearTokens();
      isRefreshing = false;
      return null;
    }
  })();

  return refreshPromise;
}

/**
 * API fetch helper with automatic token refresh on 401
 * - If token is expired (401), automatically refreshes and retries the request
 * - Prevents multiple simultaneous refresh attempts
 */
async function authFetch<T>(
  endpoint: string,
  options: RequestInit = {},
  retryOnUnauthorized: boolean = true
): Promise<T> {
  const token = getAccessToken();

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  // Auto-refresh on 401 (Unauthorized) - token might be expired
  if (response.status === 401 && retryOnUnauthorized) {
    const newTokens = await performTokenRefresh();
    if (newTokens) {
      // Retry the original request with new token
      const retryHeaders: Record<string, string> = {
        'Content-Type': 'application/json',
        ...(options.headers as Record<string, string>),
        'Authorization': `Bearer ${newTokens.access_token}`,
      };

      const retryResponse = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers: retryHeaders,
      });

      if (!retryResponse.ok) {
        const error = await retryResponse.json().catch(() => ({ detail: 'Request failed' }));
        throw new Error(error.detail || error.message || 'Request failed');
      }

      return retryResponse.json();
    } else {
      // Refresh failed, throw auth error
      throw new Error('Session expired. Please log in again.');
    }
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(error.detail || error.message || 'Request failed');
  }

  return response.json();
}

// ============================================================================
// Auth API Functions
// ============================================================================

/**
 * Register a new user
 */
export async function signup(data: SignupData): Promise<AuthTokens> {
  const tokens = await authFetch<AuthTokens>('/auth/signup', {
    method: 'POST',
    body: JSON.stringify(data),
  });
  saveTokens(tokens);
  return tokens;
}

/**
 * Login user
 */
export async function login(data: LoginData): Promise<AuthTokens> {
  const tokens = await authFetch<AuthTokens>('/auth/login', {
    method: 'POST',
    body: JSON.stringify(data),
  });
  saveTokens(tokens);
  return tokens;
}

/**
 * Logout user
 */
export async function logout(): Promise<void> {
  try {
    await authFetch('/auth/logout', { method: 'POST' });
  } catch (e) {
    // Ignore errors, still clear tokens
  }
  clearTokens();
}

/**
 * Refresh access token (uses singleton pattern to prevent race conditions)
 */
export async function refreshToken(): Promise<AuthTokens | null> {
  return performTokenRefresh();
}

/**
 * Get current user info
 */
export async function getCurrentUser(): Promise<User | null> {
  const token = getAccessToken();
  if (!token) return null;

  try {
    return await authFetch<User>('/auth/me');
  } catch {
    // Token might be expired, try refresh
    const refreshed = await refreshToken();
    if (refreshed) {
      return await authFetch<User>('/auth/me');
    }
    return null;
  }
}

/**
 * Get user's connection status
 */
export async function getConnectionStatus(): Promise<ConnectionStatus> {
  return authFetch<ConnectionStatus>('/auth/connection');
}

/**
 * Choose connection type (first-time setup)
 */
export async function chooseConnection(data: ConnectionChoice): Promise<{
  success: boolean;
  message: string;
  connection_type: string;
  connection_mode?: string;
  needs_mcp_connect: boolean;
  needs_schema_discovery?: boolean;
  tables_found?: number;
  connected?: boolean;
}> {
  return authFetch('/auth/connection/choose', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * Update MCP connection status
 */
export async function updateMCPStatus(
  mcp_status: string,
  mcp_session_id?: string
): Promise<{ success: boolean }> {
  const params = new URLSearchParams({ mcp_status });
  if (mcp_session_id) params.append('mcp_session_id', mcp_session_id);

  return authFetch(`/auth/connection/update-mcp-status?${params}`, {
    method: 'POST',
  });
}

/**
 * Disconnect database and reset to service selection
 */
export async function disconnectDatabase(): Promise<{ success: boolean; message: string }> {
  return authFetch('/auth/connection/disconnect', {
    method: 'DELETE',
  });
}

/**
 * Check if user is authenticated
 */
export function isAuthenticated(): boolean {
  return !!getAccessToken();
}
