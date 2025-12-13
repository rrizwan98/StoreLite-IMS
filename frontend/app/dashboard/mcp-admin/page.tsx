/**
 * MCP Admin Page
 * Inventory management for users with their own database (via MCP)
 * Uses ChatKit to interact with user's database through MCP agent
 */

'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import Script from 'next/script';
import { ROUTES, APP_METADATA, API_BASE_URL } from '@/lib/constants';
import { useAuth } from '@/lib/auth-context';
import { getAccessToken } from '@/lib/auth-api';

export default function MCPAdminPage() {
  const { user, connectionStatus, logout, isLoading } = useAuth();
  const router = useRouter();

  const [isChatkitLoaded, setIsChatkitLoaded] = useState(false);
  const chatkitRef = useRef<HTMLElement | null>(null);
  const configuredRef = useRef(false);

  // Derived state
  const isOwnDatabase = connectionStatus?.connection_type === 'own_database';
  const mcpConnected = connectionStatus?.mcp_status === 'connected';
  const mcpSessionId = connectionStatus?.mcp_session_id;

  // Redirect if not own_database user
  useEffect(() => {
    if (!isLoading) {
      if (!isOwnDatabase) {
        router.push(ROUTES.ADMIN); // Redirect to regular Admin
      } else if (!mcpConnected || !mcpSessionId) {
        router.push(ROUTES.DB_CONNECT); // Need to connect first
      }
    }
  }, [isLoading, isOwnDatabase, mcpConnected, mcpSessionId, router]);

  // Configure ChatKit for Admin operations
  const configureChatKit = useCallback(() => {
    if (!isChatkitLoaded || !mcpSessionId) return;
    if (configuredRef.current) return;

    const chatkit = chatkitRef.current as any;
    if (!chatkit || typeof chatkit.setOptions !== 'function') {
      setTimeout(() => configureChatKit(), 100);
      return;
    }

    configuredRef.current = true;
    console.log('[MCP-Admin] Configuring ChatKit with session:', mcpSessionId);

    chatkit.setOptions({
      api: {
        url: `${API_BASE_URL}/inventory-agent/chatkit`,
        domainKey: '',
        fetch: async (url: string, options: RequestInit) => {
          try {
            const body = options.body ? JSON.parse(options.body as string) : {};
            body.session_id = mcpSessionId;
            body.user_id = user?.id;

            return await fetch(url, {
              ...options,
              body: JSON.stringify(body),
              headers: {
                ...options.headers,
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getAccessToken()}`,
                'x-session-id': mcpSessionId,
              },
            });
          } catch (e) {
            console.error('[MCP-Admin] ChatKit fetch error:', e);
            throw e;
          }
        },
      },
      theme: 'light',
      header: {
        enabled: true,
        title: { enabled: true, text: 'Admin - Your Database' },
      },
      startScreen: {
        greeting: 'Inventory Admin - Manage products and inventory in your database!',
        prompts: [
          { label: 'View All Items', prompt: 'Show all products in my inventory with their stock levels' },
          { label: 'Add Product', prompt: 'I want to add a new product to the inventory. Guide me through the process.' },
          { label: 'Update Stock', prompt: 'Help me update the stock quantity for a product' },
          { label: 'Categories', prompt: 'Show me all product categories and count of items in each' },
        ],
      },
      composer: { placeholder: 'Add products, update stock, manage inventory...' },
      disclaimer: { text: 'Connected to your database via MCP' },
    });
  }, [isChatkitLoaded, mcpSessionId, user?.id]);

  useEffect(() => {
    if (isChatkitLoaded && mcpSessionId) {
      const timer = setTimeout(configureChatKit, 100);
      return () => clearTimeout(timer);
    }
  }, [isChatkitLoaded, mcpSessionId, configureChatKit]);

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

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  // Show loading while waiting for MCP session
  if (!mcpConnected || !mcpSessionId) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Connecting to your database...</p>
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
              <Link href={ROUTES.MCP_ADMIN} className="text-blue-600 font-medium">Admin</Link>
              <Link href={ROUTES.MCP_POS} className="text-gray-600 hover:text-gray-900">POS</Link>
              <Link href={ROUTES.ANALYTICS} className="text-gray-600 hover:text-gray-900">Analytics</Link>
              <Link href={ROUTES.DB_CONNECT} className="text-gray-600 hover:text-gray-900">Connection</Link>
            </nav>
          </div>
          <div className="flex items-center space-x-4">
            <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">Your Database</span>
            <span className="text-gray-600 text-sm">{user?.email}</span>
            <button onClick={logout} className="text-gray-600 hover:text-gray-900 text-sm">
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Inventory Admin</h1>
          <p className="text-gray-600">
            Manage products, update stock levels, and organize your inventory using AI assistance.
          </p>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <button
            onClick={() => {
              const chatkit = chatkitRef.current as any;
              if (chatkit?.sendMessage) {
                chatkit.sendMessage({ content: 'Show all products in the inventory with stock levels' });
              }
            }}
            className="p-4 bg-white rounded-lg shadow hover:shadow-md transition-shadow text-left"
          >
            <span className="text-2xl mb-2 block">📦</span>
            <span className="font-medium text-gray-900">All Products</span>
          </button>
          <button
            onClick={() => {
              const chatkit = chatkitRef.current as any;
              if (chatkit?.sendMessage) {
                chatkit.sendMessage({ content: 'I want to add a new product to the inventory. Ask me for the product details.' });
              }
            }}
            className="p-4 bg-white rounded-lg shadow hover:shadow-md transition-shadow text-left"
          >
            <span className="text-2xl mb-2 block">➕</span>
            <span className="font-medium text-gray-900">Add Product</span>
          </button>
          <button
            onClick={() => {
              const chatkit = chatkitRef.current as any;
              if (chatkit?.sendMessage) {
                chatkit.sendMessage({ content: 'Help me update the stock quantity for a product' });
              }
            }}
            className="p-4 bg-white rounded-lg shadow hover:shadow-md transition-shadow text-left"
          >
            <span className="text-2xl mb-2 block">📊</span>
            <span className="font-medium text-gray-900">Update Stock</span>
          </button>
          <button
            onClick={() => {
              const chatkit = chatkitRef.current as any;
              if (chatkit?.sendMessage) {
                chatkit.sendMessage({ content: 'Show items that need restocking (low stock)' });
              }
            }}
            className="p-4 bg-white rounded-lg shadow hover:shadow-md transition-shadow text-left"
          >
            <span className="text-2xl mb-2 block">⚠️</span>
            <span className="font-medium text-gray-900">Low Stock</span>
          </button>
        </div>

        {/* ChatKit Interface */}
        <div className="bg-white rounded-lg shadow-md overflow-hidden" style={{ height: '600px' }}>
          {isChatkitLoaded ? (
            <openai-chatkit
              ref={chatkitRef as any}
              id="mcp-admin-chatkit"
              style={{ width: '100%', height: '100%', display: 'block' }}
            />
          ) : (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
                <p className="text-gray-600">Loading Admin interface...</p>
              </div>
            </div>
          )}
        </div>

        {/* Help Section */}
        <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <h3 className="font-semibold text-blue-900 mb-2">Admin Capabilities</h3>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>• Add new products with name, price, category, and initial stock</li>
            <li>• Update existing product information</li>
            <li>• Adjust stock quantities (restock or corrections)</li>
            <li>• Search and filter products by name or category</li>
            <li>• View inventory reports and analytics</li>
          </ul>
        </div>
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
