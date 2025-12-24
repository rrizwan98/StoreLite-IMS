/**
 * ConnectorDetailView Component
 *
 * Shows detailed information about a predefined connector (like Notion).
 * Displays connector info and a "Connect" button to start OAuth flow.
 */

'use client';

import Image from 'next/image';
import { ArrowLeft, ExternalLink, Shield, FileSearch, RefreshCw } from 'lucide-react';
import { PredefinedConnector } from '@/lib/predefined-connectors';

interface ConnectorDetailViewProps {
  connector: PredefinedConnector;
  onBack: () => void;
  onConnect: () => void;
  isConnected?: boolean;
  isConnecting?: boolean;
}

export default function ConnectorDetailView({
  connector,
  onBack,
  onConnect,
  isConnected = false,
  isConnecting = false,
}: ConnectorDetailViewProps) {
  // Map capabilities to icons
  const getCapabilityIcon = (capability: string) => {
    if (capability.toLowerCase().includes('search')) {
      return <FileSearch className="h-4 w-4" />;
    }
    if (capability.toLowerCase().includes('sync')) {
      return <RefreshCw className="h-4 w-4" />;
    }
    return <Shield className="h-4 w-4" />;
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header with back button */}
      <div className="flex items-center px-6 py-4 border-b">
        <button
          onClick={onBack}
          className="flex items-center text-gray-600 hover:text-gray-900 transition-colors"
        >
          <ArrowLeft className="h-5 w-5 mr-2" />
          Back
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-6">
        {/* Connector Header */}
        <div className="flex items-start space-x-4 mb-6">
          {/* Logo */}
          <div className="w-16 h-16 rounded-xl overflow-hidden bg-white border border-gray-200 flex items-center justify-center shadow-sm">
            <Image
              src={connector.logo}
              alt={`${connector.name} logo`}
              width={48}
              height={48}
              className="object-contain"
            />
          </div>

          {/* Title and description */}
          <div className="flex-1">
            <h2 className="text-xl font-semibold text-gray-900">{connector.name}</h2>
            <p className="text-gray-600 mt-1">{connector.description}</p>
          </div>

          {/* Connect button */}
          <button
            onClick={onConnect}
            disabled={isConnecting || isConnected}
            className={`
              px-6 py-2.5 rounded-lg font-medium transition-all
              ${isConnected
                ? 'bg-green-100 text-green-700 cursor-default'
                : isConnecting
                  ? 'bg-blue-400 text-white cursor-wait'
                  : 'bg-blue-600 text-white hover:bg-blue-700 shadow-sm hover:shadow'
              }
            `}
          >
            {isConnected ? 'Connected' : isConnecting ? 'Connecting...' : 'Connect'}
          </button>
        </div>

        {/* Information Section */}
        <div className="bg-gray-50 rounded-xl p-5 mb-6">
          <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-4">
            Information
          </h3>

          <div className="grid grid-cols-2 gap-4">
            {/* Category */}
            <div>
              <dt className="text-xs text-gray-500 uppercase tracking-wide">Category</dt>
              <dd className="text-sm font-medium text-gray-900 mt-1">{connector.category}</dd>
            </div>

            {/* Developer */}
            <div>
              <dt className="text-xs text-gray-500 uppercase tracking-wide">Developer</dt>
              <dd className="text-sm font-medium text-gray-900 mt-1">{connector.developer}</dd>
            </div>

            {/* Capabilities */}
            <div className="col-span-2">
              <dt className="text-xs text-gray-500 uppercase tracking-wide">Capabilities</dt>
              <dd className="flex flex-wrap gap-2 mt-2">
                {connector.capabilities.map((cap) => (
                  <span
                    key={cap}
                    className="inline-flex items-center px-3 py-1 rounded-full bg-white border border-gray-200 text-sm text-gray-700"
                  >
                    <span className="mr-1.5 text-gray-400">{getCapabilityIcon(cap)}</span>
                    {cap}
                  </span>
                ))}
              </dd>
            </div>
          </div>
        </div>

        {/* Links Section */}
        <div className="flex items-center space-x-6 text-sm">
          <a
            href={connector.website}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center text-blue-600 hover:text-blue-700"
          >
            Website
            <ExternalLink className="h-3.5 w-3.5 ml-1" />
          </a>
          <a
            href={connector.privacyPolicy}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center text-blue-600 hover:text-blue-700"
          >
            Privacy Policy
            <ExternalLink className="h-3.5 w-3.5 ml-1" />
          </a>
        </div>
      </div>
    </div>
  );
}
