/**
 * ConnectorsList Component
 *
 * Shows predefined OAuth connectors (like Notion) and user's connected connectors.
 * No "Add Connector" button - users click on predefined connectors to connect.
 */

'use client';

import { useState, useEffect } from 'react';
import Image from 'next/image';
import {
  Check,
  Loader2,
  AlertCircle,
  ChevronRight,
  Trash2,
  Power,
  PowerOff,
} from 'lucide-react';
import {
  Connector,
  getConnectors,
  deleteConnector,
  toggleConnector,
  getNotionStatus,
  OAuthStatus,
} from '@/lib/connectors-api';
import {
  PREDEFINED_CONNECTORS,
  PredefinedConnector,
} from '@/lib/predefined-connectors';

interface ConnectorsListProps {
  onConnectorClick?: (connector: PredefinedConnector) => void;
  onConnectedConnectorClick?: (connector: Connector) => void;
}

export default function ConnectorsList({
  onConnectorClick,
  onConnectedConnectorClick,
}: ConnectorsListProps) {
  const [connectors, setConnectors] = useState<Connector[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<number | null>(null);
  const [oauthStatuses, setOauthStatuses] = useState<Record<string, OAuthStatus>>({});

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      setLoading(true);
      setError(null);

      // Load user's connectors and OAuth statuses in parallel
      const [connectorsData, statuses] = await Promise.all([
        getConnectors(),
        loadOAuthStatuses(),
      ]);

      setConnectors(connectorsData);
      setOauthStatuses(statuses);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load connectors');
    } finally {
      setLoading(false);
    }
  }

  async function loadOAuthStatuses(): Promise<Record<string, OAuthStatus>> {
    const statuses: Record<string, OAuthStatus> = {};

    // Check Notion status using new endpoint
    try {
      const notionStatus = await getNotionStatus();
      statuses['notion'] = {
        connected: notionStatus.connected,
        connector_id: notionStatus.connector_id,
        connector_name: notionStatus.connector_name,
      };
    } catch {
      statuses['notion'] = { connected: false };
    }

    // Add other connectors here in future...

    return statuses;
  }

  async function handleToggle(connector: Connector, e: React.MouseEvent) {
    e.stopPropagation();
    try {
      setActionLoading(connector.id);
      const updated = await toggleConnector(connector.id, !connector.is_active);
      setConnectors(prev =>
        prev.map(c => (c.id === connector.id ? updated : c))
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to toggle connector');
    } finally {
      setActionLoading(null);
    }
  }

  async function handleDelete(connector: Connector, e: React.MouseEvent) {
    e.stopPropagation();
    if (!confirm(`Are you sure you want to disconnect "${connector.name}"?`)) {
      return;
    }

    try {
      setActionLoading(connector.id);
      await deleteConnector(connector.id);
      setConnectors(prev => prev.filter(c => c.id !== connector.id));
      // Reload OAuth statuses
      const statuses = await loadOAuthStatuses();
      setOauthStatuses(statuses);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete connector');
    } finally {
      setActionLoading(null);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
        <span className="ml-2 text-gray-500">Loading connectors...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center p-8 text-red-500">
        <AlertCircle className="h-5 w-5 mr-2" />
        <span>{error}</span>
        <button
          onClick={loadData}
          className="ml-4 text-sm underline hover:no-underline"
        >
          Retry
        </button>
      </div>
    );
  }

  // Find connected connectors by matching MCP server URL
  const getConnectedConnector = (predefined: PredefinedConnector): Connector | undefined => {
    return connectors.find(c => c.server_url === predefined.mcpServerUrl);
  };

  return (
    <div className="space-y-6">
      {/* Available Connectors Section */}
      <div>
        <h3 className="text-sm font-medium text-gray-500 mb-3">
          Available Connectors
        </h3>

        <div className="space-y-2">
          {PREDEFINED_CONNECTORS.map((predefined) => {
            const connectedConnector = getConnectedConnector(predefined);
            const isConnected = !!connectedConnector;

            return (
              <button
                key={predefined.id}
                onClick={() => {
                  if (isConnected && connectedConnector) {
                    onConnectedConnectorClick?.(connectedConnector);
                  } else {
                    onConnectorClick?.(predefined);
                  }
                }}
                className={`
                  w-full flex items-center p-4 rounded-xl border transition-all text-left
                  ${isConnected
                    ? 'bg-green-50 border-green-200 hover:border-green-300'
                    : 'bg-white border-gray-200 hover:border-blue-300 hover:shadow-sm'
                  }
                `}
              >
                {/* Logo */}
                <div className="w-12 h-12 rounded-xl overflow-hidden bg-white border border-gray-100 flex items-center justify-center shadow-sm flex-shrink-0">
                  <Image
                    src={predefined.logo}
                    alt={predefined.name}
                    width={32}
                    height={32}
                    className="object-contain"
                  />
                </div>

                {/* Info */}
                <div className="flex-1 ml-4 min-w-0">
                  <div className="flex items-center">
                    <h4 className="font-medium text-gray-900">{predefined.name}</h4>
                    {isConnected && (
                      <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700">
                        <Check className="h-3 w-3 mr-1" />
                        Connected
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-500 mt-0.5 truncate">
                    {predefined.description}
                  </p>
                </div>

                {/* Actions for connected connectors */}
                {isConnected && connectedConnector && (
                  <div className="flex items-center space-x-1 ml-2" onClick={e => e.stopPropagation()}>
                    {actionLoading === connectedConnector.id ? (
                      <Loader2 className="h-4 w-4 animate-spin text-gray-400" />
                    ) : (
                      <>
                        <button
                          onClick={(e) => handleToggle(connectedConnector, e)}
                          className="p-1.5 rounded-lg hover:bg-gray-100 text-gray-400 hover:text-gray-600"
                          title={connectedConnector.is_active ? 'Disable' : 'Enable'}
                        >
                          {connectedConnector.is_active ? (
                            <Power className="h-4 w-4" />
                          ) : (
                            <PowerOff className="h-4 w-4" />
                          )}
                        </button>
                        <button
                          onClick={(e) => handleDelete(connectedConnector, e)}
                          className="p-1.5 rounded-lg hover:bg-red-50 text-gray-400 hover:text-red-600"
                          title="Disconnect"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </>
                    )}
                  </div>
                )}

                {/* Arrow for unconnected */}
                {!isConnected && (
                  <ChevronRight className="h-5 w-5 text-gray-400 ml-2 flex-shrink-0" />
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Coming Soon */}
      <div className="text-center text-sm text-gray-400 py-4">
        More connectors coming soon...
      </div>
    </div>
  );
}
