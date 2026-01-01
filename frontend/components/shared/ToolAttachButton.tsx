/**
 * ToolAttachButton Component
 *
 * Attach button for selecting tools in chat.
 * Shows dropdown with system tools and user connectors.
 * Selected tool will be prefixed to the message as [TOOL:NAME].
 */

'use client';

import { useState, useEffect, useRef } from 'react';
import { Paperclip, Check, X, Server, Mail, BarChart3, Download, Loader2 } from 'lucide-react';
import { getAllTools, SystemTool } from '@/lib/tools-api';
import { getConnectors, Connector } from '@/lib/connectors-api';

interface ToolAttachButtonProps {
  onToolSelect?: (toolPrefix: string | null, toolName: string | null) => void;
  selectedTool?: string | null;
}

const iconMap: Record<string, React.ReactNode> = {
  mail: <Mail className="h-4 w-4" />,
  chart: <BarChart3 className="h-4 w-4" />,
  download: <Download className="h-4 w-4" />,
};


export default function ToolAttachButton({ onToolSelect, selectedTool }: ToolAttachButtonProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [systemTools, setSystemTools] = useState<SystemTool[]>([]);
  const [connectors, setConnectors] = useState<Connector[]>([]);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Load tools and connectors
  useEffect(() => {
    async function loadData() {
      if (!isOpen) return;

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
    }
    loadData();
  }, [isOpen]);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  function handleSelectSystemTool(tool: SystemTool) {
    const prefix = `[TOOL:${tool.id.toUpperCase()}]`;
    onToolSelect?.(prefix, tool.name);
    setIsOpen(false);
  }

  function handleSelectConnectorTool(connector: Connector, toolName?: string) {
    const prefix = toolName
      ? `[TOOL:${connector.name.toUpperCase().replace(' ', '_')}]`
      : `[TOOL:${connector.name.toUpperCase().replace(' ', '_')}]`;
    onToolSelect?.(prefix, toolName || connector.name);
    setIsOpen(false);
  }

  function handleClearSelection() {
    onToolSelect?.(null, null);
    setIsOpen(false);
  }

  const hasSelection = !!selectedTool;

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Attach Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`
          flex items-center justify-center w-9 h-9 rounded-lg transition-colors
          ${hasSelection
            ? 'bg-blue-100 text-blue-600 hover:bg-blue-200'
            : 'text-gray-500 hover:bg-gray-100'
          }
        `}
        title={hasSelection ? `Selected: ${selectedTool}` : 'Attach tool'}
      >
        <Paperclip className="h-5 w-5" />
        {hasSelection && (
          <span className="absolute -top-1 -right-1 w-3 h-3 bg-blue-600 rounded-full" />
        )}
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute bottom-12 left-0 w-72 bg-white rounded-lg shadow-xl border border-gray-200 z-50 max-h-80 overflow-auto">
          {/* Header */}
          <div className="px-3 py-2 border-b border-gray-100 bg-gray-50 rounded-t-lg">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-700">Select Tool</span>
              {hasSelection && (
                <button
                  onClick={handleClearSelection}
                  className="flex items-center text-xs text-red-600 hover:text-red-700"
                >
                  <X className="h-3 w-3 mr-1" />
                  Clear
                </button>
              )}
            </div>
            {hasSelection && (
              <p className="text-xs text-blue-600 mt-1">Selected: {selectedTool}</p>
            )}
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-5 w-5 animate-spin text-gray-400" />
            </div>
          ) : (
            <>
              {/* System Tools */}
              <div className="p-2">
                <p className="px-2 py-1 text-xs font-medium text-gray-500 uppercase">System Tools</p>
                {systemTools.length > 0 ? (
                  systemTools.map(tool => (
                    <button
                      key={tool.id}
                      onClick={() => handleSelectSystemTool(tool)}
                      className={`
                        flex items-center w-full px-2 py-2 rounded hover:bg-gray-50 text-left
                        ${selectedTool === tool.name ? 'bg-blue-50' : ''}
                      `}
                    >
                      <div className={`
                        w-7 h-7 rounded flex items-center justify-center mr-2
                        ${tool.is_connected ? 'bg-green-100 text-green-600' : 'bg-gray-100 text-gray-500'}
                      `}>
                        {iconMap[tool.icon] || <Mail className="h-4 w-4" />}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-700">{tool.name}</p>
                        <p className="text-xs text-gray-500 truncate">{tool.description}</p>
                      </div>
                      {selectedTool === tool.name && (
                        <Check className="h-4 w-4 text-blue-600 ml-2" />
                      )}
                    </button>
                  ))
                ) : (
                  <p className="px-2 py-3 text-sm text-gray-500 text-center">
                    No system tools available
                  </p>
                )}
              </div>

              {/* User Connectors */}
              {connectors.length > 0 && (
                <div className="p-2 border-t border-gray-100">
                  <p className="px-2 py-1 text-xs font-medium text-gray-500 uppercase">My Connectors</p>
                  {connectors.map(connector => (
                    <div key={connector.id} className="mb-1">
                      <button
                        onClick={() => handleSelectConnectorTool(connector)}
                        className={`
                          flex items-center w-full px-2 py-2 rounded hover:bg-gray-50 text-left
                          ${selectedTool === connector.name ? 'bg-blue-50' : ''}
                        `}
                      >
                        <div className="w-7 h-7 rounded bg-purple-100 text-purple-600 flex items-center justify-center mr-2">
                          <Server className="h-4 w-4" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-700">Use {connector.name}</p>
                          <p className="text-xs text-gray-500">
                            {connector.tool_count} tool{connector.tool_count !== 1 ? 's' : ''}
                          </p>
                        </div>
                        {selectedTool === connector.name && (
                          <Check className="h-4 w-4 text-blue-600 ml-2" />
                        )}
                      </button>
                      {/* Individual tools from connector */}
                      {connector.discovered_tools && connector.discovered_tools.length > 0 && (
                        <div className="ml-9 mt-1 space-y-1">
                          {connector.discovered_tools.slice(0, 5).map(tool => (
                            <button
                              key={tool.name}
                              onClick={() => handleSelectConnectorTool(connector, tool.name)}
                              className="flex items-center w-full px-2 py-1 text-xs text-gray-600 hover:bg-gray-50 rounded"
                            >
                              <span className="w-1.5 h-1.5 bg-gray-400 rounded-full mr-2" />
                              {tool.name}
                            </button>
                          ))}
                          {connector.discovered_tools.length > 5 && (
                            <p className="px-2 py-1 text-xs text-gray-400">
                              +{connector.discovered_tools.length - 5} more
                            </p>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* Empty State */}
              {systemTools.length === 0 && connectors.length === 0 && (
                <div className="px-4 py-6 text-center">
                  <p className="text-sm text-gray-500">No tools available</p>
                  <p className="text-xs text-gray-400 mt-1">
                    Connect tools in Settings
                  </p>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
