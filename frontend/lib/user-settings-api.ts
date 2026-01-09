/**
 * User Settings API Client
 *
 * Currently supports file retention settings for ChatKit attachments/uploads.
 */
import { API_BASE_URL } from './constants';
import { getAccessToken } from './auth-api';

export type FileRetentionMode = 'keep_24h' | 'keep_48h' | 'delete_immediately';

export interface FileRetentionResponse {
  file_retention_mode: FileRetentionMode;
}

async function authFetch<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = getAccessToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${API_BASE_URL}${endpoint}`, { ...options, headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(err.detail || err.message || 'Request failed');
  }
  return res.json();
}

export async function getFileRetention(): Promise<FileRetentionResponse> {
  return authFetch<FileRetentionResponse>('/api/user-settings/file-retention');
}

export async function updateFileRetention(mode: FileRetentionMode): Promise<FileRetentionResponse> {
  return authFetch<FileRetentionResponse>('/api/user-settings/file-retention', {
    method: 'PUT',
    body: JSON.stringify({ file_retention_mode: mode }),
  });
}





