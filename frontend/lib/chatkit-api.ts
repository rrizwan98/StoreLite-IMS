/**
 * ChatKit API Client
 * Typed API calls to self-hosted FastAPI backend
 *
 * Features:
 * - Auto-refresh tokens on 401 responses
 * - Seamless session management for 30-day validity
 */

import { getAccessToken, getTokens, saveTokens, clearTokens } from './auth-api';
import { API_BASE_URL } from './constants';

export interface ChatKitSession {
  session_id: string;
  created_at: string;
}

export interface ChatKitMessage {
  session_id: string;
  message: string;
  user_id?: string | null;
  thread_id?: string | null;
}

export interface ChatKitResponse {
  session_id: string;
  message: string;
  type: 'text' | 'item_created' | 'bill_created' | 'item_list' | 'error';
  structured_data?: Record<string, any>;
  timestamp: string;
  error?: string;
}

const API_BASE = process.env.NEXT_PUBLIC_AGENT_API_URL || 'http://localhost:8000/agent';

// ============================================================================
// Auto-Refresh Helper for ChatKit
// ============================================================================

let isRefreshingChatKit = false;
let refreshPromiseChatKit: Promise<string | null> | null = null;

/**
 * Refresh token and return new access token
 */
async function refreshAndGetToken(): Promise<string | null> {
  if (isRefreshingChatKit && refreshPromiseChatKit) {
    return refreshPromiseChatKit;
  }

  isRefreshingChatKit = true;
  refreshPromiseChatKit = (async () => {
    const currentTokens = getTokens();
    if (!currentTokens?.refresh_token) {
      isRefreshingChatKit = false;
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
        isRefreshingChatKit = false;
        return null;
      }

      const tokens = await response.json();
      saveTokens(tokens);
      isRefreshingChatKit = false;
      return tokens.access_token;
    } catch {
      clearTokens();
      isRefreshingChatKit = false;
      return null;
    }
  })();

  return refreshPromiseChatKit;
}

/**
 * Fetch with auto-refresh on 401 for ChatKit endpoints
 */
async function chatKitFetch<T>(
  url: string,
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

  const response = await fetch(url, {
    ...options,
    headers,
  });

  // Auto-refresh on 401
  if (response.status === 401 && retryOnUnauthorized) {
    const newToken = await refreshAndGetToken();
    if (newToken) {
      // Retry with new token
      const retryHeaders: Record<string, string> = {
        'Content-Type': 'application/json',
        ...(options.headers as Record<string, string>),
        'Authorization': `Bearer ${newToken}`,
      };

      const retryResponse = await fetch(url, {
        ...options,
        headers: retryHeaders,
      });

      if (!retryResponse.ok) {
        throw new Error(`Request failed: ${retryResponse.statusText}`);
      }

      return retryResponse.json();
    } else {
      throw new Error('Session expired. Please log in again.');
    }
  }

  if (!response.ok) {
    throw new Error(`Request failed: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Create a new ChatKit session (with auto-refresh on 401)
 */
export async function createChatKitSession(userId?: string | null): Promise<ChatKitSession> {
  return chatKitFetch<ChatKitSession>(`${API_BASE}/session`, {
    method: 'POST',
    body: JSON.stringify({ user_id: userId || null }),
  });
}

/**
 * Send a message to the ChatKit agent (with auto-refresh on 401)
 */
export async function sendChatKitMessage(request: ChatKitMessage): Promise<ChatKitResponse> {
  return chatKitFetch<ChatKitResponse>(`${API_BASE}/chat`, {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

/**
 * Stream a message to the ChatKit agent (for real-time responses)
 * Note: Streaming has its own auth handling with auto-refresh
 */
export async function streamChatKitMessage(request: ChatKitMessage): Promise<ReadableStream> {
  const token = getAccessToken();

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  let response = await fetch(`${API_BASE}/chat/stream`, {
    method: 'POST',
    headers,
    body: JSON.stringify(request),
  });

  // Auto-refresh on 401 for streaming
  if (response.status === 401) {
    const newToken = await refreshAndGetToken();
    if (newToken) {
      response = await fetch(`${API_BASE}/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${newToken}`,
        },
        body: JSON.stringify(request),
      });
    } else {
      throw new Error('Session expired. Please log in again.');
    }
  }

  if (!response.ok) {
    throw new Error(`Failed to stream message: ${response.statusText}`);
  }

  return response.body!;
}
