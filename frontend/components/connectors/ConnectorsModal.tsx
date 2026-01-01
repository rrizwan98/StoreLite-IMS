/**
 * ConnectorsModal Component
 *
 * Modal for managing MCP connectors - viewing list, adding new, or OAuth flow.
 * Supports both predefined OAuth connectors (like Notion) and custom URL connectors.
 */

'use client';

import { useState, useEffect } from 'react';
import { X } from 'lucide-react';
import AppsToolsPanel from './AppsToolsPanel';
import AddConnectorForm from './AddConnectorForm';
import ConnectorDetailView from './ConnectorDetailView';
import OAuthConfirmModal from './OAuthConfirmModal';
import { Connector, initiateOAuth, getOAuthStatus, connectNotion, getNotionStatus, connectGoogleDrive, getGDriveStatus, connectGmail, getGmailStatus } from '@/lib/connectors-api';
import { SystemTool } from '@/lib/tools-api';
import { PredefinedConnector, PREDEFINED_CONNECTORS } from '@/lib/predefined-connectors';

type ModalView = 'list' | 'add' | 'edit' | 'connector-detail';

interface ConnectorsModalProps {
  isOpen: boolean;
  onClose: () => void;
  defaultTab?: 'system' | 'connectors';
  onToolSelect?: (tool: SystemTool) => void;
  onConnectorSelect?: (connector: Connector) => void;
}

export default function ConnectorsModal({
  isOpen,
  onClose,
  defaultTab = 'connectors',
  onToolSelect,
  onConnectorSelect,
}: ConnectorsModalProps) {
  const [view, setView] = useState<ModalView>('list');
  const [editConnector, setEditConnector] = useState<Connector | null>(null);
  const [selectedPredefined, setSelectedPredefined] = useState<PredefinedConnector | null>(null);
  const [showOAuthConfirm, setShowOAuthConfirm] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [connectedPredefinedIds, setConnectedPredefinedIds] = useState<string[]>([]);
  const [oauthError, setOAuthError] = useState<string | null>(null);

  // Reset view when modal opens
  useEffect(() => {
    if (isOpen) {
      setView('list');
      setEditConnector(null);
      setSelectedPredefined(null);
      setShowOAuthConfirm(false);
      setOAuthError(null);
      loadOAuthStatuses();
    }
  }, [isOpen]);

  // Load OAuth connection statuses for predefined connectors
  async function loadOAuthStatuses() {
    try {
      const connectedIds: string[] = [];

      // Check Notion status
      try {
        const notionStatus = await getNotionStatus();
        if (notionStatus.connected) {
          connectedIds.push('notion');
        }
      } catch {
        // Notion not connected or error
      }

      // Check Google Drive status
      try {
        const gdriveStatus = await getGDriveStatus();
        if (gdriveStatus.connected) {
          connectedIds.push('google_drive');
        }
      } catch {
        // Google Drive not connected or error
      }

      // Check Gmail status
      try {
        const gmailStatus = await getGmailStatus();
        if (gmailStatus.connected) {
          connectedIds.push('gmail');
        }
      } catch {
        // Gmail not connected or error
      }

      setConnectedPredefinedIds(connectedIds);
    } catch (error) {
      console.error('Failed to load OAuth statuses:', error);
    }
  }

  if (!isOpen) return null;

  function handleConnectorSuccess() {
    setView('list');
    setEditConnector(null);
    loadOAuthStatuses();
  }

  function handleCancel() {
    setView('list');
    setEditConnector(null);
    setSelectedPredefined(null);
  }

  function handlePredefinedConnectorClick(connector: PredefinedConnector) {
    setSelectedPredefined(connector);
    setView('connector-detail');
  }

  function handleConnectClick() {
    if (!selectedPredefined) return;
    setShowOAuthConfirm(true);
  }

  async function handleOAuthConfirm() {
    if (!selectedPredefined) {
      console.error('[OAuth] No connector selected');
      return;
    }

    console.log(`[OAuth] Starting OAuth for connector: ${selectedPredefined.id}`);
    setIsConnecting(true);
    setOAuthError(null);

    try {
      if (selectedPredefined.id === 'notion') {
        // Use Notion MCP with Dynamic Client Registration
        console.log('[OAuth] Calling connectNotion()...');
        const response = await connectNotion();
        console.log(`[OAuth] Using ${response.method} method for Notion`);
        console.log(`[OAuth] Redirecting to: ${response.authorization_url}`);
        // Redirect user to Notion's OAuth page
        window.location.href = response.authorization_url;
      } else if (selectedPredefined.id === 'google_drive') {
        // Use Google Drive OAuth flow
        console.log('[OAuth] Calling connectGoogleDrive()...');
        const response = await connectGoogleDrive();
        console.log('[OAuth] Starting Google Drive OAuth flow');
        console.log(`[OAuth] Redirecting to: ${response.authorization_url}`);
        // Redirect user to Google's OAuth page
        window.location.href = response.authorization_url;
      } else if (selectedPredefined.id === 'gmail') {
        // Use Gmail OAuth flow
        console.log('[OAuth] Calling connectGmail()...');
        const response = await connectGmail();
        console.log('[OAuth] Starting Gmail OAuth flow');
        console.log(`[OAuth] Redirecting to: ${response.authorization_url}`);
        // Redirect user to Google's OAuth page
        window.location.href = response.authorization_url;
      } else {
        // For other connectors, use the generic OAuth flow
        console.log(`[OAuth] Using generic OAuth for: ${selectedPredefined.id}`);
        const callbackUrl = `${window.location.origin}/connectors/callback`;
        const response = await initiateOAuth(selectedPredefined.id, callbackUrl);
        console.log(`[OAuth] Redirecting to: ${response.authorization_url}`);
        window.location.href = response.authorization_url;
      }
    } catch (error) {
      console.error('[OAuth] Failed to initiate OAuth:', error);
      setIsConnecting(false);
      setShowOAuthConfirm(false);

      // Show user-friendly error message
      const errorMessage = error instanceof Error ? error.message : 'Failed to connect';
      console.error(`[OAuth] Error message: ${errorMessage}`);
      setOAuthError(errorMessage);
    }
  }

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 z-40"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="fixed inset-4 md:inset-auto md:top-1/2 md:left-1/2 md:-translate-x-1/2 md:-translate-y-1/2 md:w-full md:max-w-2xl md:max-h-[80vh] bg-white rounded-xl shadow-xl z-50 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h2 className="text-lg font-semibold text-gray-900">
            {view === 'list' && 'Apps & Tools'}
            {view === 'add' && 'Custom Connector'}
            {view === 'edit' && 'Edit Connector'}
            {view === 'connector-detail' && selectedPredefined?.name}
          </h2>
          <button
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <X className="h-5 w-5 text-gray-500" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto">
          {view === 'list' && (
            <AppsToolsPanel
              defaultTab={defaultTab}
              onSystemToolClick={onToolSelect}
              onPredefinedConnectorClick={handlePredefinedConnectorClick}
              onConnectedConnectorClick={onConnectorSelect}
            />
          )}

          {view === 'connector-detail' && selectedPredefined && (
            <div>
              <ConnectorDetailView
                connector={selectedPredefined}
                onBack={handleCancel}
                onConnect={handleConnectClick}
                isConnected={connectedPredefinedIds.includes(selectedPredefined.id)}
                isConnecting={isConnecting}
              />
              {/* Error message */}
              {oauthError && (
                <div className="mx-6 mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                  <p className="text-sm text-red-700">{oauthError}</p>
                  <button
                    onClick={() => setOAuthError(null)}
                    className="mt-2 text-xs text-red-600 underline hover:no-underline"
                  >
                    Dismiss
                  </button>
                </div>
              )}
            </div>
          )}

          {view === 'add' && (
            <div className="p-6">
              <AddConnectorForm
                onSuccess={handleConnectorSuccess}
                onCancel={handleCancel}
              />
            </div>
          )}

          {view === 'edit' && editConnector && (
            <div className="p-6">
              <EditConnectorView
                connector={editConnector}
                onSuccess={handleConnectorSuccess}
                onCancel={handleCancel}
              />
            </div>
          )}
        </div>
      </div>

      {/* OAuth Confirmation Modal */}
      {selectedPredefined && (
        <OAuthConfirmModal
          isOpen={showOAuthConfirm}
          onClose={() => setShowOAuthConfirm(false)}
          onConfirm={handleOAuthConfirm}
          connector={selectedPredefined}
          isLoading={isConnecting}
        />
      )}
    </>
  );
}

/**
 * Edit Connector View - For editing existing connectors
 */
interface EditConnectorViewProps {
  connector: Connector;
  onSuccess: () => void;
  onCancel: () => void;
}

function EditConnectorView({ connector, onSuccess, onCancel }: EditConnectorViewProps) {
  const [name, setName] = useState(connector.name);
  const [description, setDescription] = useState(connector.description || '');
  const [saving, setSaving] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      const { updateConnector } = await import('@/lib/connectors-api');
      await updateConnector(connector.id, { name, description });
      onSuccess();
    } catch (err) {
      console.error('Failed to update connector:', err);
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
          Connector Name
        </label>
        <input
          id="name"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div>
        <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
          Description
        </label>
        <textarea
          id="description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={2}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div className="flex justify-end space-x-3 pt-4 border-t">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 text-gray-700 hover:text-gray-900"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={saving}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-blue-300"
        >
          {saving ? 'Saving...' : 'Save Changes'}
        </button>
      </div>
    </form>
  );
}
