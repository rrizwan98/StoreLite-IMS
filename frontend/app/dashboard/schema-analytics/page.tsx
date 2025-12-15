/**
 * Schema Analytics Page
 *
 * Analytics dashboard for schema_query_only users.
 * Provides visualizations based on AI agent queries.
 */

'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { ROUTES, API_BASE_URL, APP_METADATA } from '@/lib/constants';
import { useAuth } from '@/lib/auth-context';
import { getAccessToken } from '@/lib/auth-api';

interface QueryResult {
  query: string;
  response: string;
  timestamp: Date;
}

export default function SchemaAnalyticsPage() {
  const { user, connectionStatus, isLoading, isAuthenticated } = useAuth();
  const router = useRouter();

  const [quickQuery, setQuickQuery] = useState('');
  const [queryResult, setQueryResult] = useState<QueryResult | null>(null);
  const [querying, setQuerying] = useState(false);
  const [error, setError] = useState('');

  // Redirect if not authenticated or wrong connection type
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push(ROUTES.LOGIN);
    }
  }, [isAuthenticated, isLoading, router]);

  // Redirect if not schema_query_only
  useEffect(() => {
    if (!isLoading && connectionStatus) {
      if (connectionStatus.connection_type !== 'schema_query_only') {
        router.push(ROUTES.DASHBOARD);
      } else if (connectionStatus.schema_status !== 'ready') {
        router.push(ROUTES.SCHEMA_CONNECT);
      }
    }
  }, [connectionStatus, isLoading, router]);

  const runQuickQuery = async (question: string) => {
    setQuerying(true);
    setError('');
    setQuickQuery(question);

    try {
      const response = await fetch(`${API_BASE_URL}/schema-agent/chat`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${getAccessToken()}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: question }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Query failed');
      }

      setQueryResult({
        query: question,
        response: data.response,
        timestamp: new Date(),
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Query failed');
    } finally {
      setQuerying(false);
    }
  };

  const analyticsQueries = [
    {
      title: 'Table Overview',
      description: 'Get a summary of all tables and their sizes',
      query: 'Give me an overview of all tables with their row counts and sizes',
      icon: '📋',
    },
    {
      title: 'Data Distribution',
      description: 'Analyze how data is distributed across tables',
      query: 'Analyze the data distribution across my largest tables',
      icon: '📊',
    },
    {
      title: 'Recent Activity',
      description: 'Find tables with recent modifications',
      query: 'Which tables have timestamp columns and show recent records?',
      icon: '🕐',
    },
    {
      title: 'Relationship Map',
      description: 'Understand table relationships',
      query: 'Describe all foreign key relationships between tables',
      icon: '🔗',
    },
    {
      title: 'Numeric Summary',
      description: 'Get statistics on numeric columns',
      query: 'Find numeric columns and give me min, max, and average values',
      icon: '🔢',
    },
    {
      title: 'Data Quality',
      description: 'Check for null values and data quality',
      query: 'Which columns have the most null values? Show percentages',
      icon: '✅',
    },
  ];

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600"></div>
      </div>
    );
  }

  if (!user || connectionStatus?.connection_type !== 'schema_query_only') {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-3">
            <Link href={ROUTES.DASHBOARD} className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-emerald-600 rounded-lg flex items-center justify-center">
                <span className="text-white text-xl">📊</span>
              </div>
              <span className="text-xl font-bold text-gray-900">Analytics</span>
            </Link>
            <span className="text-gray-400">|</span>
            <span className="text-gray-600 text-sm">AI-powered data insights</span>
          </div>
          <div className="flex items-center space-x-4">
            <Link
              href={ROUTES.SCHEMA_AGENT}
              className="text-gray-600 hover:text-gray-900 text-sm"
            >
              Open Agent
            </Link>
            <Link
              href={ROUTES.DASHBOARD}
              className="text-gray-600 hover:text-gray-900 font-medium"
            >
              Dashboard
            </Link>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Quick Analytics Cards */}
        <div className="mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Analytics</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {analyticsQueries.map((item, idx) => (
              <button
                key={idx}
                onClick={() => runQuickQuery(item.query)}
                disabled={querying}
                className="bg-white rounded-xl shadow-md p-6 text-left hover:shadow-lg transition-shadow disabled:opacity-50"
              >
                <div className="text-3xl mb-3">{item.icon}</div>
                <h3 className="font-semibold text-gray-900 mb-1">{item.title}</h3>
                <p className="text-sm text-gray-600">{item.description}</p>
              </button>
            ))}
          </div>
        </div>

        {/* Query Result */}
        {(querying || queryResult) && (
          <div className="bg-white rounded-xl shadow-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">
                {querying ? 'Analyzing...' : 'Analysis Result'}
              </h2>
              {queryResult && (
                <span className="text-sm text-gray-500">
                  {queryResult.timestamp.toLocaleTimeString()}
                </span>
              )}
            </div>

            {querying ? (
              <div className="flex items-center justify-center py-12">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-emerald-600 mx-auto mb-4"></div>
                  <p className="text-gray-600">Running: {quickQuery}</p>
                </div>
              </div>
            ) : queryResult ? (
              <div>
                <div className="bg-gray-50 rounded-lg p-3 mb-4">
                  <p className="text-sm text-gray-600">
                    <span className="font-medium">Query:</span> {queryResult.query}
                  </p>
                </div>
                <div className="prose prose-sm max-w-none">
                  <pre className="whitespace-pre-wrap bg-gray-50 p-4 rounded-lg text-sm text-gray-800 overflow-x-auto">
                    {queryResult.response}
                  </pre>
                </div>
              </div>
            ) : null}

            {error && (
              <div className="text-red-600 bg-red-50 px-4 py-3 rounded-lg">
                {error}
              </div>
            )}
          </div>
        )}

        {/* Custom Query */}
        <div className="mt-8 bg-white rounded-xl shadow-md p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Custom Analysis</h2>
          <p className="text-gray-600 mb-4">
            Need a specific analysis? Ask in natural language or use the AI Agent for more complex queries.
          </p>
          <Link
            href={ROUTES.SCHEMA_AGENT}
            className="inline-flex items-center px-6 py-3 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors font-semibold"
          >
            <span className="mr-2">🧠</span>
            Open AI Agent
          </Link>
        </div>

        {/* Read-Only Notice */}
        <div className="mt-8 bg-emerald-50 border border-emerald-200 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <span className="text-emerald-600 text-xl">🛡️</span>
            <div>
              <h4 className="font-semibold text-emerald-800">Read-Only Analytics</h4>
              <p className="text-sm text-emerald-700">
                All analytics queries are read-only. Your data is never modified.
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
