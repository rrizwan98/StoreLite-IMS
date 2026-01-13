/**
 * Developer Tools Page
 *
 * Main page for managing published agents.
 * Organizations can create agents that external users
 * can access via API keys.
 */

'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  Plus, Key, Database, AlertCircle, Loader2,
  ArrowLeft, Settings, Code, BarChart3
} from 'lucide-react';
import { ROUTES } from '@/lib/constants';
import { useAuth } from '@/lib/auth-context';
import { ThemeToggle } from '@/components/theme-toggle';
import {
  listPublishedAgents,
  PublishedAgent,
  AgentListResponse,
} from '@/lib/developer-tools-api';
import AgentCard from './components/agent-card';
import CreateAgentModal from './components/create-agent-modal';

export default function DeveloperToolsPage() {
  const { user, connectionStatus, isLoading, isAuthenticated } = useAuth();
  const router = useRouter();

  // State
  const [agents, setAgents] = useState<PublishedAgent[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [maxAllowed, setMaxAllowed] = useState(10);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Check authentication
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push(ROUTES.LOGIN);
    }
  }, [isAuthenticated, isLoading, router]);

  // Check if database is connected
  const isDatabaseConnected = connectionStatus?.connection_type === 'schema_query_only' &&
    connectionStatus?.schema_status === 'ready';

  // Load agents
  const loadAgents = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await listPublishedAgents();
      setAgents(response.agents);
      setTotalCount(response.total_count);
      setMaxAllowed(response.max_allowed);
    } catch (err) {
      console.error('Failed to load agents:', err);
      setError(err instanceof Error ? err.message : 'Failed to load agents');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated && isDatabaseConnected) {
      loadAgents();
    } else if (isAuthenticated && !isLoading) {
      setLoading(false);
    }
  }, [isAuthenticated, isDatabaseConnected, isLoading]);

  // Handle agent created
  const handleAgentCreated = () => {
    setShowCreateModal(false);
    loadAgents();
  };

  // Handle agent updated/deleted
  const handleAgentChanged = () => {
    loadAgents();
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <Link
                href={ROUTES.SCHEMA_AGENT}
                className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
              >
                <ArrowLeft className="h-5 w-5" />
              </Link>
              <div className="flex items-center gap-2">
                <Key className="h-6 w-6 text-blue-500" />
                <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
                  Developer Tools
                </h1>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <ThemeToggle />
              {user && (
                <span className="text-sm text-gray-600 dark:text-gray-300">
                  {user.email}
                </span>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Prerequisites Check */}
        {!isDatabaseConnected ? (
          <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-6">
            <div className="flex items-start gap-4">
              <AlertCircle className="h-6 w-6 text-yellow-600 dark:text-yellow-400 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="text-lg font-medium text-yellow-800 dark:text-yellow-200">
                  Database Connection Required
                </h3>
                <p className="mt-1 text-yellow-700 dark:text-yellow-300">
                  To create published agents, you need to connect your database first.
                  Published agents will allow external users to query your data with restricted access.
                </p>
                <Link
                  href={ROUTES.SCHEMA_CONNECT}
                  className="mt-4 inline-flex items-center gap-2 px-4 py-2 bg-yellow-600 hover:bg-yellow-700 text-white rounded-lg transition-colors"
                >
                  <Database className="h-4 w-4" />
                  Connect Database
                </Link>
              </div>
            </div>
          </div>
        ) : (
          <>
            {/* Page Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
              <div>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                  Published Agents
                </h2>
                <p className="mt-1 text-gray-600 dark:text-gray-400">
                  Create API keys to let external users query your data with controlled access.
                </p>
              </div>
              <div className="flex items-center gap-4">
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  {totalCount} / {maxAllowed} agents
                </span>
                <button
                  onClick={() => setShowCreateModal(true)}
                  disabled={totalCount >= maxAllowed}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
                >
                  <Plus className="h-4 w-4" />
                  Create Agent
                </button>
              </div>
            </div>

            {/* Error State */}
            {error && (
              <div className="mb-6 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
                <div className="flex items-center gap-2 text-red-700 dark:text-red-400">
                  <AlertCircle className="h-5 w-5" />
                  <span>{error}</span>
                </div>
              </div>
            )}

            {/* Loading State */}
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
              </div>
            ) : agents.length === 0 ? (
              /* Empty State */
              <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-12 text-center">
                <Key className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                  No Published Agents Yet
                </h3>
                <p className="text-gray-600 dark:text-gray-400 mb-6 max-w-md mx-auto">
                  Create your first published agent to allow external users to query your data
                  through a secure API.
                </p>
                <button
                  onClick={() => setShowCreateModal(true)}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                >
                  <Plus className="h-4 w-4" />
                  Create Your First Agent
                </button>
              </div>
            ) : (
              /* Agent Cards Grid */
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {agents.map((agent) => (
                  <AgentCard
                    key={agent.id}
                    agent={agent}
                    onUpdate={handleAgentChanged}
                    onDelete={handleAgentChanged}
                  />
                ))}
              </div>
            )}

            {/* Info Section */}
            <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
                <div className="flex items-center gap-3 mb-3">
                  <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                    <Key className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                  </div>
                  <h3 className="font-medium text-gray-900 dark:text-white">API Keys</h3>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Each agent gets a unique API key. External users authenticate with the X-API-Key header.
                </p>
              </div>

              <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
                <div className="flex items-center gap-3 mb-3">
                  <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-lg">
                    <Code className="h-5 w-5 text-green-600 dark:text-green-400" />
                  </div>
                  <h3 className="font-medium text-gray-900 dark:text-white">Embed Code</h3>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Get ready-to-use ChatKit widget code to embed in any website.
                </p>
              </div>

              <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
                <div className="flex items-center gap-3 mb-3">
                  <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                    <BarChart3 className="h-5 w-5 text-purple-600 dark:text-purple-400" />
                  </div>
                  <h3 className="font-medium text-gray-900 dark:text-white">Usage Analytics</h3>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Track queries, response times, and success rates for each agent.
                </p>
              </div>
            </div>
          </>
        )}
      </main>

      {/* Create Agent Modal */}
      {showCreateModal && (
        <CreateAgentModal
          onClose={() => setShowCreateModal(false)}
          onCreated={handleAgentCreated}
        />
      )}
    </div>
  );
}
