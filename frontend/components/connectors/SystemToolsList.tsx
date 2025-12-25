/**
 * SystemToolsList Component
 *
 * Displays list of system tools (Gmail, Analytics, Export) with connection status.
 * Used in the Apps/Tools settings page.
 *
 * Gmail uses OAuth popup flow, other tools use simple API connect.
 */

'use client';

import { useState, useEffect } from 'react';
import { Mail, BarChart3, Download, Check, X, Loader2, AlertCircle, Link, Unlink } from 'lucide-react';
import { SystemTool, getAllTools, connectTool, disconnectTool } from '@/lib/tools-api';
import { connectGmailWithPopup, disconnectGmail, getGmailStatus } from '@/lib/gmail-api';

interface SystemToolsListProps {
  onToolClick?: (tool: SystemTool) => void;
  showBeta?: boolean;
}

const iconMap: Record<string, React.ReactNode> = {
  mail: <Mail className="h-5 w-5" />,
  chart: <BarChart3 className="h-5 w-5" />,
  download: <Download className="h-5 w-5" />,
};

const categoryLabels: Record<string, string> = {
  communication: 'Communication',
  insights: 'Insights & Analytics',
  utilities: 'Utilities',
};

export default function SystemToolsList({ onToolClick, showBeta = true }: SystemToolsListProps) {
  const [tools, setTools] = useState<SystemTool[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [gmailEmail, setGmailEmail] = useState<string | null>(null);

  useEffect(() => {
    loadTools();
  }, []);

  async function loadTools() {
    try {
      setLoading(true);
      setError(null);

      // Load tools and Gmail status in parallel
      const [data, gmailStatus] = await Promise.all([
        getAllTools(),
        getGmailStatus().catch(() => ({ connected: false, email: null })),
      ]);

      // Filter beta tools if showBeta is false
      let filteredTools = showBeta ? data : data.filter(t => !t.is_beta);

      // Sync Gmail connection status from Gmail API
      filteredTools = filteredTools.map(t =>
        t.id === 'gmail'
          ? { ...t, is_connected: gmailStatus.connected }
          : t
      );

      setTools(filteredTools);
      setGmailEmail(gmailStatus.email || null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load tools');
    } finally {
      setLoading(false);
    }
  }

  async function handleConnect(tool: SystemTool) {
    try {
      setActionLoading(tool.id);
      setError(null);

      // Gmail requires OAuth popup flow
      if (tool.id === 'gmail') {
        const success = await connectGmailWithPopup();
        if (success) {
          // Refresh Gmail status
          const gmailStatus = await getGmailStatus();
          setTools(prev => prev.map(t =>
            t.id === 'gmail'
              ? { ...t, is_connected: gmailStatus.connected }
              : t
          ));
          setGmailEmail(gmailStatus.email || null);
        }
      } else {
        // Other tools use simple API connect
        const updatedTool = await connectTool(tool.id);
        setTools(prev => prev.map(t => t.id === tool.id ? updatedTool : t));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to connect');
    } finally {
      setActionLoading(null);
    }
  }

  async function handleDisconnect(tool: SystemTool) {
    try {
      setActionLoading(tool.id);
      setError(null);

      // Gmail requires special disconnect
      if (tool.id === 'gmail') {
        await disconnectGmail();
        setTools(prev => prev.map(t =>
          t.id === 'gmail'
            ? { ...t, is_connected: false }
            : t
        ));
        setGmailEmail(null);
      } else {
        // Other tools use simple API disconnect
        const updatedTool = await disconnectTool(tool.id);
        setTools(prev => prev.map(t => t.id === tool.id ? updatedTool : t));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to disconnect');
    } finally {
      setActionLoading(null);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
        <span className="ml-2 text-gray-500">Loading tools...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center p-8 text-red-500">
        <AlertCircle className="h-5 w-5 mr-2" />
        <span>{error}</span>
        <button
          onClick={loadTools}
          className="ml-4 text-sm underline hover:no-underline"
        >
          Retry
        </button>
      </div>
    );
  }

  // Group tools by category
  const groupedTools = tools.reduce((acc, tool) => {
    const category = tool.category;
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(tool);
    return acc;
  }, {} as Record<string, SystemTool[]>);

  return (
    <div className="space-y-6">
      {Object.entries(groupedTools).map(([category, categoryTools]) => (
        <div key={category}>
          <h3 className="text-sm font-medium text-gray-500 mb-3">
            {categoryLabels[category] || category}
          </h3>
          <div className="space-y-2">
            {categoryTools.map((tool) => (
              <ToolCard
                key={tool.id}
                tool={tool}
                onClick={() => onToolClick?.(tool)}
                onConnect={handleConnect}
                onDisconnect={handleDisconnect}
                loading={actionLoading === tool.id}
                connectedEmail={tool.id === 'gmail' ? gmailEmail : null}
              />
            ))}
          </div>
        </div>
      ))}

      {tools.length === 0 && (
        <div className="text-center text-gray-500 py-8">
          No system tools available
        </div>
      )}
    </div>
  );
}

interface ToolCardProps {
  tool: SystemTool;
  onClick?: () => void;
  onConnect?: (tool: SystemTool) => void;
  onDisconnect?: (tool: SystemTool) => void;
  loading?: boolean;
  connectedEmail?: string | null; // For Gmail - show connected email
}

function ToolCard({ tool, onClick, onConnect, onDisconnect, loading, connectedEmail }: ToolCardProps) {
  const isClickable = tool.is_enabled && !tool.is_beta && onClick;
  const canConnect = tool.is_enabled && !tool.is_beta && !tool.is_connected;
  const canDisconnect = tool.is_connected;

  return (
    <div
      className={`
        flex items-center p-4 rounded-lg border transition-colors
        ${tool.is_enabled && !tool.is_beta
          ? 'bg-white border-gray-200 hover:border-blue-300'
          : 'bg-gray-50 border-gray-200 opacity-60'
        }
      `}
    >
      {/* Icon */}
      <div
        className={`
          flex items-center justify-center w-10 h-10 rounded-lg mr-4
          ${tool.is_connected ? 'bg-green-100 text-green-600' : 'bg-gray-100 text-gray-500'}
          ${isClickable ? 'cursor-pointer' : ''}
        `}
        onClick={isClickable ? onClick : undefined}
      >
        {iconMap[tool.icon] || <div className="w-5 h-5 bg-gray-300 rounded" />}
      </div>

      {/* Info */}
      <div
        className="flex-1 min-w-0"
        onClick={isClickable ? onClick : undefined}
        style={{ cursor: isClickable ? 'pointer' : 'default' }}
      >
        <div className="flex items-center">
          <h4 className="font-medium text-gray-900">{tool.name}</h4>
          {tool.is_beta && (
            <span className="ml-2 px-2 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-800 rounded">
              Coming Soon
            </span>
          )}
        </div>
        <p className="text-sm text-gray-500 truncate">{tool.description}</p>
      </div>

      {/* Status & Actions */}
      <div className="flex items-center ml-4 space-x-3">
        {/* Status indicator */}
        {tool.is_beta ? (
          <span className="text-sm text-gray-400">Beta</span>
        ) : tool.is_connected ? (
          <div className="flex flex-col items-end">
            <div className="flex items-center text-green-600">
              <Check className="h-4 w-4 mr-1" />
              <span className="text-sm">Connected</span>
            </div>
            {/* Show connected email for Gmail */}
            {tool.id === 'gmail' && connectedEmail && (
              <span className="text-xs text-gray-500 mt-0.5">{connectedEmail}</span>
            )}
          </div>
        ) : tool.auth_type === 'none' ? (
          <div className="flex items-center text-blue-600">
            <span className="text-sm">Ready</span>
          </div>
        ) : (
          <div className="flex items-center text-gray-400">
            <X className="h-4 w-4 mr-1" />
            <span className="text-sm">Not connected</span>
          </div>
        )}

        {/* Connect/Disconnect Button */}
        {!tool.is_beta && tool.is_enabled && (
          <>
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin text-gray-400" />
            ) : canDisconnect ? (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDisconnect?.(tool);
                }}
                className="flex items-center px-3 py-1.5 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                title="Disconnect"
              >
                <Unlink className="h-4 w-4 mr-1" />
                Disconnect
              </button>
            ) : canConnect ? (
              // Gmail needs Google Sign-in button, others use simple Connect
              tool.id === 'gmail' ? (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onConnect?.(tool);
                  }}
                  className="flex items-center px-4 py-2 text-sm font-medium text-white bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors shadow-sm"
                  title="Sign in with Google"
                >
                  {/* Google Logo */}
                  <svg className="w-4 h-4 mr-2" viewBox="0 0 24 24">
                    <path
                      fill="#4285F4"
                      d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                    />
                    <path
                      fill="#34A853"
                      d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                    />
                    <path
                      fill="#FBBC05"
                      d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                    />
                    <path
                      fill="#EA4335"
                      d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                    />
                  </svg>
                  <span className="text-gray-700">Sign in with Google</span>
                </button>
              ) : (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onConnect?.(tool);
                  }}
                  className="flex items-center px-3 py-1.5 text-sm text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                  title="Connect"
                >
                  <Link className="h-4 w-4 mr-1" />
                  Connect
                </button>
              )
            ) : null}
          </>
        )}
      </div>
    </div>
  );
}
