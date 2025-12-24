/**
 * PredefinedConnectorsList Component
 *
 * Shows available predefined connectors (like Notion) that can be connected via OAuth.
 */

'use client';

import Image from 'next/image';
import { Check, ChevronRight } from 'lucide-react';
import { PREDEFINED_CONNECTORS, PredefinedConnector } from '@/lib/predefined-connectors';

interface PredefinedConnectorsListProps {
  connectedIds: string[];
  onConnectorClick: (connector: PredefinedConnector) => void;
}

export default function PredefinedConnectorsList({
  connectedIds,
  onConnectorClick,
}: PredefinedConnectorsListProps) {
  return (
    <div className="space-y-2">
      <h3 className="text-sm font-medium text-gray-500 mb-3">
        Available Connectors
      </h3>

      {PREDEFINED_CONNECTORS.map((connector) => {
        const isConnected = connectedIds.includes(connector.id);

        return (
          <button
            key={connector.id}
            onClick={() => onConnectorClick(connector)}
            disabled={!connector.isAvailable}
            className={`
              w-full flex items-center p-4 rounded-xl border transition-all
              ${isConnected
                ? 'bg-green-50 border-green-200 hover:border-green-300'
                : connector.isAvailable
                  ? 'bg-white border-gray-200 hover:border-blue-300 hover:shadow-sm'
                  : 'bg-gray-50 border-gray-200 opacity-60 cursor-not-allowed'
              }
            `}
          >
            {/* Logo */}
            <div className="w-12 h-12 rounded-xl overflow-hidden bg-white border border-gray-100 flex items-center justify-center shadow-sm">
              <Image
                src={connector.logo}
                alt={connector.name}
                width={32}
                height={32}
                className="object-contain"
              />
            </div>

            {/* Info */}
            <div className="flex-1 ml-4 text-left">
              <div className="flex items-center">
                <h4 className="font-medium text-gray-900">{connector.name}</h4>
                {isConnected && (
                  <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700">
                    <Check className="h-3 w-3 mr-1" />
                    Connected
                  </span>
                )}
              </div>
              <p className="text-sm text-gray-500 mt-0.5">{connector.description}</p>
            </div>

            {/* Arrow */}
            <ChevronRight className="h-5 w-5 text-gray-400 ml-2" />
          </button>
        );
      })}

      {PREDEFINED_CONNECTORS.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          No predefined connectors available
        </div>
      )}
    </div>
  );
}
