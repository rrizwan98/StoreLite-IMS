/**
 * Connect Tools Section Component
 *
 * Dashboard section showing connected tools summary.
 * Links to Settings page for managing all tools.
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { Settings, Check, Mail, BarChart3, Download, Server, ChevronRight } from 'lucide-react';
import { getAllTools, SystemTool } from '@/lib/tools-api';
import { getConnectors, Connector } from '@/lib/connectors-api';

interface ConnectToolsSectionProps {
  className?: string;
}

const iconMap: Record<string, React.ReactNode> = {
  mail: <Mail className="h-5 w-5" />,
  chart: <BarChart3 className="h-5 w-5" />,
  download: <Download className="h-5 w-5" />,
};

export default function ConnectToolsSection({ className = '' }: ConnectToolsSectionProps) {
  const [systemTools, setSystemTools] = useState<SystemTool[]>([]);
  const [connectors, setConnectors] = useState<Connector[]>([]);
  const [loading, setLoading] = useState(true);

  // Load tools and connectors
  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [tools, conns] = await Promise.all([
        getAllTools().catch(() => []),
        getConnectors(true).catch(() => []),
      ]);

      // Only show connected/available system tools
      setSystemTools(tools.filter(t => (t.is_connected || t.auth_type === 'none') && t.is_enabled && !t.is_beta));
      // Only show verified connectors
      setConnectors(conns.filter(c => c.is_verified && c.is_active));
    } catch (err) {
      console.error('Failed to load tools:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const connectedSystemTools = systemTools.filter(t => t.is_connected);
  const totalConnected = connectedSystemTools.length + connectors.length;

  return (
    <div className={`bg-white rounded-xl shadow-md p-6 ${className}`}>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-gray-900">Connected Tools</h2>
          <p className="text-sm text-gray-600">
            {totalConnected > 0
              ? `${totalConnected} tool${totalConnected !== 1 ? 's' : ''} connected to AI Agent`
              : 'Connect tools to extend AI Agent capabilities'}
          </p>
        </div>
        <Link
          href="/dashboard/settings"
          className="flex items-center px-4 py-2 text-sm font-medium text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 transition-colors"
        >
          <Settings className="w-4 h-4 mr-2" />
          Manage All Tools
        </Link>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"></div>
        </div>
      ) : totalConnected === 0 ? (
        /* Empty State */
        <div className="text-center py-8 border-2 border-dashed border-gray-200 rounded-lg">
          <div className="text-gray-400 text-4xl mb-3">🔌</div>
          <p className="text-gray-600 font-medium mb-2">No tools connected yet</p>
          <p className="text-sm text-gray-500 mb-4">
            Connect Gmail, Analytics, or custom MCP servers to enhance your AI Agent
          </p>
          <Link
            href="/dashboard/settings"
            className="inline-flex items-center px-4 py-2 text-sm font-medium text-emerald-600 bg-emerald-50 rounded-lg hover:bg-emerald-100 transition-colors"
          >
            Connect Your First Tool
            <ChevronRight className="w-4 h-4 ml-1" />
          </Link>
        </div>
      ) : (
        /* Connected Tools Grid */
        <div className="space-y-4">
          {/* System Tools */}
          {connectedSystemTools.length > 0 && (
            <div>
              <p className="text-xs font-medium text-gray-500 uppercase mb-2">System Tools</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {connectedSystemTools.map((tool) => (
                  <div
                    key={tool.id}
                    className="flex items-center p-3 bg-gray-50 rounded-lg border border-gray-100"
                  >
                    <div className="w-10 h-10 rounded-lg bg-green-100 text-green-600 flex items-center justify-center mr-3">
                      {iconMap[tool.icon] || <Mail className="h-5 w-5" />}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-gray-900">{tool.name}</p>
                      <p className="text-xs text-green-600 flex items-center">
                        <Check className="w-3 h-3 mr-1" />
                        Connected
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* MCP Connectors */}
          {connectors.length > 0 && (
            <div>
              <p className="text-xs font-medium text-gray-500 uppercase mb-2">MCP Connectors</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {connectors.map((connector) => (
                  <div
                    key={connector.id}
                    className="flex items-center p-3 bg-gray-50 rounded-lg border border-gray-100"
                  >
                    <div className="w-10 h-10 rounded-lg bg-purple-100 text-purple-600 flex items-center justify-center mr-3">
                      <Server className="h-5 w-5" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-gray-900">{connector.name}</p>
                      <p className="text-xs text-purple-600">
                        {connector.tool_count} tool{connector.tool_count !== 1 ? 's' : ''}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Usage hint */}
          <div className="mt-4 p-4 bg-blue-50 rounded-lg">
            <div className="flex items-start space-x-3">
              <span className="text-blue-500 text-lg">💡</span>
              <div className="text-sm text-blue-800">
                <p className="font-medium mb-1">How to use tools:</p>
                <p>
                  In AI Agent chat, click the <strong>+</strong> button or type <strong>/</strong> to select a tool.
                  Then ask your question in natural language.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
