/**
 * Agent Card Component
 *
 * Displays published agent info with actions.
 */

'use client';

import { useState } from 'react';
import {
  Key, Copy, Check, Settings, Trash2, RefreshCw,
  Code, BarChart3, Database, Globe, Clock, Activity,
  MoreVertical, Shield, AlertTriangle
} from 'lucide-react';
import {
  PublishedAgent,
  deletePublishedAgent,
  regenerateApiKey,
  updatePublishedAgent,
  formatDateTime,
  formatNumber,
  getStatusBadge,
  getAccessModeInfo,
} from '@/lib/developer-tools-api';
import EmbedCodeViewer from './embed-code-viewer';
import UsageStatsModal from './usage-stats-modal';

interface AgentCardProps {
  agent: PublishedAgent;
  onUpdate: () => void;
  onDelete: () => void;
}

export default function AgentCard({ agent, onUpdate, onDelete }: AgentCardProps) {
  const [showMenu, setShowMenu] = useState(false);
  const [showEmbedCode, setShowEmbedCode] = useState(false);
  const [showUsageStats, setShowUsageStats] = useState(false);
  const [copied, setCopied] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [showRegenerateConfirm, setShowRegenerateConfirm] = useState(false);
  const [newApiKey, setNewApiKey] = useState<string | null>(null);

  const statusBadge = getStatusBadge(agent.is_active);
  const accessMode = getAccessModeInfo(agent.access_mode);

  // Copy API key prefix
  const handleCopyPrefix = async () => {
    try {
      await navigator.clipboard.writeText(agent.api_key_prefix);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  // Toggle active status
  const handleToggleActive = async () => {
    setLoading(true);
    setError('');
    try {
      await updatePublishedAgent(agent.id, { is_active: !agent.is_active });
      onUpdate();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update');
    } finally {
      setLoading(false);
      setShowMenu(false);
    }
  };

  // Delete agent
  const handleDelete = async () => {
    setLoading(true);
    setError('');
    try {
      await deletePublishedAgent(agent.id);
      onDelete();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete');
      setLoading(false);
    }
    setShowDeleteConfirm(false);
  };

  // Regenerate API key
  const handleRegenerate = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await regenerateApiKey(agent.id);
      setNewApiKey(response.api_key);
      onUpdate();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to regenerate');
    } finally {
      setLoading(false);
      setShowRegenerateConfirm(false);
    }
  };

  // Copy new API key
  const handleCopyNewKey = async () => {
    if (newApiKey) {
      await navigator.clipboard.writeText(newApiKey);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <>
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
        {/* Header */}
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-start justify-between">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white truncate">
                  {agent.name}
                </h3>
                <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${statusBadge.bgColor} ${statusBadge.color}`}>
                  {statusBadge.label}
                </span>
              </div>
              {agent.description && (
                <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
                  {agent.description}
                </p>
              )}
            </div>
            <div className="relative ml-2">
              <button
                onClick={() => setShowMenu(!showMenu)}
                className="p-1 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 rounded"
              >
                <MoreVertical className="h-5 w-5" />
              </button>
              {showMenu && (
                <div className="absolute right-0 mt-1 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 py-1 z-10">
                  <button
                    onClick={handleToggleActive}
                    className="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2"
                  >
                    <Shield className="h-4 w-4" />
                    {agent.is_active ? 'Deactivate' : 'Activate'}
                  </button>
                  <button
                    onClick={() => { setShowRegenerateConfirm(true); setShowMenu(false); }}
                    className="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2"
                  >
                    <RefreshCw className="h-4 w-4" />
                    Regenerate Key
                  </button>
                  <hr className="my-1 border-gray-200 dark:border-gray-700" />
                  <button
                    onClick={() => { setShowDeleteConfirm(true); setShowMenu(false); }}
                    className="w-full px-4 py-2 text-left text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 flex items-center gap-2"
                  >
                    <Trash2 className="h-4 w-4" />
                    Delete Agent
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="px-4 py-2 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm">
            {error}
          </div>
        )}

        {/* New API Key Display */}
        {newApiKey && (
          <div className="px-4 py-3 bg-green-50 dark:bg-green-900/20 border-b border-green-200 dark:border-green-800">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-green-800 dark:text-green-200">
                  New API Key Generated
                </p>
                <p className="text-xs text-green-600 dark:text-green-400">
                  Save this key now - it won&apos;t be shown again!
                </p>
              </div>
              <button
                onClick={handleCopyNewKey}
                className="flex items-center gap-1 px-3 py-1 bg-green-600 hover:bg-green-700 text-white text-sm rounded transition-colors"
              >
                {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                {copied ? 'Copied!' : 'Copy Key'}
              </button>
            </div>
            <code className="mt-2 block text-xs text-green-700 dark:text-green-300 bg-green-100 dark:bg-green-900/40 p-2 rounded font-mono break-all">
              {newApiKey}
            </code>
          </div>
        )}

        {/* Content */}
        <div className="p-4 space-y-4">
          {/* API Key */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
              <Key className="h-4 w-4" />
              <span className="font-mono">{agent.api_key_prefix}</span>
            </div>
            <button
              onClick={handleCopyPrefix}
              className="p-1 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
              title="Copy API key prefix"
            >
              {copied ? <Check className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
            </button>
          </div>

          {/* Stats Row */}
          <div className="grid grid-cols-2 gap-4">
            <div className="flex items-center gap-2 text-sm">
              <Database className="h-4 w-4 text-gray-400" />
              <span className="text-gray-600 dark:text-gray-400">
                {agent.allowed_tables.length} table{agent.allowed_tables.length !== 1 ? 's' : ''}
              </span>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <span className={`px-2 py-0.5 text-xs rounded-full ${accessMode.bgColor} ${accessMode.color}`}>
                {accessMode.label}
              </span>
            </div>
          </div>

          {/* Tables List */}
          <div className="flex flex-wrap gap-1">
            {agent.allowed_tables.slice(0, 5).map((table) => (
              <span
                key={table}
                className="px-2 py-0.5 text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded"
              >
                {table}
              </span>
            ))}
            {agent.allowed_tables.length > 5 && (
              <span className="px-2 py-0.5 text-xs bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 rounded">
                +{agent.allowed_tables.length - 5} more
              </span>
            )}
          </div>

          {/* Usage Stats */}
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400">
              <Activity className="h-4 w-4" />
              <span>{formatNumber(agent.total_queries)} queries</span>
            </div>
            <div className="flex items-center gap-2 text-gray-500 dark:text-gray-500">
              <Clock className="h-4 w-4" />
              <span>{formatDateTime(agent.last_used_at)}</span>
            </div>
          </div>

          {/* Domains */}
          <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
            <Globe className="h-4 w-4" />
            <span>
              {agent.allowed_domains.includes('*')
                ? 'All domains'
                : `${agent.allowed_domains.length} domain${agent.allowed_domains.length !== 1 ? 's' : ''}`}
            </span>
          </div>
        </div>

        {/* Actions */}
        <div className="px-4 py-3 bg-gray-50 dark:bg-gray-800/50 border-t border-gray-200 dark:border-gray-700 flex gap-2">
          <button
            onClick={() => setShowEmbedCode(true)}
            className="flex-1 flex items-center justify-center gap-2 px-3 py-2 text-sm font-medium text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors"
          >
            <Code className="h-4 w-4" />
            Embed Code
          </button>
          <button
            onClick={() => setShowUsageStats(true)}
            className="flex-1 flex items-center justify-center gap-2 px-3 py-2 text-sm font-medium text-purple-600 dark:text-purple-400 hover:bg-purple-50 dark:hover:bg-purple-900/20 rounded-lg transition-colors"
          >
            <BarChart3 className="h-4 w-4" />
            Usage Stats
          </button>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg max-w-md w-full p-6">
            <div className="flex items-center gap-3 text-red-600 dark:text-red-400 mb-4">
              <AlertTriangle className="h-6 w-6" />
              <h3 className="text-lg font-semibold">Delete Agent?</h3>
            </div>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              This will immediately revoke the API key and remove all configuration.
              External integrations using this agent will stop working.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                disabled={loading}
                className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors disabled:opacity-50"
              >
                {loading ? 'Deleting...' : 'Delete Agent'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Regenerate Confirmation Modal */}
      {showRegenerateConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg max-w-md w-full p-6">
            <div className="flex items-center gap-3 text-yellow-600 dark:text-yellow-400 mb-4">
              <RefreshCw className="h-6 w-6" />
              <h3 className="text-lg font-semibold">Regenerate API Key?</h3>
            </div>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              This will immediately revoke the current API key.
              All existing integrations will need to be updated with the new key.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setShowRegenerateConfirm(false)}
                className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleRegenerate}
                disabled={loading}
                className="flex-1 px-4 py-2 bg-yellow-600 hover:bg-yellow-700 text-white rounded-lg transition-colors disabled:opacity-50"
              >
                {loading ? 'Regenerating...' : 'Regenerate Key'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Embed Code Viewer */}
      {showEmbedCode && (
        <EmbedCodeViewer
          agentId={agent.id}
          agentName={agent.name}
          onClose={() => setShowEmbedCode(false)}
        />
      )}

      {/* Usage Stats Modal */}
      {showUsageStats && (
        <UsageStatsModal
          agentId={agent.id}
          agentName={agent.name}
          onClose={() => setShowUsageStats(false)}
        />
      )}
    </>
  );
}
