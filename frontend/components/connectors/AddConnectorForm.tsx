/**
 * AddConnectorForm Component
 *
 * Form for adding a new MCP connector with connection testing.
 */

'use client';

import { useState } from 'react';
import {
  Server,
  Loader2,
  CheckCircle,
  XCircle,
  Eye,
  EyeOff,
  AlertTriangle,
} from 'lucide-react';
import {
  AuthType,
  ConnectorCreateRequest,
  ConnectionTestResult,
  testConnection,
  createConnector,
  Connector,
} from '@/lib/connectors-api';

interface AddConnectorFormProps {
  onSuccess?: (connector: Connector) => void;
  onCancel?: () => void;
}

export default function AddConnectorForm({
  onSuccess,
  onCancel,
}: AddConnectorFormProps) {
  // Form state
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [serverUrl, setServerUrl] = useState('');
  const [authType, setAuthType] = useState<AuthType>('none');
  const [apiKey, setApiKey] = useState('');
  const [showApiKey, setShowApiKey] = useState(false);

  // Status state
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<ConnectionTestResult | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isValidUrl = (url: string) => {
    try {
      new URL(url);
      return true;
    } catch {
      return false;
    }
  };

  const canTest = serverUrl && isValidUrl(serverUrl);
  const canSave =
    name.trim() &&
    serverUrl &&
    isValidUrl(serverUrl) &&
    testResult?.success;

  async function handleTest() {
    if (!canTest) return;

    try {
      setTesting(true);
      setTestResult(null);
      setError(null);

      const authConfig = authType === 'api_key' && apiKey ? { api_key: apiKey } : undefined;
      const result = await testConnection(serverUrl, authType, authConfig);
      setTestResult(result);
    } catch (err) {
      setTestResult({
        success: false,
        error_message: err instanceof Error ? err.message : 'Connection test failed',
      });
    } finally {
      setTesting(false);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!canSave) return;

    try {
      setSaving(true);
      setError(null);

      const request: ConnectorCreateRequest = {
        name: name.trim(),
        description: description.trim() || undefined,
        server_url: serverUrl,
        auth_type: authType,
      };

      if (authType === 'api_key' && apiKey) {
        request.auth_config = { api_key: apiKey };
      }

      const connector = await createConnector(request);
      onSuccess?.(connector);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save connector');
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Header */}
      <div className="flex items-center space-x-3">
        <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-blue-100">
          <Server className="h-5 w-5 text-blue-600" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Add MCP Connector</h2>
          <p className="text-sm text-gray-500">Connect to an external MCP server</p>
        </div>
      </div>

      {/* Error message */}
      {error && (
        <div className="flex items-center p-3 bg-red-50 border border-red-200 rounded-lg text-red-700">
          <AlertTriangle className="h-5 w-5 mr-2 flex-shrink-0" />
          <span className="text-sm">{error}</span>
        </div>
      )}

      {/* Server URL */}
      <div>
        <label htmlFor="serverUrl" className="block text-sm font-medium text-gray-700 mb-1">
          Server URL <span className="text-red-500">*</span>
        </label>
        <input
          id="serverUrl"
          type="url"
          value={serverUrl}
          onChange={(e) => {
            setServerUrl(e.target.value);
            setTestResult(null);
          }}
          placeholder="https://example.com/mcp"
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          required
        />
        {serverUrl && !isValidUrl(serverUrl) && (
          <p className="mt-1 text-sm text-red-600">Please enter a valid URL</p>
        )}
      </div>

      {/* Auth Type */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Authentication
        </label>
        <div className="flex space-x-4">
          <label className="flex items-center">
            <input
              type="radio"
              name="authType"
              value="none"
              checked={authType === 'none'}
              onChange={() => {
                setAuthType('none');
                setTestResult(null);
              }}
              className="h-4 w-4 text-blue-600"
            />
            <span className="ml-2 text-sm text-gray-700">None</span>
          </label>
          <label className="flex items-center">
            <input
              type="radio"
              name="authType"
              value="api_key"
              checked={authType === 'api_key'}
              onChange={() => {
                setAuthType('api_key');
                setTestResult(null);
              }}
              className="h-4 w-4 text-blue-600"
            />
            <span className="ml-2 text-sm text-gray-700">API Key</span>
          </label>
        </div>
      </div>

      {/* API Key (conditional) */}
      {authType === 'api_key' && (
        <div>
          <label htmlFor="apiKey" className="block text-sm font-medium text-gray-700 mb-1">
            API Key <span className="text-red-500">*</span>
          </label>
          <div className="relative">
            <input
              id="apiKey"
              type={showApiKey ? 'text' : 'password'}
              value={apiKey}
              onChange={(e) => {
                setApiKey(e.target.value);
                setTestResult(null);
              }}
              placeholder="Enter your API key"
              className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
            <button
              type="button"
              onClick={() => setShowApiKey(!showApiKey)}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              {showApiKey ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
            </button>
          </div>
        </div>
      )}

      {/* Test Connection Button */}
      <div className="flex items-center space-x-4">
        <button
          type="button"
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
                <span className="text-sm">{testResult.error_message || 'Connection failed'}</span>
              </>
            )}
          </div>
        )}
      </div>

      {/* Discovered Tools Preview */}
      {testResult?.success && testResult.tools && testResult.tools.length > 0 && (
        <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
          <h3 className="text-sm font-medium text-gray-700 mb-2">
            Discovered Tools ({testResult.tools.length})
          </h3>
          <div className="flex flex-wrap gap-2">
            {testResult.tools.slice(0, 5).map((tool) => (
              <span
                key={tool.name}
                className="px-2 py-1 bg-white border border-gray-200 rounded text-xs text-gray-600"
              >
                {tool.name}
              </span>
            ))}
            {testResult.tools.length > 5 && (
              <span className="px-2 py-1 text-xs text-gray-500">
                +{testResult.tools.length - 5} more
              </span>
            )}
          </div>
        </div>
      )}

      {/* Name (only after successful test) */}
      {testResult?.success && (
        <>
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
              Connector Name <span className="text-red-500">*</span>
            </label>
            <input
              id="name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="My MCP Server"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            />
          </div>

          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Optional description of this connector"
              rows={2}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </>
      )}

      {/* Actions */}
      <div className="flex justify-end space-x-3 pt-4 border-t">
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 text-gray-700 hover:text-gray-900"
          >
            Cancel
          </button>
        )}
        <button
          type="submit"
          disabled={!canSave || saving}
          className={`
            flex items-center px-4 py-2 rounded-lg font-medium transition-colors
            ${canSave && !saving
              ? 'bg-blue-600 text-white hover:bg-blue-700'
              : 'bg-blue-300 text-white cursor-not-allowed'
            }
          `}
        >
          {saving ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Saving...
            </>
          ) : (
            'Save Connector'
          )}
        </button>
      </div>
    </form>
  );
}
