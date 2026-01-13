/**
 * Developer Tools API Client
 *
 * Functions for interacting with Developer Portal endpoints.
 * Allows organizations to create and manage published agents
 * that external users can access via API keys.
 */

import { API_BASE_URL } from './constants';
import { getAccessToken } from './auth-api';

// =============================================================================
// Types
// =============================================================================

/**
 * Table summary for selection UI
 */
export interface TableSummary {
  name: string;
  column_count: number;
  column_preview: string;
}

/**
 * Published agent configuration
 */
export interface PublishedAgent {
  id: string;
  name: string;
  description: string | null;
  api_key_prefix: string;
  allowed_tables: string[];
  access_mode: 'read_only' | 'read_write';
  rate_limit_per_minute: number;
  allowed_domains: string[];
  is_active: boolean;
  total_queries: number;
  last_used_at: string | null;
  created_at: string;
  updated_at: string;
  expires_at: string | null;
}

/**
 * Response when creating a new agent (includes full API key)
 */
export interface AgentCreatedResponse extends PublishedAgent {
  api_key: string;
  endpoint: string;
  embed_code: string;
}

/**
 * Request to create a new agent
 */
export interface CreateAgentRequest {
  name: string;
  description?: string;
  allowed_tables: string[];
  access_mode?: 'read_only' | 'read_write';
  rate_limit_per_minute?: number;
  allowed_domains?: string[];
  custom_instructions?: string;
}

/**
 * Request to update an existing agent
 */
export interface UpdateAgentRequest {
  name?: string;
  description?: string;
  allowed_tables?: string[];
  access_mode?: 'read_only' | 'read_write';
  rate_limit_per_minute?: number;
  allowed_domains?: string[];
  custom_instructions?: string;
  is_active?: boolean;
}

/**
 * Response for listing agents
 */
export interface AgentListResponse {
  agents: PublishedAgent[];
  total_count: number;
  max_allowed: number;
}

/**
 * Response for API key regeneration
 */
export interface RegenerateKeyResponse {
  api_key: string;
  api_key_prefix: string;
  message: string;
}

/**
 * Daily usage breakdown entry
 */
export interface DailyUsage {
  date: string;
  queries: number;
  successful: number;
  failed: number;
  avg_response_ms: number;
}

/**
 * Usage statistics response
 */
export interface UsageStatsResponse {
  agent_id: string;
  agent_name: string;
  period_days: number;
  total_queries: number;
  successful_queries: number;
  failed_queries: number;
  success_rate: number;
  total_tokens: number;
  avg_response_time_ms: number;
  daily_breakdown: DailyUsage[];
}

/**
 * Embed code response
 */
export interface EmbedCodeResponse {
  agent_id: string;
  agent_name: string;
  embed_code: string;
  endpoint: string;
  instructions: string;
}

// =============================================================================
// API Helper
// =============================================================================

/**
 * Helper function to make authenticated API requests
 */
async function developerFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getAccessToken();
  if (!token) {
    throw new Error('Not authenticated');
  }

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`,
  };

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      ...headers,
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    const message = typeof error.detail === 'object'
      ? error.detail.message || JSON.stringify(error.detail)
      : error.detail || `Request failed: ${response.status}`;
    throw new Error(message);
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

// =============================================================================
// API Functions
// =============================================================================

/**
 * Get available tables from user's database schema
 *
 * @returns List of tables with column info
 */
export async function getAvailableTables(): Promise<TableSummary[]> {
  return developerFetch<TableSummary[]>('/api/developer/tables');
}

/**
 * Create a new published agent
 *
 * @param request - Agent configuration
 * @returns Created agent with API key (shown only once!)
 */
export async function createPublishedAgent(
  request: CreateAgentRequest
): Promise<AgentCreatedResponse> {
  return developerFetch<AgentCreatedResponse>('/api/developer/agents', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

/**
 * Get all published agents for current user
 *
 * @returns List of agents with total count and max allowed
 */
export async function listPublishedAgents(): Promise<AgentListResponse> {
  return developerFetch<AgentListResponse>('/api/developer/agents');
}

/**
 * Get details of a specific published agent
 *
 * @param agentId - Agent UUID
 * @returns Agent details
 */
export async function getPublishedAgent(agentId: string): Promise<PublishedAgent> {
  return developerFetch<PublishedAgent>(`/api/developer/agents/${agentId}`);
}

/**
 * Update a published agent's configuration
 *
 * @param agentId - Agent UUID
 * @param request - Fields to update
 * @returns Updated agent
 */
export async function updatePublishedAgent(
  agentId: string,
  request: UpdateAgentRequest
): Promise<PublishedAgent> {
  return developerFetch<PublishedAgent>(`/api/developer/agents/${agentId}`, {
    method: 'PUT',
    body: JSON.stringify(request),
  });
}

/**
 * Delete a published agent
 *
 * @param agentId - Agent UUID
 */
export async function deletePublishedAgent(agentId: string): Promise<void> {
  return developerFetch<void>(`/api/developer/agents/${agentId}`, {
    method: 'DELETE',
  });
}

/**
 * Regenerate API key for an agent
 *
 * WARNING: This immediately revokes the old key!
 *
 * @param agentId - Agent UUID
 * @returns New API key (shown only once!)
 */
export async function regenerateApiKey(agentId: string): Promise<RegenerateKeyResponse> {
  return developerFetch<RegenerateKeyResponse>(
    `/api/developer/agents/${agentId}/regenerate-key`,
    { method: 'POST' }
  );
}

/**
 * Get usage statistics for an agent
 *
 * @param agentId - Agent UUID
 * @param days - Number of days to include (1-90, default: 30)
 * @returns Usage statistics and daily breakdown
 */
export async function getUsageStats(
  agentId: string,
  days: number = 30
): Promise<UsageStatsResponse> {
  return developerFetch<UsageStatsResponse>(
    `/api/developer/agents/${agentId}/usage?days=${days}`
  );
}

/**
 * Get embed code for an agent
 *
 * @param agentId - Agent UUID
 * @returns Embed code snippet and instructions
 */
export async function getEmbedCode(agentId: string): Promise<EmbedCodeResponse> {
  return developerFetch<EmbedCodeResponse>(
    `/api/developer/agents/${agentId}/embed-code`
  );
}

// =============================================================================
// Utility Functions
// =============================================================================

/**
 * Format date for display
 */
export function formatDate(isoString: string | null): string {
  if (!isoString) return 'Never';
  const date = new Date(isoString);
  return date.toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

/**
 * Format datetime for display
 */
export function formatDateTime(isoString: string | null): string {
  if (!isoString) return 'Never';
  const date = new Date(isoString);
  return date.toLocaleString(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  });
}

/**
 * Get status badge info
 */
export function getStatusBadge(isActive: boolean): {
  label: string;
  color: string;
  bgColor: string;
} {
  return isActive
    ? { label: 'Active', color: 'text-green-700 dark:text-green-400', bgColor: 'bg-green-100 dark:bg-green-900/30' }
    : { label: 'Inactive', color: 'text-gray-700 dark:text-gray-400', bgColor: 'bg-gray-100 dark:bg-gray-800' };
}

/**
 * Get access mode display info
 */
export function getAccessModeInfo(mode: 'read_only' | 'read_write'): {
  label: string;
  color: string;
  bgColor: string;
} {
  return mode === 'read_only'
    ? { label: 'Read Only', color: 'text-blue-700 dark:text-blue-400', bgColor: 'bg-blue-100 dark:bg-blue-900/30' }
    : { label: 'Read/Write', color: 'text-orange-700 dark:text-orange-400', bgColor: 'bg-orange-100 dark:bg-orange-900/30' };
}

/**
 * Format number with commas
 */
export function formatNumber(num: number): string {
  return num.toLocaleString();
}

/**
 * Truncate API key for display
 */
export function truncateApiKey(prefix: string): string {
  return prefix.length > 15 ? prefix.substring(0, 15) + '...' : prefix;
}
