/**
 * Connect Tools Section Component
 *
 * Dashboard section for managing external tool connections (Gmail, etc.)
 * Displays connection status and allows users to connect/disconnect tools.
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  GmailStatus,
  getGmailStatus,
  connectGmailWithPopup,
  disconnectGmail,
  updateRecipientEmail,
} from '@/lib/gmail-api';

interface ConnectToolsSectionProps {
  className?: string;
}

export default function ConnectToolsSection({ className = '' }: ConnectToolsSectionProps) {
  // Gmail state
  const [gmailStatus, setGmailStatus] = useState<GmailStatus | null>(null);
  const [gmailLoading, setGmailLoading] = useState(true);
  const [gmailError, setGmailError] = useState<string | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isDisconnecting, setIsDisconnecting] = useState(false);

  // Recipient email form state
  const [recipientEmail, setRecipientEmail] = useState('');
  const [isSavingRecipient, setIsSavingRecipient] = useState(false);
  const [recipientSaved, setRecipientSaved] = useState(false);
  const [recipientError, setRecipientError] = useState<string | null>(null);

  // Fetch Gmail status on mount and after URL params check
  const fetchGmailStatus = useCallback(async () => {
    try {
      setGmailLoading(true);
      setGmailError(null);
      const status = await getGmailStatus();
      setGmailStatus(status);
      if (status.recipient_email) {
        setRecipientEmail(status.recipient_email);
      }
    } catch (err) {
      console.error('Failed to fetch Gmail status:', err);
      setGmailError('Failed to check Gmail status');
    } finally {
      setGmailLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchGmailStatus();

    // Check URL params for OAuth callback result
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('gmail_connected') === 'true') {
      // Clear URL params and refresh status
      window.history.replaceState({}, '', window.location.pathname);
      fetchGmailStatus();
    } else if (urlParams.get('gmail_error')) {
      const error = urlParams.get('gmail_error');
      setGmailError(error?.replace(/_/g, ' ') || 'Connection failed');
      window.history.replaceState({}, '', window.location.pathname);
    }
  }, [fetchGmailStatus]);

  // Handle Gmail connect
  const handleConnectGmail = async () => {
    setIsConnecting(true);
    setGmailError(null);

    try {
      const success = await connectGmailWithPopup();
      if (success) {
        await fetchGmailStatus();
      }
    } catch (err) {
      console.error('Gmail connection failed:', err);
      setGmailError(err instanceof Error ? err.message : 'Connection failed');
    } finally {
      setIsConnecting(false);
    }
  };

  // Handle Gmail disconnect
  const handleDisconnectGmail = async () => {
    setIsDisconnecting(true);
    setGmailError(null);

    try {
      await disconnectGmail();
      setGmailStatus({ connected: false, email: null, connected_at: null, recipient_email: null });
      setRecipientEmail('');
    } catch (err) {
      console.error('Gmail disconnect failed:', err);
      setGmailError(err instanceof Error ? err.message : 'Disconnect failed');
    } finally {
      setIsDisconnecting(false);
    }
  };

  // Handle save recipient email
  const handleSaveRecipient = async () => {
    if (!recipientEmail.trim()) {
      setRecipientError('Please enter an email address');
      return;
    }

    // Basic email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(recipientEmail)) {
      setRecipientError('Please enter a valid email address');
      return;
    }

    setIsSavingRecipient(true);
    setRecipientError(null);
    setRecipientSaved(false);

    try {
      await updateRecipientEmail(recipientEmail);
      setRecipientSaved(true);
      setTimeout(() => setRecipientSaved(false), 3000);
    } catch (err) {
      console.error('Failed to save recipient:', err);
      setRecipientError(err instanceof Error ? err.message : 'Failed to save');
    } finally {
      setIsSavingRecipient(false);
    }
  };

  return (
    <div className={`bg-white rounded-xl shadow-md p-6 ${className}`}>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-gray-900">Connect Tools</h2>
          <p className="text-sm text-gray-600">Extend your AI agent with external services</p>
        </div>
      </div>

      {/* Gmail Connection Card */}
      <div className="border border-gray-200 rounded-lg p-5">
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-4">
            {/* Gmail Icon */}
            <div className="w-12 h-12 bg-red-50 rounded-lg flex items-center justify-center">
              <svg className="w-7 h-7" viewBox="0 0 24 24">
                <path
                  fill="#EA4335"
                  d="M24 5.457v13.909c0 .904-.732 1.636-1.636 1.636h-3.819V11.73L12 16.64l-6.545-4.91v9.273H1.636A1.636 1.636 0 0 1 0 19.366V5.457c0-2.023 2.309-3.178 3.927-1.964L5.455 4.64 12 9.548l6.545-4.91 1.528-1.145C21.69 2.28 24 3.434 24 5.457z"
                />
              </svg>
            </div>

            <div>
              <h3 className="font-semibold text-gray-900">Gmail</h3>
              {gmailLoading ? (
                <p className="text-sm text-gray-500">Checking status...</p>
              ) : gmailStatus?.connected ? (
                <p className="text-sm text-green-600 flex items-center">
                  <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                  Connected: {gmailStatus.email}
                </p>
              ) : (
                <p className="text-sm text-gray-500">Not connected</p>
              )}
            </div>
          </div>

          {/* Connect/Disconnect Button */}
          {!gmailLoading && (
            gmailStatus?.connected ? (
              <button
                onClick={handleDisconnectGmail}
                disabled={isDisconnecting}
                className="px-4 py-2 text-sm font-medium text-red-600 bg-red-50 rounded-lg hover:bg-red-100 disabled:opacity-50 transition-colors"
              >
                {isDisconnecting ? 'Disconnecting...' : 'Disconnect'}
              </button>
            ) : (
              <button
                onClick={handleConnectGmail}
                disabled={isConnecting}
                className="px-4 py-2 text-sm font-medium text-white bg-red-500 rounded-lg hover:bg-red-600 disabled:opacity-50 transition-colors flex items-center space-x-2"
              >
                {isConnecting ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    <span>Connecting...</span>
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                      <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                      <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                      <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
                    </svg>
                    <span>Sign in with Google</span>
                  </>
                )}
              </button>
            )
          )}
        </div>

        {/* Error Message */}
        {gmailError && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
            {gmailError}
          </div>
        )}

        {/* Recipient Email Form - Show only when connected */}
        {gmailStatus?.connected && (
          <div className="mt-5 pt-5 border-t border-gray-100">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Default Recipient Email
            </label>
            <p className="text-xs text-gray-500 mb-3">
              Emails will be sent to this address when you ask the AI agent to email something.
            </p>
            <div className="flex space-x-3">
              <input
                type="email"
                value={recipientEmail}
                onChange={(e) => {
                  setRecipientEmail(e.target.value);
                  setRecipientError(null);
                  setRecipientSaved(false);
                }}
                placeholder="recipient@example.com"
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
              />
              <button
                onClick={handleSaveRecipient}
                disabled={isSavingRecipient || !recipientEmail.trim()}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:bg-blue-400 transition-colors"
              >
                {isSavingRecipient ? 'Saving...' : recipientSaved ? 'Saved!' : 'Save'}
              </button>
            </div>
            {recipientError && (
              <p className="mt-2 text-sm text-red-600">{recipientError}</p>
            )}
            {recipientSaved && (
              <p className="mt-2 text-sm text-green-600">Recipient saved successfully!</p>
            )}
          </div>
        )}

        {/* Info about email tool */}
        {gmailStatus?.connected && (
          <div className="mt-4 p-4 bg-blue-50 rounded-lg">
            <div className="flex items-start space-x-3">
              <span className="text-blue-500 text-lg">💡</span>
              <div className="text-sm text-blue-800">
                <p className="font-medium mb-1">How to use:</p>
                <p>
                  Just ask the AI agent to email any response. For example:
                  <span className="block mt-1 italic text-blue-600">
                    &quot;Show me sales by month and email this report&quot;
                  </span>
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Future Tools Placeholder */}
      <div className="mt-4 border border-dashed border-gray-200 rounded-lg p-5 text-center">
        <div className="text-gray-400 text-3xl mb-2">+</div>
        <p className="text-sm text-gray-500">More integrations coming soon</p>
        <p className="text-xs text-gray-400 mt-1">Slack, Notion, Google Sheets...</p>
      </div>
    </div>
  );
}
