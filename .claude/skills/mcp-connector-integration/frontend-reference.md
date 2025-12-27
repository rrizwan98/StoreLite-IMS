# Frontend Reference for MCP Connector Integration

This document provides detailed frontend implementation patterns for MCP connector integrations.

## Directory Structure

```
frontend/
  lib/
    predefined-connectors.ts      # Connector configurations
    connectors-api.ts             # API client functions
  public/
    connectors/
      notion-logo.svg             # Connector logos
      [new]-logo.svg
  components/
    connectors/
      index.ts                    # Exports
      PredefinedConnectorsList.tsx  # Grid of available connectors
      OAuthConfirmModal.tsx       # Permission confirmation dialog
      ConnectorDetailView.tsx     # Post-connection success view
      ConnectorsList.tsx          # List of connected connectors
      ConnectorsModal.tsx         # Main modal container
      AppsToolsPanel.tsx          # "Manage Tools" panel
  app/
    connectors/
      callback/
        page.tsx                  # OAuth callback handler
```

## Predefined Connector Configuration

### Interface Definition

```typescript
// frontend/lib/predefined-connectors.ts

export interface PredefinedConnector {
  id: string;                    // Unique identifier (lowercase)
  name: string;                  // Display name
  description: string;           // Brief description
  logo: string;                  // Path to logo in /public
  category: string;              // Category for grouping
  capabilities: string[];        // List of capabilities
  developer: string;             // Developer/company name
  website: string;               // Official website URL
  privacyPolicy: string;         // Privacy policy URL
  authType: 'oauth';             // Authentication type
  oauthConfig: {
    clientId: string;            // OAuth client ID
    authorizationUrl: string;    // OAuth authorization endpoint
    redirectUri: string;         // OAuth redirect URI
    scopes?: string[];           // Required OAuth scopes
  };
  mcpServerUrl: string;          // MCP server endpoint
  isAvailable: boolean;          // Is connector available
}
```

### Adding a New Connector

```typescript
// frontend/lib/predefined-connectors.ts

const SLACK_CONNECTOR: PredefinedConnector = {
  id: 'slack',
  name: 'Slack',
  description: 'Send messages and manage channels',
  logo: '/connectors/slack-logo.svg',
  category: 'Communication',
  capabilities: ['Send Messages', 'Manage Channels', 'Search History'],
  developer: 'Slack Technologies',
  website: 'https://slack.com',
  privacyPolicy: 'https://slack.com/privacy-policy',
  authType: 'oauth',
  oauthConfig: {
    clientId: process.env.NEXT_PUBLIC_SLACK_OAUTH_CLIENT_ID || '',
    authorizationUrl: 'https://slack.com/oauth/v2/authorize',
    redirectUri: typeof window !== 'undefined'
      ? `${window.location.origin}/connectors/callback/slack`
      : '',
    scopes: ['chat:write', 'channels:read', 'channels:history'],
  },
  mcpServerUrl: 'https://mcp.slack.com/mcp',
  isAvailable: true,
};

// Add to array
export const PREDEFINED_CONNECTORS: PredefinedConnector[] = [
  NOTION_CONNECTOR,
  SLACK_CONNECTOR,  // Add here
];
```

## OAuth Flow

### Step 1: User Clicks Connector

```tsx
// PredefinedConnectorsList.tsx
<button onClick={() => onConnectorClick(connector)}>
  {connector.name}
</button>
```

### Step 2: Show Confirmation Modal

```tsx
// ConnectorsModal.tsx
{showOAuthConfirm && selectedConnector && (
  <OAuthConfirmModal
    isOpen={showOAuthConfirm}
    onClose={() => setShowOAuthConfirm(false)}
    onConfirm={handleOAuthConfirm}
    connector={selectedConnector}
  />
)}
```

### Step 3: Redirect to OAuth

```typescript
// OAuth redirect function
const handleOAuthConfirm = () => {
  const connector = selectedConnector;
  if (!connector) return;

  // Build OAuth URL
  const params = new URLSearchParams({
    client_id: connector.oauthConfig.clientId,
    redirect_uri: connector.oauthConfig.redirectUri,
    response_type: 'code',
  });

  if (connector.oauthConfig.scopes?.length) {
    params.set('scope', connector.oauthConfig.scopes.join(' '));
  }

  // Store state for callback
  sessionStorage.setItem('oauth_connector', connector.id);

  // Redirect to OAuth provider
  window.location.href = `${connector.oauthConfig.authorizationUrl}?${params}`;
};
```

### Step 4: Handle Callback

```tsx
// frontend/app/connectors/callback/page.tsx

'use client';

import { useEffect, useState } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';

export default function OAuthCallbackPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');

  useEffect(() => {
    const code = searchParams.get('code');
    const error = searchParams.get('error');
    const connectorId = sessionStorage.getItem('oauth_connector');

    if (error) {
      setStatus('error');
      return;
    }

    if (!code || !connectorId) {
      setStatus('error');
      return;
    }

    // Exchange code for tokens
    exchangeToken(code, connectorId);
  }, [searchParams]);

  const exchangeToken = async (code: string, connectorId: string) => {
    try {
      const response = await fetch('/api/connectors/oauth/callback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, connector_id: connectorId }),
      });

      if (!response.ok) throw new Error('Token exchange failed');

      setStatus('success');

      // Redirect to dashboard after delay
      setTimeout(() => {
        router.push('/dashboard?connected=' + connectorId);
      }, 2000);

    } catch (error) {
      console.error('OAuth error:', error);
      setStatus('error');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center">
      {status === 'loading' && <p>Connecting...</p>}
      {status === 'success' && <p>Connected successfully!</p>}
      {status === 'error' && <p>Connection failed. Please try again.</p>}
    </div>
  );
}
```

## UI Components

### OAuthConfirmModal

Shows permission confirmation before OAuth redirect:

```tsx
// Key elements:
// 1. App logos (IMS + Connector)
// 2. Permission points
// 3. "Continue to {Connector}" button
// 4. Privacy/developer info

<div className="flex items-center justify-center space-x-4">
  <div className="w-14 h-14 rounded-xl bg-blue-600 flex items-center justify-center">
    <span className="text-white font-bold">IMS</span>
  </div>
  <ArrowRight className="h-4 w-4 text-gray-400" />
  <Image src={connector.logo} alt={connector.name} width={40} height={40} />
</div>

<h2>Connect {connector.name}</h2>
<p>Developed by {connector.developer}</p>

{permissionPoints.map(point => (
  <div key={point.title}>
    <Icon type={point.icon} />
    <h4>{point.title}</h4>
    <p>{point.description}</p>
  </div>
))}

<button onClick={onConfirm}>
  Continue to {connector.name}
</button>
```

### ConnectorDetailView

Shows after successful connection:

```tsx
// Post-connection success state
<div className="text-center">
  <CheckCircle className="h-16 w-16 text-green-500 mx-auto" />
  <h2>{connector.name} Connected!</h2>
  <p>You can now use {connector.name} with IMS Agent</p>

  <div className="mt-6 space-y-3">
    <p className="text-sm text-gray-600">Available tools:</p>
    {connector.capabilities.map(cap => (
      <span key={cap} className="px-3 py-1 bg-gray-100 rounded-full text-sm">
        {cap}
      </span>
    ))}
  </div>

  <button onClick={onStartChat} className="mt-8 bg-blue-600 text-white">
    Start Chat
  </button>
</div>
```

### PredefinedConnectorsList

Grid of available connectors:

```tsx
{PREDEFINED_CONNECTORS.map(connector => {
  const isConnected = connectedIds.includes(connector.id);

  return (
    <button
      key={connector.id}
      onClick={() => onConnectorClick(connector)}
      disabled={!connector.isAvailable}
      className={`
        flex items-center p-4 rounded-xl border
        ${isConnected ? 'bg-green-50 border-green-200' : 'bg-white border-gray-200'}
      `}
    >
      <Image src={connector.logo} alt={connector.name} width={32} height={32} />
      <div className="ml-4">
        <h4>{connector.name}</h4>
        {isConnected && <span className="text-green-700">Connected</span>}
        <p className="text-gray-500">{connector.description}</p>
      </div>
      <ChevronRight className="ml-auto" />
    </button>
  );
})}
```

## API Client Functions

```typescript
// frontend/lib/connectors-api.ts

export async function listConnectors(): Promise<Connector[]> {
  const res = await fetch('/api/connectors', { credentials: 'include' });
  return res.json();
}

export async function createConnector(data: ConnectorCreateRequest): Promise<Connector> {
  const res = await fetch('/api/connectors', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function deleteConnector(id: number): Promise<void> {
  await fetch(`/api/connectors/${id}`, {
    method: 'DELETE',
    credentials: 'include',
  });
}

export async function checkConnectorHealth(id: number): Promise<HealthStatus> {
  const res = await fetch(`/api/connectors/${id}/health`, { credentials: 'include' });
  return res.json();
}

export async function toggleConnector(id: number, isActive: boolean): Promise<Connector> {
  const res = await fetch(`/api/connectors/${id}/toggle`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ is_active: isActive }),
  });
  return res.json();
}
```

## Environment Variables

```bash
# frontend/.env.local

# OAuth Client IDs (public - safe to expose)
NEXT_PUBLIC_NOTION_OAUTH_CLIENT_ID=your_notion_client_id
NEXT_PUBLIC_SLACK_OAUTH_CLIENT_ID=your_slack_client_id
NEXT_PUBLIC_AIRTABLE_OAUTH_CLIENT_ID=your_airtable_client_id
```

## Logo Requirements

- Format: SVG preferred (PNG acceptable)
- Size: At least 128x128px source
- Location: `frontend/public/connectors/`
- Naming: `{connector-id}-logo.svg`

## State Management

Track connected connectors:

```typescript
// Using React state or Zustand store
const [connectedIds, setConnectedIds] = useState<string[]>([]);

// Load on mount
useEffect(() => {
  const loadConnectors = async () => {
    const connectors = await listConnectors();
    const ids = connectors
      .filter(c => c.is_verified && c.is_active)
      .map(c => detectConnectorType(c.server_url));
    setConnectedIds(ids);
  };
  loadConnectors();
}, []);

// Helper to detect connector type from URL
const detectConnectorType = (url: string): string => {
  if (url.includes('notion')) return 'notion';
  if (url.includes('slack')) return 'slack';
  return 'unknown';
};
```

## Error Handling

```tsx
// OAuth callback error handling
const [error, setError] = useState<string | null>(null);

try {
  await exchangeToken(code, connectorId);
} catch (e) {
  if (e.message.includes('invalid_grant')) {
    setError('Authorization expired. Please try again.');
  } else if (e.message.includes('access_denied')) {
    setError('Access was denied. Please authorize the connection.');
  } else {
    setError('An unexpected error occurred. Please try again.');
  }
}

// Display error
{error && (
  <div className="bg-red-50 border border-red-200 rounded-lg p-4">
    <p className="text-red-700">{error}</p>
    <button onClick={retry}>Try Again</button>
  </div>
)}
```

## Accessibility

```tsx
// Ensure proper ARIA labels
<button
  aria-label={`Connect to ${connector.name}`}
  role="button"
>
  Connect {connector.name}
</button>

// Loading states
<button disabled={isLoading} aria-busy={isLoading}>
  {isLoading ? 'Connecting...' : 'Connect'}
</button>

// Modal focus trap
useEffect(() => {
  if (isOpen) {
    // Focus first interactive element
    modalRef.current?.querySelector('button')?.focus();
  }
}, [isOpen]);
```
