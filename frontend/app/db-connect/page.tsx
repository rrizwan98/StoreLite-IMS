/**
 * Database Connection Page with ChatKit UI
 *
 * Allows users to connect their own PostgreSQL database via DATABASE_URI
 * After successful connection, shows ChatKit UI for inventory management
 */

'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import Script from 'next/script';
import { API_BASE_URL } from '@/lib/constants';

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
  install_instructions: string | null;
  active_sessions: number;
}

interface ActiveSession {
  session_id: string;
  user_database_uri: string;
  mcp_tools: string[];
  connected_at: string;
  is_active: boolean;
}

type ConnectionStep = 'connect' | 'setup' | 'chat';

export default function DBConnectPage() {
  const [step, setStep] = useState<ConnectionStep>('connect');
  const [sessionId, setSessionId] = useState<string>('');
  const [databaseUri, setDatabaseUri] = useState<string>('');
  const [connecting, setConnecting] = useState(false);
  const [setting, setSetting] = useState(false);
  const [restoring, setRestoring] = useState(true); // Start with restoring state
  const [result, setResult] = useState<ConnectionResult | null>(null);
  const [error, setError] = useState<string>('');
  const [isChatkitLoaded, setIsChatkitLoaded] = useState(false);
  const [mcpStatus, setMcpStatus] = useState<MCPStatus | null>(null);
  const [checkingMcp, setCheckingMcp] = useState(true);
  const [activeSession, setActiveSession] = useState<ActiveSession | null>(null);
  const chatkitRef = useRef<HTMLElement | null>(null);
  const configuredRef = useRef(false);

  // Check for active session and restore on mount
  useEffect(() => {
    const checkAndRestoreSession = async () => {
      try {
        // First check MCP status
        const mcpResponse = await fetch(`${API_BASE_URL}/inventory-agent/mcp-status`);
        const mcpData: MCPStatus = await mcpResponse.json();
        setMcpStatus(mcpData);
        setCheckingMcp(false);

        if (!mcpData.postgres_mcp_installed) {
          setRestoring(false);
          return;
        }

        // Check for active session in database
        console.log('[DB Connect] Checking for active session...');
        const activeResponse = await fetch(`${API_BASE_URL}/inventory-agent/active-session`);
        const activeData = await activeResponse.json();

        if (activeData.has_active_session && activeData.session) {
          console.log('[DB Connect] Found active session:', activeData.session.session_id);
          setActiveSession(activeData.session);

          // Try to restore the session (reconnect MCP if needed)
          console.log('[DB Connect] Restoring session...');
          const restoreResponse = await fetch(`${API_BASE_URL}/inventory-agent/restore`, {
            method: 'POST',
          });
          const restoreData = await restoreResponse.json();

          if (restoreData.success) {
            console.log('[DB Connect] Session restored successfully!');
            setSessionId(restoreData.session_id);
            setResult({
              success: true,
              session_id: restoreData.session_id,
              message: restoreData.message,
              mcp_info: restoreData.mcp_info,
            });
            setStep('chat'); // Go directly to chat
          } else {
            console.log('[DB Connect] Session restore failed:', restoreData.message);
            setActiveSession(null);
          }
        } else {
          console.log('[DB Connect] No active session found');
        }
      } catch (err) {
        console.error('[DB Connect] Failed to check/restore session:', err);
        setMcpStatus({ postgres_mcp_installed: false, postgres_mcp_path: null, install_instructions: 'pipx install postgres-mcp', active_sessions: 0 });
        setCheckingMcp(false);
      } finally {
        setRestoring(false);
      }
    };

    checkAndRestoreSession();
  }, []);

  const connectDatabase = async () => {
    setConnecting(true);
    setError('');
    setResult(null);

    try {
      const response = await fetch(`${API_BASE_URL}/inventory-agent/connect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ database_uri: databaseUri }),
      });

      const data: ConnectionResult = await response.json();

      if (!response.ok) {
        throw new Error(data.message || 'Connection failed');
      }

      setResult(data);
      if (data.success && data.session_id) {
        setSessionId(data.session_id);
        setStep('setup');
      }
    } catch (err) {
      setError(`Connection failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setConnecting(false);
    }
  };

  const setupTables = async () => {
    setSetting(true);
    setError('');

    try {
      const response = await fetch(`${API_BASE_URL}/inventory-agent/setup-tables?session_id=${sessionId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Setup failed');
      }

      if (data.success) {
        setStep('chat');
      }
    } catch (err) {
      setError(`Setup failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setSetting(false);
    }
  };

  const skipSetup = () => {
    setStep('chat');
  };

  const disconnect = async () => {
    try {
      await fetch(`${API_BASE_URL}/inventory-agent/disconnect/${sessionId}`, { method: 'DELETE' });
    } catch (e) {
      // Ignore disconnect errors
    }
    setStep('connect');
    setResult(null);
    setSessionId('');
    setError('');
    configuredRef.current = false;
  };

  // Configure ChatKit when loaded and in chat step
  const configureChatKit = useCallback(() => {
    if (!isChatkitLoaded || step !== 'chat' || !sessionId) return;
    if (configuredRef.current) return;

    const chatkit = chatkitRef.current as any;
    if (!chatkit || typeof chatkit.setOptions !== 'function') {
      // Retry later
      setTimeout(() => configureChatKit(), 100);
      return;
    }

    console.log('[DB Connect] Configuring ChatKit for session:', sessionId);
    configuredRef.current = true;

    chatkit.setOptions({
      api: {
        url: `${API_BASE_URL}/inventory-agent/chatkit`,
        domainKey: '',
        fetch: async (url: string, options: RequestInit) => {
          try {
            const body = options.body ? JSON.parse(options.body as string) : {};
            body.session_id = sessionId;

            const response = await fetch(url, {
              ...options,
              body: JSON.stringify(body),
              headers: {
                ...options.headers,
                'Content-Type': 'application/json',
                'x-session-id': sessionId,
              },
            });

            return response;
          } catch (e) {
            console.error('[DB Connect] ChatKit fetch error:', e);
            throw e;
          }
        },
      },
      theme: 'light',
      header: {
        enabled: true,
        title: {
          enabled: true,
          text: 'Inventory Management Agent',
        },
      },
      startScreen: {
        greeting: 'Connected to your PostgreSQL database! Ask me anything about inventory.',
        prompts: [
          { label: 'Show Products', prompt: 'Show all products' },
          { label: 'Low Stock', prompt: 'Show low stock items' },
          { label: 'Add Product', prompt: 'Add new product' },
          { label: 'Create Bill', prompt: 'Create a bill' },
        ],
      },
      composer: {
        placeholder: 'Ask about products, stock, bills...',
      },
      disclaimer: {
        text: 'Connected to your own database.',
      },
    });

    console.log('[DB Connect] ChatKit configured successfully');
  }, [isChatkitLoaded, step, sessionId]);

  // Effect to configure ChatKit
  useEffect(() => {
    if (step === 'chat' && isChatkitLoaded) {
      // Small delay to ensure DOM is ready
      const timer = setTimeout(configureChatKit, 100);
      return () => clearTimeout(timer);
    }
  }, [step, isChatkitLoaded, configureChatKit]);

  // Handle ChatKit script load
  const handleScriptLoad = () => {
    console.log('[DB Connect] ChatKit script loaded');
    // Check if custom element is registered
    const checkElement = () => {
      if (customElements.get('openai-chatkit')) {
        console.log('[DB Connect] ChatKit element registered');
        setIsChatkitLoaded(true);
      } else {
        setTimeout(checkElement, 100);
      }
    };
    checkElement();
  };

  // Show loading state while restoring session
  if (restoring) {
    return (
      <div className="max-w-4xl mx-auto py-6">
        <div className="flex flex-col items-center justify-center py-20">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
          <h2 className="text-xl font-semibold text-gray-700">Checking for active session...</h2>
          <p className="text-gray-500 mt-2">Please wait while we restore your connection</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto py-6">
      {/* Load ChatKit Script from OpenAI CDN */}
      <Script
        src="https://cdn.platform.openai.com/deployments/chatkit/chatkit.js"
        strategy="afterInteractive"
        onLoad={handleScriptLoad}
        onError={(e) => console.error('[DB Connect] Failed to load ChatKit:', e)}
      />

      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Connect Your PostgreSQL Database</h1>
        <p className="text-gray-600">
          Connect your own PostgreSQL database and manage inventory with our specialized AI agent.
        </p>
      </div>

      {/* Step indicator */}
      <div className="flex items-center mb-8">
        <div className={`flex items-center ${step === 'connect' ? 'text-blue-600' : 'text-green-600'}`}>
          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
            step === 'connect' ? 'bg-blue-100' : 'bg-green-100'
          }`}>
            {step === 'connect' ? '1' : '✓'}
          </div>
          <span className="ml-2 font-medium">Connect</span>
        </div>
        <div className={`flex-1 h-1 mx-4 ${step !== 'connect' ? 'bg-green-400' : 'bg-gray-200'}`} />
        <div className={`flex items-center ${step === 'setup' ? 'text-blue-600' : step === 'chat' ? 'text-green-600' : 'text-gray-400'}`}>
          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
            step === 'setup' ? 'bg-blue-100' : step === 'chat' ? 'bg-green-100' : 'bg-gray-100'
          }`}>
            {step === 'chat' ? '✓' : '2'}
          </div>
          <span className="ml-2 font-medium">Setup</span>
        </div>
        <div className={`flex-1 h-1 mx-4 ${step === 'chat' ? 'bg-green-400' : 'bg-gray-200'}`} />
        <div className={`flex items-center ${step === 'chat' ? 'text-blue-600' : 'text-gray-400'}`}>
          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
            step === 'chat' ? 'bg-blue-100' : 'bg-gray-100'
          }`}>
            3
          </div>
          <span className="ml-2 font-medium">Manage</span>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">
          {error}
        </div>
      )}

      {/* Step 1: Connect with DATABASE_URI */}
      {step === 'connect' && (
        <div className="space-y-6">
          {/* MCP Status Banner */}
          {checkingMcp ? (
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 flex items-center">
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-gray-600 mr-3"></div>
              <span className="text-gray-600">Checking MCP server status...</span>
            </div>
          ) : mcpStatus && !mcpStatus.postgres_mcp_installed ? (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-start">
                <span className="text-2xl mr-3">⚠️</span>
                <div>
                  <h3 className="font-semibold text-red-800 mb-1">postgres-mcp Not Installed</h3>
                  <p className="text-red-700 text-sm mb-3">
                    The MCP server for PostgreSQL is required. Install it on your server/machine:
                  </p>
                  <code className="bg-red-100 px-3 py-2 rounded text-sm block font-mono text-red-800">
                    pipx install postgres-mcp
                  </code>
                  <p className="text-red-600 text-xs mt-2">
                    After installation, refresh this page to verify.
                  </p>
                </div>
              </div>
            </div>
          ) : mcpStatus?.postgres_mcp_installed && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-center">
                <span className="text-2xl mr-3">✅</span>
                <div>
                  <h3 className="font-semibold text-green-800">MCP Server Ready</h3>
                  <p className="text-green-700 text-sm">
                    postgres-mcp is installed and ready to connect to your database.
                  </p>
                </div>
              </div>
            </div>
          )}

          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4">PostgreSQL Connection via MCP</h2>

            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">Database URI</label>
              <input
                type="text"
                value={databaseUri}
                onChange={(e) => setDatabaseUri(e.target.value)}
                placeholder="postgresql://user:password@host:port/database"
                className="w-full px-4 py-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                disabled={!mcpStatus?.postgres_mcp_installed}
              />
              <p className="mt-2 text-sm text-gray-500">
                Format: <code className="bg-gray-100 px-1 rounded">postgresql://username:password@host:port/dbname</code>
              </p>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
              <h3 className="font-semibold text-blue-800 mb-2">Connection URI Examples</h3>
              <ul className="text-sm text-blue-700 space-y-1">
                <li>Local: <code className="bg-blue-100 px-1 rounded">postgresql://postgres:password@localhost:5432/mydb</code></li>
                <li>Remote: <code className="bg-blue-100 px-1 rounded">postgresql://user:pass@db.example.com:5432/inventory</code></li>
                <li>SSL: <code className="bg-blue-100 px-1 rounded">postgresql://user:pass@host:5432/db?sslmode=require</code></li>
              </ul>
            </div>

            <button
              onClick={connectDatabase}
              disabled={connecting || !databaseUri.trim() || !mcpStatus?.postgres_mcp_installed}
              className="w-full bg-blue-600 text-white py-3 px-4 rounded-md hover:bg-blue-700 disabled:bg-blue-400 disabled:cursor-not-allowed transition-colors font-medium"
            >
              {connecting ? 'Connecting via MCP...' : 'Connect to Database via MCP'}
            </button>
          </div>
        </div>
      )}

      {/* Step 2: Setup Tables */}
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

            {/* MCP Info */}
            {result.mcp_info && (
              <div className="bg-white rounded-lg p-4 mt-4">
                <h3 className="font-semibold mb-2">MCP Server Information</h3>
                <div className="text-sm space-y-1">
                  <div><span className="text-gray-500">Server:</span> {result.mcp_info.server}</div>
                  <div><span className="text-gray-500">Mode:</span> {result.mcp_info.mode}</div>
                </div>
                {result.mcp_info.tools.length > 0 && (
                  <div className="mt-2">
                    <span className="text-sm text-gray-500">Available MCP Tools:</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {result.mcp_info.tools.map((tool, idx) => (
                        <span key={idx} className="bg-blue-100 text-blue-800 px-2 py-0.5 rounded text-xs">{tool}</span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {result.database_info && (
              <div className="bg-white rounded-lg p-4 mt-4">
                <h3 className="font-semibold mb-2">Database Information</h3>
                <div className="text-sm space-y-1">
                  <div><span className="text-gray-500">Version:</span> {result.database_info.version}</div>
                  <div><span className="text-gray-500">Tables:</span> {result.database_info.table_count}</div>
                </div>
                {result.database_info.tables.length > 0 && (
                  <div className="mt-2">
                    <span className="text-sm text-gray-500">Existing tables:</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {result.database_info.tables.map((table, idx) => (
                        <span key={idx} className="bg-gray-100 px-2 py-0.5 rounded text-xs">{table}</span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4">Setup Inventory Tables</h2>
            <p className="text-gray-600 mb-4">
              Create the standard inventory tables in your database:
            </p>
            <ul className="list-disc list-inside text-gray-700 mb-4 space-y-1 text-sm">
              <li><strong>inventory_items</strong> - Products and stock management</li>
              <li><strong>inventory_bills</strong> - Bills and invoices</li>
              <li><strong>inventory_bill_items</strong> - Line items for each bill</li>
            </ul>

            <div className="flex gap-4">
              <button
                onClick={setupTables}
                disabled={setting}
                className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-blue-400 disabled:cursor-not-allowed transition-colors"
              >
                {setting ? 'Creating tables...' : 'Create Tables'}
              </button>
              <button
                onClick={skipSetup}
                className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
              >
                Skip (tables exist)
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Step 3: ChatKit Interface */}
      {step === 'chat' && (
        <div className="space-y-4">
          {/* Header with prominent disconnect button */}
          <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white px-6 py-4 rounded-lg shadow-lg flex justify-between items-center">
            <div>
              <h2 className="text-xl font-semibold">Inventory Management Agent</h2>
              <p className="text-blue-100 text-sm">Session: {sessionId} | Connected via MCP</p>
            </div>
            <button
              onClick={disconnect}
              className="bg-red-500 hover:bg-red-600 px-5 py-2.5 rounded-md transition-colors font-medium shadow-md flex items-center gap-2"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M3 3a1 1 0 00-1 1v12a1 1 0 001 1h12a1 1 0 001-1V4a1 1 0 00-1-1H3zm11 4a1 1 0 10-2 0v4a1 1 0 102 0V7z" clipRule="evenodd" />
              </svg>
              Disconnect
            </button>
          </div>

          {/* Specialized agent notice */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg px-4 py-3">
            <p className="text-sm text-yellow-800">
              <strong>Specialized Agent:</strong> I can ONLY help with inventory operations - add products, manage stock, generate bills. I cannot create custom tables or work with non-inventory data.
            </p>
          </div>

          {/* ChatKit Container */}
          <div className="bg-white rounded-lg shadow-md overflow-hidden" style={{ height: '500px' }}>
            {isChatkitLoaded ? (
              <openai-chatkit
                ref={chatkitRef as any}
                id="inventory-chatkit"
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

      {/* Info Section */}
      <div className="mt-8 bg-blue-50 rounded-lg p-6">
        <h3 className="font-semibold text-blue-800 mb-2">About This Feature - MCP Architecture</h3>
        <ul className="text-sm text-blue-700 space-y-1">
          <li><strong>MCP Protocol:</strong> Uses Model Context Protocol for secure database access</li>
          <li><strong>postgres-mcp:</strong> Based on <a href="https://github.com/crystaldba/postgres-mcp" target="_blank" rel="noopener noreferrer" className="underline">crystaldba/postgres-mcp</a> MCP server</li>
          <li><strong>MCP Tools:</strong> execute_sql, list_schemas, list_objects, get_object_details</li>
          <li><strong>AI Agent:</strong> Uses MCP tools via OpenAI Agents SDK for database operations</li>
          <li><strong>Your data:</strong> Stays in your database - no data storage on our servers</li>
        </ul>
        <div className="mt-4 pt-4 border-t border-blue-200">
          <h4 className="font-semibold text-blue-800 mb-1">How It Works</h4>
          <ol className="text-sm text-blue-700 space-y-1 list-decimal list-inside">
            <li>You provide DATABASE_URI (postgresql://...)</li>
            <li>Backend starts postgres-mcp as subprocess via MCPServerStdio</li>
            <li>Agent connects to MCP server and gets available tools</li>
            <li>All database queries go through MCP protocol (not direct SQL)</li>
          </ol>
        </div>
      </div>

      {/* ChatKit CSS Variables */}
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

// TypeScript declaration for the custom element
declare global {
  namespace JSX {
    interface IntrinsicElements {
      'openai-chatkit': React.DetailedHTMLProps<React.HTMLAttributes<HTMLElement>, HTMLElement>;
    }
  }
}
