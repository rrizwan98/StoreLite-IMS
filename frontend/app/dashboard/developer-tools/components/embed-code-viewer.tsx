/**
 * Embed Code Viewer Component
 *
 * Modal showing the embed code snippet for a published agent.
 */

'use client';

import { useState, useEffect } from 'react';
import { X, Copy, Check, Loader2, Code, AlertCircle, ExternalLink } from 'lucide-react';
import { getEmbedCode, EmbedCodeResponse } from '@/lib/developer-tools-api';

interface EmbedCodeViewerProps {
  agentId: string;
  agentName: string;
  onClose: () => void;
}

export default function EmbedCodeViewer({ agentId, agentName, onClose }: EmbedCodeViewerProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [embedData, setEmbedData] = useState<EmbedCodeResponse | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const loadEmbedCode = async () => {
      try {
        const data = await getEmbedCode(agentId);
        setEmbedData(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load embed code');
      } finally {
        setLoading(false);
      }
    };
    loadEmbedCode();
  }, [agentId]);

  const handleCopy = async () => {
    if (embedData?.embed_code) {
      await navigator.clipboard.writeText(embedData.embed_code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl max-w-3xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Code className="h-6 w-6 text-green-500" />
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Embed Code - {agentName}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
            </div>
          ) : error ? (
            <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-600 dark:text-red-400 flex items-center gap-2">
              <AlertCircle className="h-5 w-5" />
              {error}
            </div>
          ) : embedData && (
            <div className="space-y-6">
              {/* Instructions */}
              <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                <h3 className="font-medium text-blue-800 dark:text-blue-200 mb-2">
                  Integration Instructions
                </h3>
                <div className="text-sm text-blue-700 dark:text-blue-300 whitespace-pre-line">
                  {embedData.instructions}
                </div>
              </div>

              {/* API Endpoint */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  API Endpoint
                </label>
                <code className="block px-4 py-3 bg-gray-100 dark:bg-gray-700 rounded-lg font-mono text-sm text-gray-800 dark:text-gray-200 break-all">
                  {embedData.endpoint}
                </code>
              </div>

              {/* Embed Code */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Embed Code
                  </label>
                  <button
                    onClick={handleCopy}
                    className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-green-600 dark:text-green-400 hover:bg-green-50 dark:hover:bg-green-900/20 rounded-lg transition-colors"
                  >
                    {copied ? (
                      <>
                        <Check className="h-4 w-4" />
                        Copied!
                      </>
                    ) : (
                      <>
                        <Copy className="h-4 w-4" />
                        Copy Code
                      </>
                    )}
                  </button>
                </div>
                <div className="relative">
                  <pre className="p-4 bg-gray-900 rounded-lg overflow-x-auto text-sm">
                    <code className="text-gray-100 whitespace-pre">
                      {embedData.embed_code}
                    </code>
                  </pre>
                </div>
              </div>

              {/* Important Note */}
              <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <AlertCircle className="h-5 w-5 text-yellow-600 dark:text-yellow-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <h4 className="font-medium text-yellow-800 dark:text-yellow-200 mb-1">
                      Important: Replace the API Key
                    </h4>
                    <p className="text-sm text-yellow-700 dark:text-yellow-300">
                      The embed code contains a placeholder <code className="px-1 bg-yellow-200 dark:bg-yellow-900/40 rounded">YOUR_API_KEY_HERE</code>.
                      Replace it with your actual API key before deploying.
                    </p>
                  </div>
                </div>
              </div>

              {/* ChatKit Documentation Link */}
              <div className="flex items-center justify-center pt-4">
                <a
                  href="https://openai.github.io/chatkit-js/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 text-sm text-blue-600 dark:text-blue-400 hover:underline"
                >
                  <ExternalLink className="h-4 w-4" />
                  ChatKit Documentation
                </a>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
