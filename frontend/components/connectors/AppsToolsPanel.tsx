/**
 * AppsToolsPanel Component
 *
 * Combined panel showing both system tools and predefined OAuth connectors.
 * No "Add Connector" button - users click on predefined connectors (like Notion) to connect via OAuth.
 */

'use client';

import { useState } from 'react';
import { Wrench, Plug } from 'lucide-react';
import SystemToolsList from './SystemToolsList';
import ConnectorsList from './ConnectorsList';
import { SystemTool } from '@/lib/tools-api';
import { Connector } from '@/lib/connectors-api';
import { PredefinedConnector } from '@/lib/predefined-connectors';

type TabType = 'system' | 'connectors';

interface AppsToolsPanelProps {
  defaultTab?: TabType;
  onSystemToolClick?: (tool: SystemTool) => void;
  onPredefinedConnectorClick?: (connector: PredefinedConnector) => void;
  onConnectedConnectorClick?: (connector: Connector) => void;
}

export default function AppsToolsPanel({
  defaultTab = 'system',
  onSystemToolClick,
  onPredefinedConnectorClick,
  onConnectedConnectorClick,
}: AppsToolsPanelProps) {
  const [activeTab, setActiveTab] = useState<TabType>(defaultTab);

  return (
    <div className="h-full flex flex-col">
      {/* Tabs */}
      <div className="flex border-b border-gray-200">
        <button
          onClick={() => setActiveTab('system')}
          className={`
            flex items-center px-4 py-3 text-sm font-medium border-b-2 transition-colors
            ${activeTab === 'system'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
            }
          `}
        >
          <Wrench className="h-4 w-4 mr-2" />
          System Tools
        </button>
        <button
          onClick={() => setActiveTab('connectors')}
          className={`
            flex items-center px-4 py-3 text-sm font-medium border-b-2 transition-colors
            ${activeTab === 'connectors'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
            }
          `}
        >
          <Plug className="h-4 w-4 mr-2" />
          Connectors
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-4">
        {activeTab === 'system' ? (
          <SystemToolsList onToolClick={onSystemToolClick} />
        ) : (
          <ConnectorsList
            onConnectorClick={onPredefinedConnectorClick}
            onConnectedConnectorClick={onConnectedConnectorClick}
          />
        )}
      </div>
    </div>
  );
}
