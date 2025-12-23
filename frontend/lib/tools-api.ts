/**
 * Tools API Client
 *
 * Functions for interacting with system tools endpoints.
 * System tools are developer-managed (Gmail, Analytics, Export).
 */

import { API_BASE_URL } from './constants';
import { getAccessToken } from './auth-api';

/**
 * System tool definition
 */
export interface SystemTool {
  id: string;
  name: string;
  description: string;
  icon: string;
  category: 'communication' | 'insights' | 'utilities';
  auth_type: 'none' | 'oauth' | 'api_key';
  is_enabled: boolean;
  is_beta: boolean;
  is_connected: boolean;
  config: Record<string, unknown> | null;
}

/**
 * Helper function to make API requests
 * @param requireAuth - If true, throws error if not authenticated. If false, sends token if available.
 */
async function toolsFetch<T>(
  endpoint: string,
  options: RequestInit = {},
  requireAuth: boolean = false
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  const token = getAccessToken();
  if (requireAuth && !token) {
    throw new Error('Not authenticated');
  }
  // Always send token if available (for user-specific status)
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      ...headers,
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `Request failed: ${response.status}`);
  }

  return response.json();
}

/**
 * Get all system tools
 *
 * Returns list of all system tools (Gmail, Analytics, Export)
 */
export async function getAllTools(): Promise<SystemTool[]> {
  return toolsFetch<SystemTool[]>('/api/tools');
}

/**
 * Get enabled (non-beta) tools only
 *
 * Returns list of tools that are enabled and not in beta
 */
export async function getEnabledTools(): Promise<SystemTool[]> {
  return toolsFetch<SystemTool[]>('/api/tools?enabled=true');
}

/**
 * Get tools by category
 *
 * @param category - Tool category (communication, insights, utilities)
 */
export async function getToolsByCategory(
  category: 'communication' | 'insights' | 'utilities'
): Promise<SystemTool[]> {
  return toolsFetch<SystemTool[]>(`/api/tools?category=${category}`);
}

/**
 * Get a specific tool by ID
 *
 * @param toolId - Tool identifier (e.g., 'gmail', 'analytics')
 */
export async function getToolById(toolId: string): Promise<SystemTool> {
  return toolsFetch<SystemTool>(`/api/tools/${toolId}`);
}

/**
 * Get icon component name for a tool
 * Maps backend icon identifiers to Lucide icon names
 */
export function getToolIconName(icon: string): string {
  const iconMap: Record<string, string> = {
    mail: 'Mail',
    chart: 'BarChart3',
    download: 'Download',
    settings: 'Settings',
    database: 'Database',
    cloud: 'Cloud',
  };
  return iconMap[icon] || 'Box';
}

/**
 * Get category display name
 */
export function getCategoryDisplayName(category: string): string {
  const categoryNames: Record<string, string> = {
    communication: 'Communication',
    insights: 'Insights & Analytics',
    utilities: 'Utilities',
  };
  return categoryNames[category] || category;
}

/**
 * Connect to a system tool
 *
 * @param toolId - Tool identifier (e.g., 'gmail', 'analytics')
 * @returns Updated tool with is_connected=true
 */
export async function connectTool(toolId: string): Promise<SystemTool> {
  return toolsFetch<SystemTool>(`/api/tools/${toolId}/connect`, {
    method: 'POST',
  }, true); // requires auth
}

/**
 * Disconnect from a system tool
 *
 * @param toolId - Tool identifier
 * @returns Updated tool with is_connected=false
 */
export async function disconnectTool(toolId: string): Promise<SystemTool> {
  return toolsFetch<SystemTool>(`/api/tools/${toolId}/disconnect`, {
    method: 'POST',
  }, true); // requires auth
}
