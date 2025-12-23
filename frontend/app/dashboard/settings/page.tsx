/**
 * Settings Page
 *
 * User can manage their connected tools and MCP connectors here.
 * - System Tools: Gmail, Analytics, Export (connect/disconnect)
 * - MCP Connectors: User's custom MCP server connections (add/edit/delete)
 */

'use client';

import { useState } from 'react';
import Link from 'next/link';
import { ArrowLeft, Plus, Settings } from 'lucide-react';
import { SystemToolsList, ConnectorsList, AddConnectorForm } from '@/components/connectors';
import { Connector } from '@/lib/connectors-api';

type View = 'main' | 'add-connector';

export default function SettingsPage() {
  const [view, setView] = useState<View>('main');
  const [refreshKey, setRefreshKey] = useState(0);

  function handleConnectorAdded(connector: Connector) {
    console.log('Connector added:', connector);
    setView('main');
    // Refresh the connectors list
    setRefreshKey(prev => prev + 1);
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Link
                href="/dashboard"
                className="flex items-center text-gray-600 hover:text-gray-900 transition-colors"
              >
                <ArrowLeft className="h-5 w-5 mr-2" />
                Back to Dashboard
              </Link>
            </div>
            <div className="flex items-center space-x-2">
              <Settings className="h-6 w-6 text-gray-600" />
              <h1 className="text-xl font-semibold text-gray-900">Settings</h1>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8 max-w-4xl">
        {view === 'main' ? (
          <div className="space-y-8">
            {/* System Tools Section */}
            <section className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
                <h2 className="text-lg font-semibold text-gray-900">System Tools</h2>
                <p className="text-sm text-gray-500 mt-1">
                  Connect to built-in tools like Gmail and Analytics
                </p>
              </div>
              <div className="p-6">
                <SystemToolsList showBeta={true} />
              </div>
            </section>

            {/* MCP Connectors Section */}
            <section className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-lg font-semibold text-gray-900">MCP Connectors</h2>
                    <p className="text-sm text-gray-500 mt-1">
                      Connect to external MCP servers for custom tools
                    </p>
                  </div>
                  <button
                    onClick={() => setView('add-connector')}
                    className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    Add Connector
                  </button>
                </div>
              </div>
              <div className="p-6" key={refreshKey}>
                <ConnectorsList
                  onAddConnector={() => setView('add-connector')}
                  onEditConnector={(connector) => {
                    console.log('Edit connector:', connector);
                    // TODO: Open edit modal
                  }}
                />
              </div>
            </section>

            {/* Help Section */}
            <section className="bg-blue-50 rounded-xl border border-blue-200 p-6">
              <h3 className="font-semibold text-blue-900 mb-2">How it works</h3>
              <ul className="text-sm text-blue-800 space-y-2">
                <li>
                  <strong>System Tools:</strong> Built-in integrations like Gmail. Click "Connect" to enable.
                </li>
                <li>
                  <strong>MCP Connectors:</strong> Connect to external MCP servers. The connection will be
                  tested and verified before saving.
                </li>
                <li>
                  <strong>Using in Chat:</strong> Once connected, use the Attach button in chat to select
                  tools for your queries.
                </li>
              </ul>
            </section>
          </div>
        ) : view === 'add-connector' ? (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 max-w-2xl mx-auto">
            <AddConnectorForm
              onSuccess={handleConnectorAdded}
              onCancel={() => setView('main')}
            />
          </div>
        ) : null}
      </main>
    </div>
  );
}
