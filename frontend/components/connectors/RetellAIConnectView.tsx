/**
 * RetellAIConnectView Component
 *
 * Dedicated view for connecting Retell AI with API key.
 * Tests the API key and shows discovered tools before saving.
 */

'use client';

import { useState } from 'react';
import Image from 'next/image';
import {
  ArrowLeft,
  Eye,
  EyeOff,
  Loader2,
  CheckCircle,
  XCircle,
  ExternalLink,
  Phone,
  Users,
  BarChart3,
  Mic,
} from 'lucide-react';
import { PredefinedConnector } from '@/lib/predefined-connectors';
import {
  testRetellAIConnection,
  connectRetellAI,
  DiscoveredTool,
} from '@/lib/connectors-api';

interface RetellAIConnectViewProps {
  connector: PredefinedConnector;
  onBack: () => void;
  onSuccess: (connectorId: number) => void;
  isConnected?: boolean;
}

export default function RetellAIConnectView({
  connector,
  onBack,
  onSuccess,
  isConnected = false,
}: RetellAIConnectViewProps) {
  const [apiKey, setApiKey] = useState('');
  const [showApiKey, setShowApiKey] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{
    success: boolean;
    message: string;
    tools?: DiscoveredTool[];
  } | null>(null);
  const [connecting, setConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canTest = apiKey.trim().length > 0;
  const canConnect = testResult?.success === true;

  async function handleTest() {
    if (!canTest) return;

    setTesting(true);
    setTestResult(null);
    setError(null);

    try {
      const result = await testRetellAIConnection(apiKey.trim());
      setTestResult({
        success: result.success,
        message: result.message,
        tools: result.tools,
      });
    } catch (err) {
      setTestResult({
        success: false,
        message: err instanceof Error ? err.message : 'Connection test failed',
      });
    } finally {
      setTesting(false);
    }
  }

  async function handleConnect() {
    if (!canConnect) return;

    setConnecting(true);
    setError(null);

    try {
      const result = await connectRetellAI(apiKey.trim());
      if (result.success && result.connector_id) {
        onSuccess(result.connector_id);
      } else {
        setError(result.message || 'Failed to connect');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to connect');
    } finally {
      setConnecting(false);
    }
  }

  // Map capabilities to icons
  const getCapabilityIcon = (capability: string) => {
    const capLower = capability.toLowerCase();
    if (capLower.includes('call')) return <Phone className="h-4 w-4" />;
    if (capLower.includes('agent')) return <Users className="h-4 w-4" />;
    if (capLower.includes('analytics')) return <BarChart3 className="h-4 w-4" />;
    if (capLower.includes('voice')) return <Mic className="h-4 w-4" />;
    return <Phone className="h-4 w-4" />;
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
        </div>

        {/* API Key Input Section */}
        {!isConnected && (
          <div className="bg-gray-50 rounded-xl p-5 mb-6">
            <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-4">
              Enter API Key
            </h3>

            <p className="text-sm text-gray-600 mb-4">
              {connector.apiKeyConfig?.helpText || 'Enter your Retell AI API key to connect.'}
            </p>

            {/* API Key Input */}
            <div className="relative mb-4">
              <input
                type={showApiKey ? 'text' : 'password'}
                value={apiKey}
                onChange={(e) => {
                  setApiKey(e.target.value);
                  setTestResult(null);
                  setError(null);
                }}
                placeholder={connector.apiKeyConfig?.placeholder || 'key_xxxxxxxxxxxxxxxx'}
                className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm font-mono"
              />
              <button
                type="button"
                onClick={() => setShowApiKey(!showApiKey)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                {showApiKey ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
              </button>
            </div>

            {/* Get API Key Link */}
            <a
              href={connector.apiKeyConfig?.helpUrl || 'https://dashboard.retellai.com/apiKey'}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center text-sm text-blue-600 hover:text-blue-700 mb-4"
            >
              Get your API key from Retell AI Dashboard
              <ExternalLink className="h-3.5 w-3.5 ml-1" />
            </a>

            {/* Test Button */}
            <div className="flex items-center space-x-4">
              <button
                onClick={handleTest}
                disabled={!canTest || testing}
                className={`
                  flex items-center px-4 py-2 rounded-lg font-medium transition-colors
                  ${canTest && !testing
                    ? 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  }
                `}
              >
                {testing ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Testing...
                  </>
                ) : (
                  'Test Connection'
                )}
              </button>

              {/* Test Result */}
              {testResult && (
                <div
                  className={`flex items-center ${
                    testResult.success ? 'text-green-600' : 'text-red-600'
                  }`}
                >
                  {testResult.success ? (
                    <>
                      <CheckCircle className="h-5 w-5 mr-2" />
                      <span className="text-sm">
                        Connected! Found {testResult.tools?.length || 0} tools
                      </span>
                    </>
                  ) : (
                    <>
                      <XCircle className="h-5 w-5 mr-2" />
                      <span className="text-sm">{testResult.message}</span>
                    </>
                  )}
                </div>
              )}
            </div>

            {/* Discovered Tools Preview */}
            {testResult?.success && testResult.tools && testResult.tools.length > 0 && (
              <div className="mt-4 border border-gray-200 rounded-lg p-4 bg-white">
                <h4 className="text-sm font-medium text-gray-700 mb-2">
                  Discovered Tools ({testResult.tools.length})
                </h4>
                <div className="flex flex-wrap gap-2">
                  {testResult.tools.slice(0, 8).map((tool) => (
                    <span
                      key={tool.name}
                      className="px-2 py-1 bg-gray-50 border border-gray-200 rounded text-xs text-gray-600"
                    >
                      {tool.name}
                    </span>
                  ))}
                  {testResult.tools.length > 8 && (
                    <span className="px-2 py-1 text-xs text-gray-500">
                      +{testResult.tools.length - 8} more
                    </span>
                  )}
                </div>
              </div>
            )}

            {/* Error Message */}
            {error && (
              <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                {error}
              </div>
            )}

            {/* Connect Button */}
            {canConnect && (
              <div className="mt-6">
                <button
                  onClick={handleConnect}
                  disabled={connecting}
                  className={`
                    w-full flex items-center justify-center px-4 py-3 rounded-lg font-medium transition-colors
                    ${!connecting
                      ? 'bg-blue-600 text-white hover:bg-blue-700'
                      : 'bg-blue-400 text-white cursor-wait'
                    }
                  `}
                >
                  {connecting ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Connecting...
                    </>
                  ) : (
                    'Connect Retell AI'
                  )}
                </button>
              </div>
            )}
          </div>
        )}

        {/* Already Connected */}
        {isConnected && (
          <div className="bg-green-50 border border-green-200 rounded-xl p-5 mb-6">
            <div className="flex items-center text-green-700">
              <CheckCircle className="h-5 w-5 mr-2" />
              <span className="font-medium">Retell AI is connected</span>
            </div>
            <p className="text-sm text-green-600 mt-2">
              You can now use Retell AI voice tools in your conversations.
            </p>
          </div>
        )}

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
