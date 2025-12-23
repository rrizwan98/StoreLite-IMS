/**
 * ConnectorsList Component
 *
 * Displays list of user's custom MCP connectors with status and actions.
 * Used in the Apps/Tools settings page.
 */

'use client';

import { useState, useEffect } from 'react';
import {
  Server,
  Check,
  X,
  Loader2,
  AlertCircle,
  Plus,
  MoreVertical,
  RefreshCw,
  Trash2,
  Power,
  PowerOff,
  ShieldCheck,
} from 'lucide-react';
import { Connector, getConnectors, deleteConnector, toggleConnector, verifyConnector } from '@/lib/connectors-api';

interface ConnectorsListProps {
  onAddConnector?: () => void;
  onEditConnector?: (connector: Connector) => void;
  onConnectorClick?: (connector: Connector) => void;
}

export default function ConnectorsList({
  onAddConnector,
  onEditConnector,
  onConnectorClick,
}: ConnectorsListProps) {
  const [connectors, setConnectors] = useState<Connector[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<number | null>(null);

  useEffect(() => {
    loadConnectors();
  }, []);

  async function loadConnectors() {
    try {
      setLoading(true);
      setError(null);
      const data = await getConnectors();
      setConnectors(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load connectors');
    } finally {
      setLoading(false);
    }
  }

  async function handleToggle(connector: Connector) {
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

  async function handleDelete(connector: Connector) {
    if (!confirm(`Are you sure you want to delete "${connector.name}"?`)) {
      return;
    }

    try {
      setActionLoading(connector.id);
      await deleteConnector(connector.id);
      setConnectors(prev => prev.filter(c => c.id !== connector.id));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete connector');
    } finally {
      setActionLoading(null);
    }
  }

  async function handleVerify(connector: Connector) {
    try {
      setActionLoading(connector.id);
      setError(null);
      const result = await verifyConnector(connector.id);
      if (result.success && result.connector) {
        setConnectors(prev =>
          prev.map(c => (c.id === connector.id ? result.connector! : c))
        );
      } else {
        setError(result.message || 'Verification failed');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to verify connector');
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
          onClick={loadConnectors}
          className="ml-4 text-sm underline hover:no-underline"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header with Add button */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-500">
          Your Connectors ({connectors.length}/10)
        </h3>
        {onAddConnector && connectors.length < 10 && (
          <button
            onClick={onAddConnector}
            className="flex items-center text-sm text-blue-600 hover:text-blue-700"
          >
            <Plus className="h-4 w-4 mr-1" />
            Add Connector
          </button>
        )}
      </div>

      {/* Connectors list */}
      <div className="space-y-2">
        {connectors.map((connector) => (
          <ConnectorCard
            key={connector.id}
            connector={connector}
            loading={actionLoading === connector.id}
            onClick={() => onConnectorClick?.(connector)}
            onEdit={() => onEditConnector?.(connector)}
            onToggle={() => handleToggle(connector)}
            onDelete={() => handleDelete(connector)}
            onVerify={() => handleVerify(connector)}
          />
        ))}
      </div>

      {/* Empty state */}
      {connectors.length === 0 && (
        <div className="text-center py-8 border-2 border-dashed border-gray-200 rounded-lg">
          <Server className="h-12 w-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500 mb-4">No custom connectors yet</p>
          {onAddConnector && (
            <button
              onClick={onAddConnector}
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              <Plus className="h-4 w-4 mr-2" />
              Add Your First Connector
            </button>
          )}
        </div>
      )}
    </div>
  );
}

interface ConnectorCardProps {
  connector: Connector;
  loading?: boolean;
  onClick?: () => void;
  onEdit?: () => void;
  onToggle?: () => void;
  onDelete?: () => void;
  onVerify?: () => void;
}

function ConnectorCard({
  connector,
  loading,
  onClick,
  onEdit,
  onToggle,
  onDelete,
  onVerify,
}: ConnectorCardProps) {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <div
      className={`
        flex items-center p-4 rounded-lg border transition-colors
        ${connector.is_active
          ? 'bg-white border-gray-200 hover:border-blue-300'
          : 'bg-gray-50 border-gray-200 opacity-60'
        }
      `}
    >
      {/* Icon */}
      <div
        className={`
          flex items-center justify-center w-10 h-10 rounded-lg mr-4
          ${connector.is_verified
            ? 'bg-green-100 text-green-600'
            : connector.is_active
              ? 'bg-blue-100 text-blue-600'
              : 'bg-gray-100 text-gray-400'
          }
        `}
        onClick={onClick}
        style={{ cursor: onClick ? 'pointer' : 'default' }}
      >
        <Server className="h-5 w-5" />
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0" onClick={onClick} style={{ cursor: onClick ? 'pointer' : 'default' }}>
        <div className="flex items-center">
          <h4 className="font-medium text-gray-900">{connector.name}</h4>
          {!connector.is_active && (
            <span className="ml-2 px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-600 rounded">
              Disabled
            </span>
          )}
        </div>
        <p className="text-sm text-gray-500 truncate">
          {connector.description || connector.server_url}
        </p>
        <p className="text-xs text-gray-400">
          {connector.tool_count} tool{connector.tool_count !== 1 ? 's' : ''} available
        </p>
      </div>

      {/* Status */}
      <div className="flex items-center ml-4 mr-2">
        {loading ? (
          <Loader2 className="h-4 w-4 animate-spin text-gray-400" />
        ) : connector.is_verified ? (
          <div className="flex items-center text-green-600">
            <Check className="h-4 w-4 mr-1" />
            <span className="text-sm">Verified</span>
          </div>
        ) : connector.is_active ? (
          <div className="flex items-center text-yellow-600">
            <AlertCircle className="h-4 w-4 mr-1" />
            <span className="text-sm">Unverified</span>
          </div>
        ) : (
          <div className="flex items-center text-gray-400">
            <X className="h-4 w-4 mr-1" />
            <span className="text-sm">Inactive</span>
          </div>
        )}
      </div>

      {/* Actions menu */}
      <div className="relative">
        <button
          onClick={(e) => {
            e.stopPropagation();
            setMenuOpen(!menuOpen);
          }}
          className="p-1 rounded hover:bg-gray-100"
          disabled={loading}
        >
          <MoreVertical className="h-5 w-5 text-gray-400" />
        </button>

        {menuOpen && (
          <>
            <div
              className="fixed inset-0 z-10"
              onClick={() => setMenuOpen(false)}
            />
            <div className="absolute right-0 mt-1 w-48 bg-white rounded-lg shadow-lg border z-20">
              {/* Verify button - show for unverified connectors */}
              {onVerify && !connector.is_verified && (
                <button
                  onClick={() => {
                    setMenuOpen(false);
                    onVerify();
                  }}
                  className="flex items-center w-full px-4 py-2 text-sm text-green-600 hover:bg-green-50"
                >
                  <ShieldCheck className="h-4 w-4 mr-2" />
                  Verify Connection
                </button>
              )}
              {/* Re-verify button - show for verified connectors */}
              {onVerify && connector.is_verified && (
                <button
                  onClick={() => {
                    setMenuOpen(false);
                    onVerify();
                  }}
                  className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                >
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Re-verify & Refresh
                </button>
              )}
              {onEdit && (
                <button
                  onClick={() => {
                    setMenuOpen(false);
                    onEdit();
                  }}
                  className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                >
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Edit
                </button>
              )}
              {onToggle && (
                <button
                  onClick={() => {
                    setMenuOpen(false);
                    onToggle();
                  }}
                  className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                >
                  {connector.is_active ? (
                    <>
                      <PowerOff className="h-4 w-4 mr-2" />
                      Disable
                    </>
                  ) : (
                    <>
                      <Power className="h-4 w-4 mr-2" />
                      Enable
                    </>
                  )}
                </button>
              )}
              {onDelete && (
                <button
                  onClick={() => {
                    setMenuOpen(false);
                    onDelete();
                  }}
                  className="flex items-center w-full px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Delete
                </button>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
