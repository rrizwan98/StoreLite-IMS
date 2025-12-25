/**
 * Settings Page
 *
 * User can manage their connected tools and OAuth-based connectors here.
 * - System Tools: Gmail, Analytics, Export (connect/disconnect)
 * - Connectors: OAuth-based connectors like Notion (click to connect via OAuth)
 */

'use client';

import { useState } from 'react';
import Link from 'next/link';
import { ArrowLeft, Settings } from 'lucide-react';
import { SystemToolsList, ConnectorsList } from '@/components/connectors';
import ConnectorDetailView from '@/components/connectors/ConnectorDetailView';
import OAuthConfirmModal from '@/components/connectors/OAuthConfirmModal';
import { initiateOAuth, connectNotion } from '@/lib/connectors-api';
import { PredefinedConnector, PREDEFINED_CONNECTORS } from '@/lib/predefined-connectors';

type View = 'main' | 'connector-detail';

export default function SettingsPage() {
  const [view, setView] = useState<View>('main');
  const [selectedConnector, setSelectedConnector] = useState<PredefinedConnector | null>(null);
  const [showOAuthConfirm, setShowOAuthConfirm] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  function handlePredefinedConnectorClick(connector: PredefinedConnector) {
    setSelectedConnector(connector);
    setView('connector-detail');
  }

  function handleBack() {
    setView('main');
    setSelectedConnector(null);
    // Refresh connectors list
    setRefreshKey(prev => prev + 1);
  }

  function handleConnectClick() {
    if (!selectedConnector) return;
    setShowOAuthConfirm(true);
  }

  async function handleOAuthConfirm() {
    if (!selectedConnector) return;

    setIsConnecting(true);

    try {
      // Use the new Notion MCP OAuth endpoint (Zero-config, no developer credentials needed!)
      if (selectedConnector.id === 'notion') {
        // Use Notion MCP with Dynamic Client Registration
        const response = await connectNotion();
        console.log(`[OAuth] Using ${response.method} method for Notion`);

        // Redirect user to Notion's OAuth page
        window.location.href = response.authorization_url;
      } else {
        // For other connectors, use the old OAuth flow
        const callbackUrl = `${window.location.origin}/connectors/callback`;
        const response = await initiateOAuth(selectedConnector.id, callbackUrl);
        window.location.href = response.authorization_url;
      }
    } catch (error) {
      console.error('Failed to initiate OAuth:', error);
      setIsConnecting(false);
      setShowOAuthConfirm(false);
    }
  }

  // Check if selected connector is already connected
  const isConnectorConnected = false; // Will be updated by ConnectorsList component

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

            {/* Connectors Section */}
            <section className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">Connectors</h2>
                  <p className="text-sm text-gray-500 mt-1">
                    Connect to external services like Notion
                  </p>
                </div>
              </div>
              <div className="p-6" key={refreshKey}>
                <ConnectorsList
                  onConnectorClick={handlePredefinedConnectorClick}
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
                  <strong>Connectors:</strong> Click on a connector like Notion to connect via OAuth.
                  Your Schema Agent will automatically have access to the connected tools.
                </li>
                <li>
                  <strong>Using in Chat:</strong> Once connected, use the Attach button in chat to select
                  tools for your queries.
                </li>
              </ul>
            </section>
          </div>
        ) : view === 'connector-detail' && selectedConnector ? (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden max-w-2xl mx-auto">
            <ConnectorDetailView
              connector={selectedConnector}
              onBack={handleBack}
              onConnect={handleConnectClick}
              isConnected={isConnectorConnected}
              isConnecting={isConnecting}
            />
          </div>
        ) : null}
      </main>

      {/* OAuth Confirmation Modal */}
      {selectedConnector && (
        <OAuthConfirmModal
          isOpen={showOAuthConfirm}
          onClose={() => setShowOAuthConfirm(false)}
          onConfirm={handleOAuthConfirm}
          connector={selectedConnector}
          isLoading={isConnecting}
        />
      )}
    </div>
  );
}
