/**
 * Dashboard Connect Page
 *
 * For users with own_database - manage MCP connection
 */

'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import Script from 'next/script';
import { ROUTES, APP_METADATA, API_BASE_URL } from '@/lib/constants';
import { useAuth } from '@/lib/auth-context';
import { getAccessToken } from '@/lib/auth-api';

interface ConnectionResult {
  success: boolean;
  session_id?: string;
  message: string;
  database_info?: {
    version: string;
    tables: string[];
    table_count: number;
  };
  mcp_info?: {
    server: string;
    tools: string[];
    mode: string;
  };
}

interface MCPStatus {
  postgres_mcp_installed: boolean;
  postgres_mcp_path: string | null;
  active_sessions: number;
}

type ConnectionStep = 'connect' | 'setup' | 'chat';

export default function DashboardConnectPage() {
  const { user, connectionStatus, logout, updateMCPStatus, refreshConnectionStatus, disconnectDatabase, isLoading } = useAuth();
  const router = useRouter();

  const [step, setStep] = useState<ConnectionStep>('connect');
  const [sessionId, setSessionId] = useState<string>('');
  const [connecting, setConnecting] = useState(false);
  const [restoring, setRestoring] = useState(true);
  const [result, setResult] = useState<ConnectionResult | null>(null);
  const [error, setError] = useState<string>('');
  const [isChatkitLoaded, setIsChatkitLoaded] = useState(false);
  const [mcpStatus, setMcpStatus] = useState<MCPStatus | null>(null);
  const [checkingMcp, setCheckingMcp] = useState(true);
  const chatkitRef = useRef<HTMLElement | null>(null);
  const configuredRef = useRef(false);

  // New state for "Use Different Database" feature
  const [useDifferentDb, setUseDifferentDb] = useState(false);
  const [newDatabaseUri, setNewDatabaseUri] = useState<string>('');
  const [savingUri, setSavingUri] = useState(false);

  // Check if user should be here
  useEffect(() => {
    if (!isLoading && connectionStatus?.connection_type !== 'own_database') {
      router.push(ROUTES.DASHBOARD);
    }
  }, [connectionStatus, isLoading, router]);

  // Get database URI from connection status (stored during setup)
  const databaseUri = connectionStatus?.database_uri_set ? 'stored' : '';

  // Check for active session and restore on mount
  useEffect(() => {
    const checkAndRestoreSession = async () => {
      try {
        // First check MCP status
        const mcpResponse = await fetch(`${API_BASE_URL}/inventory-agent/mcp-status`, {
          headers: { 'Authorization': `Bearer ${getAccessToken()}` }
        });
        const mcpData: MCPStatus = await mcpResponse.json();
        setMcpStatus(mcpData);
        setCheckingMcp(false);

        if (!mcpData.postgres_mcp_installed) {
          setRestoring(false);
          return;
        }

        // Check for active session
        const activeResponse = await fetch(`${API_BASE_URL}/inventory-agent/active-session`, {
          headers: { 'Authorization': `Bearer ${getAccessToken()}` }
        });
        const activeData = await activeResponse.json();

        if (activeData.has_active_session && activeData.session) {
          // Try to restore
          const restoreResponse = await fetch(`${API_BASE_URL}/inventory-agent/restore`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${getAccessToken()}` }
          });
          const restoreData = await restoreResponse.json();

          if (restoreData.success) {
            setSessionId(restoreData.session_id);
            setResult({
              success: true,
              session_id: restoreData.session_id,
              message: restoreData.message,
              mcp_info: restoreData.mcp_info,
            });
            setStep('chat');
            await updateMCPStatus('connected', restoreData.session_id);
          }
        }
      } catch (err) {
        console.error('[Connect] Failed to check/restore session:', err);
      } finally {
        setRestoring(false);
      }
    };

    if (!isLoading && connectionStatus?.connection_type === 'own_database') {
      checkAndRestoreSession();
    } else {
      setRestoring(false);
    }
  }, [isLoading, connectionStatus, updateMCPStatus]);

  const connectDatabase = async (useNewUri?: boolean) => {
    setConnecting(true);
    setError('');
    setResult(null);

    try {
      // Build request body
      const requestBody: { user_id?: number; database_uri?: string } = {
        user_id: user?.id
      };

      // If using a different database URI, include it
      if (useNewUri && newDatabaseUri.trim()) {
        requestBody.database_uri = newDatabaseUri.trim();
      }

      const response = await fetch(`${API_BASE_URL}/inventory-agent/connect`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getAccessToken()}`
        },
        body: JSON.stringify(requestBody),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || data.message || 'Connection failed');
      }

      setResult(data);
      if (data.success && data.session_id) {
        setSessionId(data.session_id);
        setStep('setup');
        await updateMCPStatus('connecting', data.session_id);

        // Reset "use different db" state on successful connection
        setUseDifferentDb(false);
        setNewDatabaseUri('');

        // Refresh connection status to get updated database_uri_set
        await refreshConnectionStatus();
      }
    } catch (err) {
      setError(`Connection failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setConnecting(false);
    }
  };

  const setupTables = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/inventory-agent/setup-tables?session_id=${sessionId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getAccessToken()}`
        },
      });

      const data = await response.json();

      if (data.success) {
        setStep('chat');
        await updateMCPStatus('connected', sessionId);
      }
    } catch (err) {
      setError(`Setup failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  const skipSetup = async () => {
    setStep('chat');
    await updateMCPStatus('connected', sessionId);
  };

  const disconnect = async () => {
    try {
      await fetch(`${API_BASE_URL}/inventory-agent/disconnect/${sessionId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${getAccessToken()}` }
      });
    } catch (e) { }

    await updateMCPStatus('disconnected');
    setStep('connect');
    setResult(null);
    setSessionId('');
    setError('');
    configuredRef.current = false;
  };

  const handleDisconnectAndReset = async () => {
    await disconnect();
    await disconnectDatabase();
    router.push(ROUTES.DASHBOARD);
  };

  // Configure ChatKit
  const configureChatKit = useCallback(() => {
    if (!isChatkitLoaded || step !== 'chat' || !sessionId) return;
    if (configuredRef.current) return;

    const chatkit = chatkitRef.current as any;
    if (!chatkit || typeof chatkit.setOptions !== 'function') {
      setTimeout(() => configureChatKit(), 100);
      return;
    }

    configuredRef.current = true;

    chatkit.setOptions({
      api: {
        url: `${API_BASE_URL}/inventory-agent/chatkit`,
        domainKey: '',
        fetch: async (url: string, options: RequestInit) => {
          try {
            const body = options.body ? JSON.parse(options.body as string) : {};
            body.session_id = sessionId;
            body.user_id = user?.id;

            return await fetch(url, {
              ...options,
              body: JSON.stringify(body),
              headers: {
                ...options.headers,
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getAccessToken()}`,
                'x-session-id': sessionId,
              },
            });
          } catch (e) {
            console.error('[Connect] ChatKit fetch error:', e);
            throw e;
          }
        },
      },
      theme: 'light',
      header: {
        enabled: true,
        title: { enabled: true, text: 'Your Database Agent' },
      },
      startScreen: {
        greeting: 'Connected to your PostgreSQL database! Ask me anything.',
        prompts: [
          { label: 'Show Products', prompt: 'Show all products' },
          { label: 'Low Stock', prompt: 'Show low stock items' },
          { label: 'Add Product', prompt: 'Add new product' },
          { label: 'Create Bill', prompt: 'Create a bill' },
        ],
      },
      composer: { placeholder: 'Ask about products, stock, bills...' },
      disclaimer: { text: 'Connected to your own database via MCP.' },
    });
  }, [isChatkitLoaded, step, sessionId, user?.id]);

  useEffect(() => {
    if (step === 'chat' && isChatkitLoaded) {
      const timer = setTimeout(configureChatKit, 100);
      return () => clearTimeout(timer);
    }
  }, [step, isChatkitLoaded, configureChatKit]);

  const handleScriptLoad = () => {
    const checkElement = () => {
      if (customElements.get('openai-chatkit')) {
        setIsChatkitLoaded(true);
      } else {
        setTimeout(checkElement, 100);
      }
    };
    checkElement();
  };

  if (isLoading || restoring) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">{restoring ? 'Restoring your connection...' : 'Loading...'}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Load ChatKit */}
      <Script
        src="https://cdn.platform.openai.com/deployments/chatkit/chatkit.js"
        strategy="afterInteractive"
        onLoad={handleScriptLoad}
      />

      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-6">
            <Link href={ROUTES.DASHBOARD} className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
                <span className="text-white text-xl font-bold">S</span>
              </div>
              <span className="text-xl font-bold text-gray-900">{APP_METADATA.NAME}</span>
            </Link>
            <nav className="hidden md:flex space-x-4">
              <Link href={ROUTES.DB_CONNECT} className="text-blue-600 font-medium">Connection</Link>
              <Link href={ROUTES.ANALYTICS} className="text-gray-600 hover:text-gray-900">Analytics</Link>
            </nav>
          </div>
          <div className="flex items-center space-x-4">
            <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">Your Database</span>
            <span className="text-gray-600 text-sm">{user?.email}</span>
            <button onClick={logout} className="text-gray-600 hover:text-gray-900 text-sm">Logout</button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-2">Your PostgreSQL Database</h1>
          <p className="text-gray-600">Manage your database connection via MCP protocol.</p>
        </div>

        {/* Step indicator */}
        <div className="flex items-center mb-8">
          <div className={`flex items-center ${step === 'connect' ? 'text-blue-600' : 'text-green-600'}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center ${step === 'connect' ? 'bg-blue-100' : 'bg-green-100'}`}>
              {step === 'connect' ? '1' : '✓'}
            </div>
            <span className="ml-2 font-medium">Connect</span>
          </div>
          <div className={`flex-1 h-1 mx-4 ${step !== 'connect' ? 'bg-green-400' : 'bg-gray-200'}`} />
          <div className={`flex items-center ${step === 'setup' ? 'text-blue-600' : step === 'chat' ? 'text-green-600' : 'text-gray-400'}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center ${step === 'setup' ? 'bg-blue-100' : step === 'chat' ? 'bg-green-100' : 'bg-gray-100'}`}>
              {step === 'chat' ? '✓' : '2'}
            </div>
            <span className="ml-2 font-medium">Setup</span>
          </div>
          <div className={`flex-1 h-1 mx-4 ${step === 'chat' ? 'bg-green-400' : 'bg-gray-200'}`} />
          <div className={`flex items-center ${step === 'chat' ? 'text-blue-600' : 'text-gray-400'}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center ${step === 'chat' ? 'bg-blue-100' : 'bg-gray-100'}`}>3</div>
            <span className="ml-2 font-medium">Manage</span>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">{error}</div>
        )}

        {/* Step 1: Connect */}
        {step === 'connect' && (
          <div className="space-y-6">
            {checkingMcp ? (
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 flex items-center">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-gray-600 mr-3"></div>
                <span className="text-gray-600">Checking MCP server status...</span>
              </div>
            ) : mcpStatus?.postgres_mcp_installed ? (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex items-center">
                  <span className="text-2xl mr-3">✅</span>
                  <div>
                    <h3 className="font-semibold text-green-800">MCP Server Ready</h3>
                    <p className="text-green-700 text-sm">postgres-mcp is installed and ready.</p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex items-start">
                  <span className="text-2xl mr-3">⚠️</span>
                  <div>
                    <h3 className="font-semibold text-red-800 mb-1">postgres-mcp Not Installed</h3>
                    <p className="text-red-700 text-sm mb-3">Install it on the server:</p>
                    <code className="bg-red-100 px-3 py-2 rounded text-sm block font-mono text-red-800">
                      pipx install postgres-mcp
                    </code>
                  </div>
                </div>
              </div>
            )}

            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold mb-4">Connect to Your Database</h2>

              {/* Show stored database option OR input field based on state */}
              {databaseUri && !useDifferentDb ? (
                // User has stored database URI - show direct connect option
                <>
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
                    <div className="flex items-center">
                      <span className="text-xl mr-2">🔐</span>
                      <div>
                        <p className="text-green-800 font-medium">Database URI Configured</p>
                        <p className="text-green-600 text-sm">Your connection details are securely stored.</p>
                      </div>
                    </div>
                  </div>

                  <button
                    onClick={() => connectDatabase(false)}
                    disabled={connecting || !mcpStatus?.postgres_mcp_installed}
                    className="w-full bg-blue-600 text-white py-3 px-4 rounded-md hover:bg-blue-700 disabled:bg-blue-400 transition-colors font-medium mb-3"
                  >
                    {connecting ? 'Connecting via MCP...' : 'Connect to Database'}
                  </button>

                  <button
                    onClick={() => setUseDifferentDb(true)}
                    className="w-full border border-gray-300 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-50 transition-colors text-sm"
                  >
                    Use Different Database
                  </button>
                </>
              ) : (
                // User wants to use different database OR no stored URI - show input field
                <>
                  {useDifferentDb && (
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mb-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center">
                          <span className="text-lg mr-2">🔄</span>
                          <p className="text-yellow-800 text-sm">Enter a new database URI to connect</p>
                        </div>
                        <button
                          onClick={() => {
                            setUseDifferentDb(false);
                            setNewDatabaseUri('');
                            setError('');
                          }}
                          className="text-yellow-700 hover:text-yellow-900 text-sm underline"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  )}

                  <div className="mb-4">
                    <label htmlFor="database-uri" className="block text-sm font-medium text-gray-700 mb-2">
                      PostgreSQL Database URI
                    </label>
                    <input
                      type="password"
                      id="database-uri"
                      value={newDatabaseUri}
                      onChange={(e) => setNewDatabaseUri(e.target.value)}
                      placeholder="postgresql://user:password@host:port/database"
                      className="w-full px-4 py-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
                    />
                    <p className="text-gray-500 text-xs mt-1">
                      Your URI will be saved for future connections.
                    </p>
                  </div>

                  <button
                    onClick={() => connectDatabase(true)}
                    disabled={connecting || !mcpStatus?.postgres_mcp_installed || !newDatabaseUri.trim()}
                    className="w-full bg-blue-600 text-white py-3 px-4 rounded-md hover:bg-blue-700 disabled:bg-blue-400 transition-colors font-medium"
                  >
                    {connecting ? 'Connecting via MCP...' : 'Connect with New Database'}
                  </button>
                </>
              )}
            </div>

            <div className="text-center">
              <button
                onClick={handleDisconnectAndReset}
                className="text-red-600 hover:text-red-700 text-sm"
              >
                Switch to different service
              </button>
            </div>
          </div>
        )}

        {/* Step 2: Setup */}
        {step === 'setup' && result && (
          <div className="space-y-6">
            <div className="bg-green-50 border border-green-200 rounded-lg p-6">
              <div className="flex items-center mb-4">
                <span className="text-3xl mr-3">✅</span>
                <div>
                  <h2 className="text-xl font-semibold text-green-800">Connected via MCP!</h2>
                  <p className="text-green-600">{result.message}</p>
                </div>
              </div>

              {result.mcp_info && (
                <div className="bg-white rounded-lg p-4 mt-4">
                  <h3 className="font-semibold mb-2">MCP Server Information</h3>
                  <div className="text-sm space-y-1">
                    <div><span className="text-gray-500">Server:</span> {result.mcp_info.server}</div>
                    <div><span className="text-gray-500">Mode:</span> {result.mcp_info.mode}</div>
                  </div>
                </div>
              )}
            </div>

            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold mb-4">Setup Inventory Tables</h2>
              <p className="text-gray-600 mb-4">Create standard inventory tables or skip if they already exist.</p>
              <div className="flex gap-4">
                <button onClick={setupTables} className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors">
                  Create Tables
                </button>
                <button onClick={skipSetup} className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors">
                  Skip (tables exist)
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Step 3: Chat */}
        {step === 'chat' && (
          <div className="space-y-4">
            <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white px-6 py-4 rounded-lg shadow-lg flex justify-between items-center">
              <div>
                <h2 className="text-xl font-semibold">Your Database Agent</h2>
                <p className="text-blue-100 text-sm">Session: {sessionId} | Connected via MCP</p>
              </div>
              <div className="flex gap-2">
                <Link href={ROUTES.ANALYTICS} className="bg-white text-blue-600 px-4 py-2 rounded-md hover:bg-gray-100 transition-colors font-medium">
                  AI Analytics
                </Link>
                <button onClick={disconnect} className="bg-red-500 hover:bg-red-600 px-5 py-2.5 rounded-md transition-colors font-medium">
                  Disconnect
                </button>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-md overflow-hidden" style={{ height: '500px' }}>
              {isChatkitLoaded ? (
                <openai-chatkit
                  ref={chatkitRef as any}
                  id="connect-chatkit"
                  style={{ width: '100%', height: '100%', display: 'block' }}
                />
              ) : (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
                    <p className="text-gray-600">Loading ChatKit...</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </main>

      <style jsx global>{`
        openai-chatkit {
          --chatkit-primary-color: #2563eb;
          --chatkit-background: #ffffff;
          --chatkit-text-color: #1f2937;
          --chatkit-border-radius: 8px;
        }
      `}</style>
    </div>
  );
}

// Note: TypeScript declaration for openai-chatkit is in db-connect/page.tsx
