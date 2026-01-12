/**
 * Schema Connect Page
 *
 * For schema_query_only users to:
 * - Discover their database schema
 * - View tables and columns
 * - Refresh schema metadata
 * - Optionally upgrade to full IMS mode
 */

'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { ROUTES, API_BASE_URL, APP_METADATA } from '@/lib/constants';
import { useAuth } from '@/lib/auth-context';
import { getAccessToken } from '@/lib/auth-api';
import { ThemeToggle } from '@/components/theme-toggle';

interface TableInfo {
  name: string;
  type: string;
  column_count: number;
}

interface ColumnInfo {
  name: string;
  type: string;
  nullable: boolean;
  primary_key: boolean;
  foreign_key?: string;
}

interface SchemaMetadata {
  tables: TableInfo[];
  table_count: number;
  discovered_at: string;
}

export default function SchemaConnectPage() {
  const { user, connectionStatus, isLoading, isAuthenticated, refreshConnectionStatus } = useAuth();
  const router = useRouter();

  const [discovering, setDiscovering] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [upgrading, setUpgrading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const [schemaMetadata, setSchemaMetadata] = useState<SchemaMetadata | null>(null);
  const [selectedTable, setSelectedTable] = useState<string | null>(null);
  const [tableDetails, setTableDetails] = useState<any>(null);
  const [loadingDetails, setLoadingDetails] = useState(false);

  // Redirect if not authenticated or wrong connection type
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push(ROUTES.LOGIN);
    }
  }, [isAuthenticated, isLoading, router]);

  // Redirect if not schema_query_only
  useEffect(() => {
    if (!isLoading && connectionStatus && connectionStatus.connection_type !== 'schema_query_only') {
      router.push(ROUTES.DASHBOARD);
    }
  }, [connectionStatus, isLoading, router]);

  // Load schema on mount
  useEffect(() => {
    if (connectionStatus?.connection_type === 'schema_query_only') {
      loadSchema();
    }
  }, [connectionStatus]);

  const loadSchema = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/schema-agent/schema`, {
        headers: {
          'Authorization': `Bearer ${getAccessToken()}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        if (data.schema_metadata) {
          setSchemaMetadata(data.schema_metadata);
        }
      }
    } catch (err) {
      console.error('Failed to load schema:', err);
    }
  };

  const handleDiscoverSchema = async () => {
    setDiscovering(true);
    setError('');
    setSuccess('');

    try {
      const response = await fetch(`${API_BASE_URL}/schema-agent/discover-schema`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${getAccessToken()}`,
          'Content-Type': 'application/json',
        },
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to discover schema');
      }

      setSchemaMetadata(data.schema_metadata);
      setSuccess(`Discovered ${data.table_count} tables successfully!`);
      await refreshConnectionStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to discover schema');
    } finally {
      setDiscovering(false);
    }
  };

  const handleRefreshSchema = async () => {
    setRefreshing(true);
    setError('');
    setSuccess('');

    try {
      const response = await fetch(`${API_BASE_URL}/schema-agent/refresh-schema`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${getAccessToken()}`,
          'Content-Type': 'application/json',
        },
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to refresh schema');
      }

      setSchemaMetadata(data.schema_metadata);
      setSuccess(`Schema refreshed! Found ${data.table_count} tables.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to refresh schema');
    } finally {
      setRefreshing(false);
    }
  };

  const handleViewTable = async (tableName: string) => {
    setSelectedTable(tableName);
    setLoadingDetails(true);
    setTableDetails(null);

    try {
      const response = await fetch(`${API_BASE_URL}/schema-agent/tables/${tableName}`, {
        headers: {
          'Authorization': `Bearer ${getAccessToken()}`,
        },
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to load table details');
      }

      setTableDetails(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load table details');
    } finally {
      setLoadingDetails(false);
    }
  };

  const handleUpgradeToFullIMS = async () => {
    if (!confirm('Are you sure you want to upgrade to Full IMS mode? This will create IMS tables in your database.')) {
      return;
    }

    setUpgrading(true);
    setError('');

    try {
      const response = await fetch(`${API_BASE_URL}/schema-agent/upgrade-to-full-ims`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${getAccessToken()}`,
          'Content-Type': 'application/json',
        },
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to upgrade');
      }

      await refreshConnectionStatus();
      router.push(ROUTES.DB_CONNECT);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to upgrade');
    } finally {
      setUpgrading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600 dark:border-emerald-400"></div>
      </div>
    );
  }

  if (!user || connectionStatus?.connection_type !== 'schema_query_only') {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm dark:shadow-gray-900/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 sm:py-4">
          <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-2 sm:gap-0">
            <div className="flex items-center space-x-2 sm:space-x-3">
              <Link href={ROUTES.DASHBOARD} className="flex items-center space-x-2 sm:space-x-3">
                <div className="w-8 h-8 sm:w-10 sm:h-10 bg-emerald-600 dark:bg-emerald-500 rounded-lg flex items-center justify-center">
                  <span className="text-white text-lg sm:text-xl font-bold">S</span>
                </div>
                <span className="text-lg sm:text-xl font-bold text-gray-900 dark:text-white">{APP_METADATA.NAME}</span>
              </Link>
              <span className="hidden sm:inline text-gray-400 dark:text-gray-500">/</span>
              <span className="hidden sm:inline text-gray-600 dark:text-gray-400">Schema Connect</span>
            </div>
            <div className="flex items-center space-x-3">
              <ThemeToggle />
              <Link
                href={ROUTES.DASHBOARD}
                className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white font-medium text-sm sm:text-base"
              >
                Back to Dashboard
              </Link>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-8">
        {/* Error/Success Messages */}
        {error && (
          <div className="mb-4 sm:mb-6 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 px-3 sm:px-4 py-2 sm:py-3 rounded-lg text-sm">
            {error}
          </div>
        )}
        {success && (
          <div className="mb-4 sm:mb-6 bg-green-50 dark:bg-green-900/30 border border-green-200 dark:border-green-800 text-green-700 dark:text-green-400 px-3 sm:px-4 py-2 sm:py-3 rounded-lg text-sm">
            {success}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-8">
          {/* Left Column - Connection Status & Actions */}
          <div className="lg:col-span-1 space-y-4 sm:space-y-6">
            {/* Connection Status Card */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md dark:shadow-gray-900/50 p-4 sm:p-6">
              <h2 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white mb-3 sm:mb-4">Connection Status</h2>

              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Mode</span>
                  <span className="bg-emerald-100 dark:bg-emerald-900/50 text-emerald-800 dark:text-emerald-300 px-3 py-1 rounded-full text-sm font-medium">
                    Agent + Analytics
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Schema Status</span>
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                    schemaMetadata
                      ? 'bg-green-100 dark:bg-green-900/50 text-green-800 dark:text-green-300'
                      : 'bg-yellow-100 dark:bg-yellow-900/50 text-yellow-800 dark:text-yellow-300'
                  }`}>
                    {schemaMetadata ? 'Ready' : 'Not Discovered'}
                  </span>
                </div>

                {schemaMetadata && (
                  <>
                    <div className="flex items-center justify-between">
                      <span className="text-gray-600 dark:text-gray-400">Tables</span>
                      <span className="text-gray-900 dark:text-white font-medium">{schemaMetadata.table_count}</span>
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">
                      Last updated: {new Date(schemaMetadata.discovered_at).toLocaleString()}
                    </div>
                  </>
                )}
              </div>
            </div>

            {/* Actions Card */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md dark:shadow-gray-900/50 p-4 sm:p-6">
              <h2 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white mb-3 sm:mb-4">Actions</h2>

              <div className="space-y-3">
                {!schemaMetadata ? (
                  <button
                    onClick={handleDiscoverSchema}
                    disabled={discovering}
                    className="w-full bg-emerald-600 text-white py-3 px-4 rounded-lg hover:bg-emerald-700 disabled:bg-emerald-400 transition-colors font-semibold flex items-center justify-center space-x-2"
                  >
                    {discovering ? (
                      <>
                        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                        <span>Discovering...</span>
                      </>
                    ) : (
                      <>
                        <span>Discover Schema</span>
                      </>
                    )}
                  </button>
                ) : (
                  <>
                    <button
                      onClick={handleRefreshSchema}
                      disabled={refreshing}
                      className="w-full bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 py-3 px-4 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 disabled:bg-gray-100 dark:disabled:bg-gray-700 transition-colors font-medium flex items-center justify-center space-x-2"
                    >
                      {refreshing ? (
                        <>
                          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-gray-600 dark:border-gray-400"></div>
                          <span>Refreshing...</span>
                        </>
                      ) : (
                        <span>Refresh Schema</span>
                      )}
                    </button>

                    <Link
                      href={ROUTES.SCHEMA_AGENT}
                      className="w-full bg-emerald-600 text-white py-3 px-4 rounded-lg hover:bg-emerald-700 transition-colors font-semibold flex items-center justify-center"
                    >
                      Open AI Agent
                    </Link>
                  </>
                )}

                <hr className="my-4 border-gray-200 dark:border-gray-700" />

                <button
                  onClick={handleUpgradeToFullIMS}
                  disabled={upgrading}
                  className="w-full bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300 py-3 px-4 rounded-lg hover:bg-blue-200 dark:hover:bg-blue-900/70 disabled:bg-blue-100 dark:disabled:bg-blue-900/50 transition-colors font-medium flex items-center justify-center space-x-2"
                >
                  {upgrading ? (
                    <>
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600 dark:border-blue-400"></div>
                      <span>Upgrading...</span>
                    </>
                  ) : (
                    <span>Upgrade to Full IMS</span>
                  )}
                </button>
                <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
                  This will create IMS tables in your database
                </p>
              </div>
            </div>

            {/* Read-Only Notice */}
            <div className="bg-emerald-50 dark:bg-emerald-900/30 border border-emerald-200 dark:border-emerald-800 rounded-lg p-4">
              <div className="flex items-start space-x-3">
                <span className="text-emerald-600 dark:text-emerald-400 text-xl">🛡️</span>
                <div>
                  <h4 className="font-semibold text-emerald-800 dark:text-emerald-300">Read-Only Mode</h4>
                  <p className="text-sm text-emerald-700 dark:text-emerald-400">
                    Only SELECT queries are allowed. Your data is safe from modifications.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column - Tables List & Details */}
          <div className="lg:col-span-2 space-y-4 sm:space-y-6">
            {!schemaMetadata ? (
              <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md dark:shadow-gray-900/50 p-8 sm:p-12 text-center">
                <div className="text-5xl sm:text-6xl mb-3 sm:mb-4">🔍</div>
                <h2 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-white mb-2">
                  Discover Your Schema
                </h2>
                <p className="text-gray-600 dark:text-gray-400 mb-4 sm:mb-6 text-sm sm:text-base">
                  Click &quot;Discover Schema&quot; to analyze your database and enable AI-powered queries.
                </p>
              </div>
            ) : (
              <>
                {/* Tables List */}
                <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md dark:shadow-gray-900/50 p-4 sm:p-6">
                  <h2 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white mb-3 sm:mb-4">
                    Tables ({schemaMetadata.table_count})
                  </h2>

                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 sm:gap-3">
                    {schemaMetadata.tables.map((table) => (
                      <button
                        key={table.name}
                        onClick={() => handleViewTable(table.name)}
                        className={`text-left p-3 rounded-lg border-2 transition-all ${
                          selectedTable === table.name
                            ? 'border-emerald-500 bg-emerald-50 dark:bg-emerald-900/30'
                            : 'border-gray-200 dark:border-gray-600 hover:border-emerald-300 dark:hover:border-emerald-700'
                        }`}
                      >
                        <div className="font-medium text-gray-900 dark:text-white">{table.name}</div>
                        <div className="text-xs text-gray-500 dark:text-gray-400">
                          {table.column_count} columns • {table.type}
                        </div>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Table Details */}
                {selectedTable && (
                  <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md dark:shadow-gray-900/50 p-4 sm:p-6">
                    <h2 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white mb-3 sm:mb-4">
                      Table: {selectedTable}
                    </h2>

                    {loadingDetails ? (
                      <div className="flex items-center justify-center py-8">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600 dark:border-emerald-400"></div>
                      </div>
                    ) : tableDetails ? (
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="bg-gray-50 dark:bg-gray-700">
                              <th className="text-left px-4 py-2 font-medium text-gray-700 dark:text-gray-300">Column</th>
                              <th className="text-left px-4 py-2 font-medium text-gray-700 dark:text-gray-300">Type</th>
                              <th className="text-left px-4 py-2 font-medium text-gray-700 dark:text-gray-300">Nullable</th>
                              <th className="text-left px-4 py-2 font-medium text-gray-700 dark:text-gray-300">Key</th>
                            </tr>
                          </thead>
                          <tbody>
                            {tableDetails.columns?.map((col: ColumnInfo, idx: number) => (
                              <tr key={col.name} className={idx % 2 === 0 ? 'bg-white dark:bg-gray-800' : 'bg-gray-50 dark:bg-gray-700/50'}>
                                <td className="px-4 py-2 font-mono text-gray-900 dark:text-white">{col.name}</td>
                                <td className="px-4 py-2 text-gray-600 dark:text-gray-400">{col.type}</td>
                                <td className="px-4 py-2">
                                  {col.nullable ? (
                                    <span className="text-gray-400 dark:text-gray-500">yes</span>
                                  ) : (
                                    <span className="text-red-600 dark:text-red-400 font-medium">NOT NULL</span>
                                  )}
                                </td>
                                <td className="px-4 py-2">
                                  {col.primary_key && (
                                    <span className="bg-yellow-100 dark:bg-yellow-900/50 text-yellow-800 dark:text-yellow-300 px-2 py-0.5 rounded text-xs font-medium">
                                      PK
                                    </span>
                                  )}
                                  {col.foreign_key && (
                                    <span className="bg-blue-100 dark:bg-blue-900/50 text-blue-800 dark:text-blue-300 px-2 py-0.5 rounded text-xs font-medium ml-1" title={col.foreign_key}>
                                      FK
                                    </span>
                                  )}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>

                        {tableDetails.estimated_rows !== undefined && (
                          <div className="mt-4 text-sm text-gray-500 dark:text-gray-400">
                            Estimated rows: ~{tableDetails.estimated_rows.toLocaleString()}
                          </div>
                        )}
                      </div>
                    ) : (
                      <p className="text-gray-500 dark:text-gray-400">Select a table to view its structure</p>
                    )}
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
