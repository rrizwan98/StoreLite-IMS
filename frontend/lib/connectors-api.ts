/**
 * Connectors API Client
 *
 * Functions for interacting with user MCP connector endpoints.
 * User connectors are user-managed custom MCP server connections.
 */

import { API_BASE_URL } from './constants';
import { getAccessToken } from './auth-api';

/**
 * Authentication type for connectors
 */
export type AuthType = 'none' | 'oauth' | 'api_key';

/**
 * Discovered tool from MCP server
 */
export interface DiscoveredTool {
  name: string;
  description?: string;
  inputSchema?: Record<string, unknown>;
}

/**
 * User MCP connector
 */
export interface Connector {
  id: number;
  name: string;
  description?: string;
  server_url: string;
  auth_type: AuthType;
  is_active: boolean;
  is_verified: boolean;
  discovered_tools: DiscoveredTool[];
  tool_count: number;
  last_verified_at?: string;
  created_at: string;
  updated_at?: string;
}

/**
 * Request to create a new connector
 */
export interface ConnectorCreateRequest {
  name: string;
  description?: string;
  server_url: string;
  auth_type: AuthType;
  auth_config?: Record<string, unknown>;
}

/**
 * Request to update a connector
 */
export interface ConnectorUpdateRequest {
  name?: string;
  description?: string;
  server_url?: string;
  auth_type?: AuthType;
  auth_config?: Record<string, unknown>;
  is_active?: boolean;
}

/**
 * Connection test result
 */
export interface ConnectionTestResult {
  success: boolean;
  error_code?: string;
  error_message?: string;
  tools?: DiscoveredTool[];
}

/**
 * Helper function to make authenticated API requests
 */
async function connectorsFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getAccessToken();

  if (!token) {
    throw new Error('Not authenticated');
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `Request failed: ${response.status}`);
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

/**
 * Get all connectors for the current user
 *
 * @param activeOnly - If true, only return active connectors
 */
export async function getConnectors(activeOnly?: boolean): Promise<Connector[]> {
  const params = activeOnly ? '?active=true' : '';
  return connectorsFetch<Connector[]>(`/api/connectors${params}`);
}

/**
 * Get a specific connector by ID
 *
 * @param connectorId - Connector ID
 */
export async function getConnectorById(connectorId: number): Promise<Connector> {
  return connectorsFetch<Connector>(`/api/connectors/${connectorId}`);
}

/**
 * Create a new connector
 *
 * @param request - Connector creation request
 */
export async function createConnector(request: ConnectorCreateRequest): Promise<Connector> {
  return connectorsFetch<Connector>('/api/connectors', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

/**
 * Update an existing connector
 *
 * @param connectorId - Connector ID
 * @param request - Update request
 */
export async function updateConnector(
  connectorId: number,
  request: ConnectorUpdateRequest
): Promise<Connector> {
  return connectorsFetch<Connector>(`/api/connectors/${connectorId}`, {
    method: 'PUT',
    body: JSON.stringify(request),
  });
}

/**
 * Delete a connector
 *
 * @param connectorId - Connector ID
 */
export async function deleteConnector(connectorId: number): Promise<void> {
  await connectorsFetch<void>(`/api/connectors/${connectorId}`, {
    method: 'DELETE',
  });
}

/**
 * Test connection to an MCP server
 *
 * @param serverUrl - MCP server URL to test
 * @param authType - Authentication type
 * @param authConfig - Authentication configuration
 */
export async function testConnection(
  serverUrl: string,
  authType: AuthType = 'none',
  authConfig?: Record<string, unknown>
): Promise<ConnectionTestResult> {
  return connectorsFetch<ConnectionTestResult>('/api/connectors/test', {
    method: 'POST',
    body: JSON.stringify({
      server_url: serverUrl,
      auth_type: authType,
      auth_config: authConfig,
    }),
  });
}

/**
 * Toggle connector active status
 *
 * @param connectorId - Connector ID
 * @param isActive - New active status
 */
export async function toggleConnector(
  connectorId: number,
  isActive: boolean
): Promise<Connector> {
  return connectorsFetch<Connector>(`/api/connectors/${connectorId}/toggle`, {
    method: 'POST',
    body: JSON.stringify({ is_active: isActive }),
  });
}

/**
 * Verify result from connector verification
 */
export interface VerifyResult {
  success: boolean;
  message: string;
  error_type?: string;
  connector?: Connector;
}

/**
 * Health check result for connector
 */
export interface HealthCheckResult {
  is_healthy: boolean;
  connector_id: number;
  connector_name: string;
  tool_count?: number;
  error_code?: string;
  error_message?: string;
  message: string;
}

/**
 * Verify or re-verify a connector
 *
 * Connects to the MCP server and discovers tools.
 *
 * @param connectorId - Connector ID to verify
 */
export async function verifyConnector(connectorId: number): Promise<VerifyResult> {
  return connectorsFetch<VerifyResult>(`/api/connectors/${connectorId}/verify`, {
    method: 'POST',
  });
}

/**
 * Refresh connector's discovered tools (alias for verify)
 *
 * @param connectorId - Connector ID
 */
export async function refreshConnectorTools(connectorId: number): Promise<Connector> {
  const result = await verifyConnector(connectorId);
  if (result.success && result.connector) {
    return result.connector;
  }
  throw new Error(result.message || 'Failed to refresh connector');
}

/**
 * Perform real-time health check on a connector
 *
 * Tests actual connection to the MCP server without modifying database.
 * Use this to check if OAuth tokens are still valid.
 *
 * @param connectorId - Connector ID to check
 */
export async function checkConnectorHealth(connectorId: number): Promise<HealthCheckResult> {
  return connectorsFetch<HealthCheckResult>(`/api/connectors/${connectorId}/health`);
}

/**
 * Get namespaced tool name for a connector tool
 * Format: "ConnectorName: tool_name"
 */
export function getNamespacedToolName(connectorName: string, toolName: string): string {
  return `${connectorName}: ${toolName}`;
}

/**
 * Parse namespaced tool name to get connector and tool name
 */
export function parseNamespacedToolName(
  namespacedName: string
): { connectorName: string; toolName: string } | null {
  const match = namespacedName.match(/^(.+?):\s*(.+)$/);
  if (!match) return null;
  return {
    connectorName: match[1].trim(),
    toolName: match[2].trim(),
  };
}


// ============================================================================
// OAuth Connector Functions
// ============================================================================

/**
 * OAuth configuration status
 */
export interface OAuthConfigStatus {
  configured: boolean;
  connector_name?: string;
  error?: string;
}

/**
 * Check if OAuth is configured for a connector
 * This is a public endpoint (no auth required)
 *
 * @param connectorId - Predefined connector ID (e.g., 'notion')
 */
export async function checkOAuthConfig(connectorId: string): Promise<OAuthConfigStatus> {
  const response = await fetch(`${API_BASE_URL}/api/oauth/config/${connectorId}`);
  return response.json();
}

// ============================================================================
// Notion MCP OAuth (Zero-Config - No Developer Credentials Needed!)
// ============================================================================

/**
 * Response from Notion MCP connect
 */
export interface NotionConnectResponse {
  authorization_url: string;
  state: string;
  method: 'dcr' | 'fallback';
}

/**
 * Start Notion MCP OAuth flow
 * Uses Dynamic Client Registration - no developer credentials needed!
 */
export async function connectNotion(): Promise<NotionConnectResponse> {
  return connectorsFetch<NotionConnectResponse>('/api/notion-mcp/connect', {
    method: 'POST',
  });
}

/**
 * Exchange OAuth code for token (called by callback page)
 */
export async function exchangeNotionCode(
  code: string,
  state: string
): Promise<{ success: boolean; connector_id?: number; connector_name?: string; message?: string }> {
  return connectorsFetch(`/api/notion-mcp/callback?code=${encodeURIComponent(code)}&state=${encodeURIComponent(state)}`, {
    method: 'POST',
  });
}

/**
 * Check Notion connection status
 */
export async function getNotionStatus(): Promise<{
  connected: boolean;
  connector_id?: number;
  connector_name?: string;
}> {
  return connectorsFetch('/api/notion-mcp/status');
}

/**
 * Disconnect Notion
 */
export async function disconnectNotion(): Promise<{ success: boolean; message: string }> {
  return connectorsFetch('/api/notion-mcp/disconnect', {
    method: 'DELETE',
  });
}

/**
 * Response from OAuth initiation
 */
export interface InitiateOAuthResponse {
  authorization_url: string;
  state: string;
}

/**
 * OAuth connection status
 */
export interface OAuthStatus {
  connected: boolean;
  connector_id?: number;
  connector_name?: string;
  verified?: boolean;
  last_verified_at?: string;
}

/**
 * Initiate OAuth flow for a predefined connector
 *
 * @param connectorId - Predefined connector ID (e.g., 'notion')
 * @param redirectUri - OAuth callback URI
 */
export async function initiateOAuth(
  connectorId: string,
  redirectUri: string
): Promise<InitiateOAuthResponse> {
  return connectorsFetch<InitiateOAuthResponse>('/api/oauth/initiate', {
    method: 'POST',
    body: JSON.stringify({
      connector_id: connectorId,
      redirect_uri: redirectUri,
    }),
  });
}

/**
 * Check OAuth connection status for a connector
 *
 * @param connectorId - Predefined connector ID (e.g., 'notion')
 */
export async function getOAuthStatus(connectorId: string): Promise<OAuthStatus> {
  return connectorsFetch<OAuthStatus>(`/api/oauth/status/${connectorId}`);
}

/**
 * Disconnect an OAuth connector
 *
 * @param connectorId - Predefined connector ID (e.g., 'notion')
 */
export async function disconnectOAuth(connectorId: string): Promise<{ success: boolean; message: string }> {
  return connectorsFetch<{ success: boolean; message: string }>(
    `/api/oauth/disconnect/${connectorId}`,
    { method: 'DELETE' }
  );
}
