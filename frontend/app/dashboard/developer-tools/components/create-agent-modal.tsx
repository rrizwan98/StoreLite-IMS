/**
 * Create Agent Modal Component
 *
 * Multi-step wizard for creating a new published agent.
 */

'use client';

import { useState, useEffect } from 'react';
import {
  X, ChevronRight, ChevronLeft, Check, Loader2,
  Key, Database, Shield, Globe, MessageSquare, Copy, AlertCircle
} from 'lucide-react';
import {
  createPublishedAgent,
  getAvailableTables,
  TableSummary,
  CreateAgentRequest,
  AgentCreatedResponse,
} from '@/lib/developer-tools-api';
import TableSelector from './table-selector';

interface CreateAgentModalProps {
  onClose: () => void;
  onCreated: () => void;
}

type Step = 'info' | 'tables' | 'permissions' | 'domains' | 'success';

export default function CreateAgentModal({ onClose, onCreated }: CreateAgentModalProps) {
  const [step, setStep] = useState<Step>('info');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);

  // Form data
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [selectedTables, setSelectedTables] = useState<string[]>([]);
  const [accessMode, setAccessMode] = useState<'read_only' | 'read_write'>('read_only');
  const [rateLimit, setRateLimit] = useState(60);
  const [allowedDomains, setAllowedDomains] = useState<string[]>(['*']);
  const [customInstructions, setCustomInstructions] = useState('');

  // Available tables
  const [availableTables, setAvailableTables] = useState<TableSummary[]>([]);
  const [tablesLoading, setTablesLoading] = useState(true);

  // Created agent result
  const [createdAgent, setCreatedAgent] = useState<AgentCreatedResponse | null>(null);

  // Load available tables
  useEffect(() => {
    const loadTables = async () => {
      try {
        const tables = await getAvailableTables();
        setAvailableTables(tables);
      } catch (err) {
        console.error('Failed to load tables:', err);
        setError('Failed to load tables from your database');
      } finally {
        setTablesLoading(false);
      }
    };
    loadTables();
  }, []);

  // Step navigation
  const steps: { key: Step; label: string; icon: React.ReactNode }[] = [
    { key: 'info', label: 'Basic Info', icon: <MessageSquare className="h-4 w-4" /> },
    { key: 'tables', label: 'Tables', icon: <Database className="h-4 w-4" /> },
    { key: 'permissions', label: 'Permissions', icon: <Shield className="h-4 w-4" /> },
    { key: 'domains', label: 'Domains', icon: <Globe className="h-4 w-4" /> },
  ];

  const currentStepIndex = steps.findIndex(s => s.key === step);

  const canProceed = () => {
    switch (step) {
      case 'info':
        return name.trim().length > 0;
      case 'tables':
        return selectedTables.length > 0;
      case 'permissions':
        return rateLimit >= 1 && rateLimit <= 1000;
      case 'domains':
        return allowedDomains.length > 0;
      default:
        return false;
    }
  };

  const handleNext = () => {
    if (step === 'domains') {
      handleCreate();
    } else {
      const nextIndex = currentStepIndex + 1;
      if (nextIndex < steps.length) {
        setStep(steps[nextIndex].key);
      }
    }
  };

  const handleBack = () => {
    const prevIndex = currentStepIndex - 1;
    if (prevIndex >= 0) {
      setStep(steps[prevIndex].key);
    }
  };

  const handleCreate = async () => {
    setLoading(true);
    setError('');

    const request: CreateAgentRequest = {
      name: name.trim(),
      description: description.trim() || undefined,
      allowed_tables: selectedTables,
      access_mode: accessMode,
      rate_limit_per_minute: rateLimit,
      allowed_domains: allowedDomains,
      custom_instructions: customInstructions.trim() || undefined,
    };

    try {
      const result = await createPublishedAgent(request);
      setCreatedAgent(result);
      setStep('success');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create agent');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyKey = async () => {
    if (createdAgent?.api_key) {
      await navigator.clipboard.writeText(createdAgent.api_key);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleDomainChange = (value: string) => {
    const domains = value.split('\n').map(d => d.trim()).filter(Boolean);
    setAllowedDomains(domains.length > 0 ? domains : ['*']);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Key className="h-6 w-6 text-blue-500" />
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              {step === 'success' ? 'Agent Created!' : 'Create Published Agent'}
            </h2>
          </div>
          <button
            onClick={step === 'success' ? onCreated : onClose}
            className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Progress Steps */}
        {step !== 'success' && (
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between">
              {steps.map((s, i) => (
                <div key={s.key} className="flex items-center">
                  <div
                    className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                      i === currentStepIndex
                        ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400'
                        : i < currentStepIndex
                        ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                        : 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400'
                    }`}
                  >
                    {i < currentStepIndex ? (
                      <Check className="h-4 w-4" />
                    ) : (
                      s.icon
                    )}
                    <span className="hidden sm:inline">{s.label}</span>
                  </div>
                  {i < steps.length - 1 && (
                    <ChevronRight className="h-4 w-4 mx-2 text-gray-400" />
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {error && (
            <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-600 dark:text-red-400 text-sm flex items-center gap-2">
              <AlertCircle className="h-4 w-4 flex-shrink-0" />
              {error}
            </div>
          )}

          {/* Step: Basic Info */}
          {step === 'info' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Agent Name *
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g., Customer Support Agent"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  maxLength={255}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Description (optional)
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Brief description of what this agent does..."
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
                  maxLength={1000}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Custom Instructions (optional)
                </label>
                <textarea
                  value={customInstructions}
                  onChange={(e) => setCustomInstructions(e.target.value)}
                  placeholder="Additional instructions for the agent (e.g., 'Always be helpful and respond in Spanish')"
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
                  maxLength={2000}
                />
              </div>
            </div>
          )}

          {/* Step: Tables */}
          {step === 'tables' && (
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                Select which tables external users can access through this agent.
              </p>
              {tablesLoading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin text-blue-500" />
                </div>
              ) : (
                <TableSelector
                  tables={availableTables}
                  selectedTables={selectedTables}
                  onChange={setSelectedTables}
                />
              )}
            </div>
          )}

          {/* Step: Permissions */}
          {step === 'permissions' && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                  Access Mode
                </label>
                <div className="space-y-2">
                  <label className="flex items-start gap-3 p-3 border border-gray-200 dark:border-gray-700 rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                    <input
                      type="radio"
                      name="accessMode"
                      value="read_only"
                      checked={accessMode === 'read_only'}
                      onChange={() => setAccessMode('read_only')}
                      className="mt-1"
                    />
                    <div>
                      <div className="font-medium text-gray-900 dark:text-white">Read Only</div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">
                        Can only query data (SELECT). Recommended for most use cases.
                      </div>
                    </div>
                  </label>
                  <label className="flex items-start gap-3 p-3 border border-gray-200 dark:border-gray-700 rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                    <input
                      type="radio"
                      name="accessMode"
                      value="read_write"
                      checked={accessMode === 'read_write'}
                      onChange={() => setAccessMode('read_write')}
                      className="mt-1"
                    />
                    <div>
                      <div className="font-medium text-gray-900 dark:text-white">Read & Write</div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">
                        Can query and modify data. Use with caution.
                      </div>
                    </div>
                  </label>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Rate Limit (requests per minute)
                </label>
                <input
                  type="number"
                  value={rateLimit}
                  onChange={(e) => setRateLimit(Math.max(1, Math.min(1000, parseInt(e.target.value) || 60)))}
                  min={1}
                  max={1000}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
                <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                  Maximum requests allowed per minute per API key (1-1000)
                </p>
              </div>
            </div>
          )}

          {/* Step: Domains */}
          {step === 'domains' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Allowed Domains
                </label>
                <textarea
                  value={allowedDomains.join('\n')}
                  onChange={(e) => handleDomainChange(e.target.value)}
                  placeholder="*"
                  rows={5}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
                />
                <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                  One domain per line. Use * for all domains, *.example.com for subdomains, localhost:* for any port.
                </p>
              </div>
              <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
                <h4 className="text-sm font-medium text-blue-800 dark:text-blue-200 mb-2">Examples:</h4>
                <ul className="text-sm text-blue-700 dark:text-blue-300 space-y-1">
                  <li><code className="bg-blue-100 dark:bg-blue-900/40 px-1 rounded">*</code> - Allow all domains</li>
                  <li><code className="bg-blue-100 dark:bg-blue-900/40 px-1 rounded">mystore.com</code> - Exact match</li>
                  <li><code className="bg-blue-100 dark:bg-blue-900/40 px-1 rounded">*.mystore.com</code> - All subdomains</li>
                  <li><code className="bg-blue-100 dark:bg-blue-900/40 px-1 rounded">localhost:*</code> - Any localhost port</li>
                </ul>
              </div>
            </div>
          )}

          {/* Step: Success */}
          {step === 'success' && createdAgent && (
            <div className="space-y-6">
              <div className="text-center">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 dark:bg-green-900/30 rounded-full mb-4">
                  <Check className="h-8 w-8 text-green-600 dark:text-green-400" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                  {createdAgent.name} is ready!
                </h3>
                <p className="text-gray-600 dark:text-gray-400">
                  Your agent has been created. Save your API key now - it won&apos;t be shown again.
                </p>
              </div>

              <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <AlertCircle className="h-5 w-5 text-yellow-600 dark:text-yellow-400 flex-shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <h4 className="font-medium text-yellow-800 dark:text-yellow-200 mb-2">
                      Your API Key (save this!)
                    </h4>
                    <div className="flex items-center gap-2">
                      <code className="flex-1 px-3 py-2 bg-yellow-100 dark:bg-yellow-900/40 rounded font-mono text-sm text-yellow-900 dark:text-yellow-100 break-all">
                        {createdAgent.api_key}
                      </code>
                      <button
                        onClick={handleCopyKey}
                        className="flex-shrink-0 p-2 bg-yellow-600 hover:bg-yellow-700 text-white rounded-lg transition-colors"
                      >
                        {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
                <h4 className="font-medium text-gray-900 dark:text-white mb-2">API Endpoint</h4>
                <code className="block px-3 py-2 bg-white dark:bg-gray-800 rounded font-mono text-sm text-gray-700 dark:text-gray-300 break-all">
                  {createdAgent.endpoint}
                </code>
              </div>

              <div className="text-center">
                <button
                  onClick={onCreated}
                  className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                >
                  Done
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        {step !== 'success' && (
          <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between">
            <button
              onClick={handleBack}
              disabled={currentStepIndex === 0}
              className="flex items-center gap-2 px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="h-4 w-4" />
              Back
            </button>
            <button
              onClick={handleNext}
              disabled={!canProceed() || loading}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Creating...
                </>
              ) : step === 'domains' ? (
                <>
                  Create Agent
                  <Check className="h-4 w-4" />
                </>
              ) : (
                <>
                  Next
                  <ChevronRight className="h-4 w-4" />
                </>
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
