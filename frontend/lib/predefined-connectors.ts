/**
 * Predefined Connectors Registry
 *
 * Contains configuration for pre-built OAuth connectors like Notion.
 * These connectors use browser-based OAuth flow instead of manual URL/token entry.
 */

export interface PredefinedConnector {
  id: string;
  name: string;
  description: string;
  logo: string;
  category: string;
  capabilities: string[];
  developer: string;
  website: string;
  privacyPolicy: string;
  authType: 'oauth' | 'api_key';
  oauthConfig?: {
    clientId: string;
    authorizationUrl: string;
    redirectUri: string;
    scopes?: string[];
  };
  apiKeyConfig?: {
    keyName: string;
    placeholder: string;
    helpUrl: string;
    helpText: string;
  };
  mcpServerUrl: string;
  isAvailable: boolean;
}

/**
 * Notion MCP OAuth Configuration
 *
 * Uses Notion's hosted MCP server which requires OAuth authentication.
 * The OAuth flow redirects to Notion's install-integration page.
 */
const NOTION_CONNECTOR: PredefinedConnector = {
  id: 'notion',
  name: 'Notion',
  description: 'Search and reference your Notion pages',
  logo: '/connectors/notion-logo.svg',
  category: 'Productivity',
  capabilities: ['Page Search', 'Content Sync', 'Database Access'],
  developer: 'Notion',
  website: 'https://www.notion.so',
  privacyPolicy: 'https://www.notion.so/privacy',
  authType: 'oauth',
  oauthConfig: {
    // Notion's public OAuth client for MCP
    clientId: process.env.NEXT_PUBLIC_NOTION_OAUTH_CLIENT_ID || '',
    authorizationUrl: 'https://www.notion.so/install-integration',
    redirectUri: typeof window !== 'undefined'
      ? `${window.location.origin}/connectors/callback/notion`
      : '',
    scopes: [],
  },
  mcpServerUrl: 'https://mcp.notion.com/mcp',
  isAvailable: true,
};

/**
 * Google Drive MCP OAuth Configuration
 *
 * Uses Google OAuth 2.0 for authentication.
 * Client ID is configured in backend .env file.
 * OAuth flow is initiated via backend endpoint.
 */
const GOOGLE_DRIVE_CONNECTOR: PredefinedConnector = {
  id: 'google_drive',
  name: 'Google Drive',
  description: 'Access your Google Drive files, Docs, Sheets & Slides',
  logo: '/connectors/google-drive-logo.svg',
  category: 'Productivity',
  capabilities: ['File Search', 'Google Docs', 'Google Sheets', 'Google Slides', 'File Management'],
  developer: 'Google',
  website: 'https://drive.google.com',
  privacyPolicy: 'https://policies.google.com/privacy',
  authType: 'oauth',
  oauthConfig: {
    // Client ID is loaded from environment variable
    clientId: process.env.NEXT_PUBLIC_GOOGLE_DRIVE_CLIENT_ID || '',
    authorizationUrl: 'https://accounts.google.com/o/oauth2/v2/auth',
    redirectUri: typeof window !== 'undefined'
      ? `${window.location.origin}/connectors/callback/google_drive`
      : '',
    scopes: [
      'openid',
      'email',
      'https://www.googleapis.com/auth/drive.readonly',
      'https://www.googleapis.com/auth/userinfo.email',
      'https://www.googleapis.com/auth/userinfo.profile',
    ],
  },
  mcpServerUrl: 'gdrive://mcp', // Google Drive MCP server URL
  isAvailable: true,
};

/**
 * Gmail MCP OAuth Configuration
 *
 * Uses Google OAuth 2.0 for authentication.
 * Provides email sending and inbox access capabilities.
 * OAuth flow is initiated via backend endpoint.
 */
const GMAIL_CONNECTOR: PredefinedConnector = {
  id: 'gmail',
  name: 'Gmail',
  description: 'Send emails and access your Gmail inbox',
  logo: '/connectors/gmail-logo.svg',
  category: 'Communication',
  capabilities: ['Send Email', 'Read Inbox', 'Search Emails', 'Email Management'],
  developer: 'Google',
  website: 'https://mail.google.com',
  privacyPolicy: 'https://policies.google.com/privacy',
  authType: 'oauth',
  oauthConfig: {
    // Client ID is loaded from environment variable (same as Google Drive)
    clientId: process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || '',
    authorizationUrl: 'https://accounts.google.com/o/oauth2/v2/auth',
    redirectUri: typeof window !== 'undefined'
      ? `${window.location.origin}/connectors/callback/gmail`
      : '',
    scopes: [
      'openid',
      'email',
      'https://www.googleapis.com/auth/gmail.send',
      'https://www.googleapis.com/auth/gmail.readonly',
      'https://www.googleapis.com/auth/userinfo.email',
      'https://www.googleapis.com/auth/userinfo.profile',
    ],
  },
  mcpServerUrl: 'gmail://mcp', // Gmail MCP server URL
  isAvailable: true,
};

/**
 * Retell AI Voice Agent Configuration
 *
 * Uses API key authentication (no OAuth).
 * User enters API key from Retell AI dashboard.
 * Enables AI-powered outbound phone calls.
 */
const RETELL_AI_CONNECTOR: PredefinedConnector = {
  id: 'retellai',
  name: 'Retell AI',
  description: 'AI Voice Agent for outbound phone calls',
  logo: '/connectors/retellai-logo.svg',
  category: 'Communication',
  capabilities: [
    'Outbound Phone Calls',
    'Voice Agent Management',
    'Phone Number Provisioning',
    'Call Analytics',
  ],
  developer: 'Retell AI',
  website: 'https://www.retellai.com',
  privacyPolicy: 'https://www.retellai.com/privacy',
  authType: 'api_key',
  apiKeyConfig: {
    keyName: 'Retell AI API Key',
    placeholder: 'key_xxxxxxxxxxxxxxxxxxxxxxxx',
    helpUrl: 'https://www.retellai.com/dashboard',
    helpText: 'Get your API key from the Retell AI dashboard under Settings > API Keys',
  },
  mcpServerUrl: 'retellai://mcp', // Backend MCP proxy for Retell AI
  isAvailable: true,
};

/**
 * All predefined connectors
 */
export const PREDEFINED_CONNECTORS: PredefinedConnector[] = [
  NOTION_CONNECTOR,
  GOOGLE_DRIVE_CONNECTOR,
  GMAIL_CONNECTOR,
  RETELL_AI_CONNECTOR,
];

/**
 * Get a predefined connector by ID
 */
export function getPredefinedConnector(id: string): PredefinedConnector | undefined {
  return PREDEFINED_CONNECTORS.find(c => c.id === id);
}

/**
 * Check if a connector ID is predefined
 */
export function isPredefinedConnector(id: string): boolean {
  return PREDEFINED_CONNECTORS.some(c => c.id === id);
}

/**
 * Permission points shown in OAuth confirmation modal
 */
export interface PermissionPoint {
  title: string;
  description: string;
  icon: 'shield' | 'control' | 'warning';
}

/**
 * Get permission points for OAuth confirmation
 */
export function getOAuthPermissionPoints(connectorId: string): PermissionPoint[] {
  return [
    {
      title: 'Permissions always respected',
      description: 'IMS Agent is strictly limited to permissions you\'ve explicitly set. Disable access anytime to revoke permissions.',
      icon: 'shield',
    },
    {
      title: 'You\'re in control',
      description: 'IMS Agent always respects your data preferences. Data from connected services may be used to provide you relevant and useful information.',
      icon: 'control',
    },
    {
      title: 'Connectors may introduce risk',
      description: 'Connectors are designed to respect your privacy, but external sites may attempt to access your data. Only connect to trusted services.',
      icon: 'warning',
    },
  ];
}
