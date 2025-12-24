'use client';

/**
 * OAuth Callback Page
 *
 * Handles OAuth callback after user authorizes a connector (like Notion).
 *
 * Flow:
 * 1. User clicks "Connect Notion" in our app
 * 2. User is redirected to Notion's OAuth page
 * 3. User authorizes access
 * 4. Notion redirects here with ?code=xxx&state=xxx
 * 5. We call backend /api/oauth/exchange to exchange code for token
 * 6. Show success/error status
 */

import { useEffect, useState, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { CheckCircle, XCircle, Loader2, MessageSquare, Settings } from 'lucide-react';
import { API_BASE_URL } from '@/lib/constants';
import { getAccessToken } from '@/lib/auth-api';
import { exchangeNotionCode } from '@/lib/connectors-api';

function OAuthCallbackContent() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [connectorName, setConnectorName] = useState<string>('');
  const [errorMessage, setErrorMessage] = useState<string>('');

  useEffect(() => {
    async function handleCallback() {
      // Check for OAuth code and state (from Notion redirect)
      const code = searchParams.get('code');
      const state = searchParams.get('state');
      const error = searchParams.get('error');

      // If Notion returned an error
      if (error) {
        setStatus('error');
        setErrorMessage(error === 'access_denied'
          ? 'You cancelled the authorization. No changes were made.'
          : `Authorization failed: ${error}`
        );
        return;
      }

      // If we have code and state, exchange for token
      if (code && state) {
        try {
          const token = getAccessToken();
          if (!token) {
            setStatus('error');
            setErrorMessage('You must be logged in to connect a service. Please log in and try again.');
            return;
          }

          // Use the new Notion MCP exchange endpoint
          // This uses Dynamic Client Registration - no developer credentials needed!
          const data = await exchangeNotionCode(code, state);

          if (data.success) {
            setStatus('success');
            setConnectorName(data.connector_name || 'Notion');
          } else {
            setStatus('error');
            setErrorMessage(data.message || 'Failed to complete connection.');
          }
        } catch (err) {
          console.error('OAuth exchange error:', err);
          setStatus('error');
          const errorMessage = err instanceof Error ? err.message : 'Network error';
          setErrorMessage(errorMessage);
        }
        return;
      }

      // Legacy: Check for success/error params (from old flow)
      const success = searchParams.get('success');
      const message = searchParams.get('message');
      const name = searchParams.get('name');

      if (success === 'true') {
        setStatus('success');
        setConnectorName(name || 'Connector');
      } else if (searchParams.get('error')) {
        setStatus('error');
        setErrorMessage(message || getErrorMessage(searchParams.get('error') || 'unknown'));
      } else {
        // No parameters - probably direct navigation
        setStatus('error');
        setErrorMessage('Invalid callback. Please try connecting again from Settings.');
      }
    }

    handleCallback();
  }, [searchParams]);

  function getErrorMessage(errorCode: string): string {
    const errorMessages: Record<string, string> = {
      oauth_denied: 'You cancelled the authorization. No changes were made.',
      access_denied: 'You cancelled the authorization. No changes were made.',
      invalid_state: 'Session expired. Please try connecting again.',
      invalid_connector: 'Connector mismatch. Please try again.',
      token_exchange_failed: 'Failed to complete authorization. Please try again.',
      server_error: 'An error occurred. Please try again later.',
    };
    return errorMessages[errorCode] || 'An unexpected error occurred.';
  }

  function handleStartChat() {
    router.push('/dashboard/schema-agent');
  }

  function handleGoToSettings() {
    router.push('/dashboard/settings');
  }

  function handleTryAgain() {
    router.push('/dashboard/settings');
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-lg overflow-hidden">
        {/* Loading State */}
        {status === 'loading' && (
          <div className="p-8 text-center">
            <Loader2 className="h-12 w-12 text-blue-600 animate-spin mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-900">Completing connection...</h2>
            <p className="text-gray-500 mt-2">Please wait while we finish setting up.</p>
          </div>
        )}

        {/* Success State */}
        {status === 'success' && (
          <div className="p-8">
            {/* Success Icon */}
            <div className="flex justify-center mb-6">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
                <CheckCircle className="h-10 w-10 text-green-600" />
              </div>
            </div>

            {/* Title */}
            <h2 className="text-2xl font-semibold text-gray-900 text-center">
              Connected Successfully!
            </h2>
            <p className="text-gray-600 text-center mt-2">
              {connectorName} is now connected to your account.
            </p>

            {/* What's Next */}
            <div className="mt-6 p-4 bg-blue-50 rounded-xl">
              <p className="text-sm text-blue-800">
                <strong>What&apos;s next?</strong> You can now use {connectorName} tools in your chat.
                Just ask the Schema Agent to search or reference your {connectorName} content!
              </p>
            </div>

            {/* Action Buttons */}
            <div className="mt-6 space-y-3">
              <button
                onClick={handleStartChat}
                className="w-full flex items-center justify-center px-4 py-3 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 transition-colors"
              >
                <MessageSquare className="h-5 w-5 mr-2" />
                Start Chat
              </button>
              <button
                onClick={handleGoToSettings}
                className="w-full flex items-center justify-center px-4 py-3 bg-gray-100 text-gray-700 rounded-xl font-medium hover:bg-gray-200 transition-colors"
              >
                <Settings className="h-5 w-5 mr-2" />
                Go to Settings
              </button>
            </div>
          </div>
        )}

        {/* Error State */}
        {status === 'error' && (
          <div className="p-8">
            {/* Error Icon */}
            <div className="flex justify-center mb-6">
              <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center">
                <XCircle className="h-10 w-10 text-red-600" />
              </div>
            </div>

            {/* Title */}
            <h2 className="text-2xl font-semibold text-gray-900 text-center">
              Connection Failed
            </h2>
            <p className="text-gray-600 text-center mt-2">
              {errorMessage}
            </p>

            {/* Action Buttons */}
            <div className="mt-8 space-y-3">
              <button
                onClick={handleTryAgain}
                className="w-full flex items-center justify-center px-4 py-3 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 transition-colors"
              >
                Try Again
              </button>
              <button
                onClick={() => router.push('/dashboard')}
                className="w-full flex items-center justify-center px-4 py-3 bg-gray-100 text-gray-700 rounded-xl font-medium hover:bg-gray-200 transition-colors"
              >
                Go to Dashboard
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function OAuthCallbackPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white rounded-2xl shadow-lg p-8 text-center">
          <Loader2 className="h-12 w-12 text-blue-600 animate-spin mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900">Loading...</h2>
        </div>
      </div>
    }>
      <OAuthCallbackContent />
    </Suspense>
  );
}
