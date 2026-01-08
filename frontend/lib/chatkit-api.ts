/**
 * ChatKit API Client
 * Typed API calls to self-hosted FastAPI backend
 */

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

/**
 * Create a new ChatKit session
 */
export async function createChatKitSession(userId?: string | null): Promise<ChatKitSession> {
  const response = await fetch(`${API_BASE}/session`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId || null }),
  });

  if (!response.ok) {
    throw new Error(`Failed to create session: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Send a message to the ChatKit agent
 */
export async function sendChatKitMessage(request: ChatKitMessage): Promise<ChatKitResponse> {
  const response = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`Failed to send message: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Stream a message to the ChatKit agent (for real-time responses)
 */
export async function streamChatKitMessage(request: ChatKitMessage): Promise<ReadableStream> {
  const response = await fetch(`${API_BASE}/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`Failed to stream message: ${response.statusText}`);
  }

  return response.body!;
}
