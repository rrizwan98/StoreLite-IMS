/**
 * Gmail API Client
 *
 * Functions for interacting with Gmail OAuth2 endpoints.
 */

import { API_BASE_URL } from './constants';
import { getAccessToken } from './auth-api';

/**
 * Gmail connection status
 */
export interface GmailStatus {
  connected: boolean;
  email: string | null;
  connected_at: string | null;
  recipient_email: string | null;
}

/**
 * Authorization URL response
 */
interface GmailAuthorizeResponse {
  authorization_url: string;
  state: string;
}

/**
 * Helper function to make authenticated API requests
 */
async function gmailFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getAccessToken();

  if (!token) {
    throw new Error('Not authenticated');
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `Request failed: ${response.status}`);
  }

  return response.json();
}

/**
 * Get Gmail OAuth2 authorization URL
 *
 * Returns the URL to redirect the user to for Google OAuth consent.
 */
export async function getGmailAuthUrl(): Promise<GmailAuthorizeResponse> {
  return gmailFetch<GmailAuthorizeResponse>('/gmail/authorize');
}

/**
 * Get Gmail connection status
 *
 * Returns whether Gmail is connected and the connected email.
 */
export async function getGmailStatus(): Promise<GmailStatus> {
  return gmailFetch<GmailStatus>('/gmail/status');
}

/**
 * Disconnect Gmail account
 *
 * Revokes OAuth tokens and removes connection.
 */
export async function disconnectGmail(): Promise<{ success: boolean; message: string }> {
  return gmailFetch('/gmail/disconnect', { method: 'DELETE' });
}

/**
 * Get saved recipient email
 */
export async function getRecipientEmail(): Promise<{ email: string | null }> {
  return gmailFetch('/gmail/recipient');
}

/**
 * Update default recipient email
 *
 * @param email - The recipient email to save
 */
export async function updateRecipientEmail(email: string): Promise<{ success: boolean; email: string }> {
  return gmailFetch('/gmail/recipient', {
    method: 'PUT',
    body: JSON.stringify({ email }),
  });
}

/**
 * Send email via Gmail API (direct API call, not via agent)
 *
 * @param to - Recipient email (optional, uses default if not provided)
 * @param subject - Email subject
 * @param body - Email body
 */
export async function sendEmail(
  subject: string,
  body: string,
  to?: string
): Promise<{ success: boolean; message_id?: string; error?: string }> {
  return gmailFetch('/gmail/send', {
    method: 'POST',
    body: JSON.stringify({
      to,
      subject,
      body,
      content_type: 'text/plain',
    }),
  });
}

/**
 * Open Gmail OAuth popup window
 *
 * Opens a popup window for the OAuth flow and returns a promise
 * that resolves when the user completes authorization.
 *
 * @returns Promise that resolves to true if connected successfully
 */
export async function connectGmailWithPopup(): Promise<boolean> {
  return new Promise(async (resolve, reject) => {
    try {
      const { authorization_url } = await getGmailAuthUrl();

      // Calculate popup position (center of screen)
      const width = 500;
      const height = 600;
      const left = window.screenX + (window.outerWidth - width) / 2;
      const top = window.screenY + (window.outerHeight - height) / 2;

      // Open popup
      const popup = window.open(
        authorization_url,
        'gmail-oauth',
        `width=${width},height=${height},left=${left},top=${top},toolbar=no,menubar=no`
      );

      if (!popup) {
        throw new Error('Popup blocked. Please allow popups for this site.');
      }

      // Poll for popup close or success redirect
      const checkInterval = setInterval(async () => {
        try {
          // Check if popup was closed
          if (popup.closed) {
            clearInterval(checkInterval);

            // Check if connection was successful
            const status = await getGmailStatus();
            if (status.connected) {
              resolve(true);
            } else {
              resolve(false);
            }
          }

          // Try to check if we've landed on our success URL
          try {
            const popupUrl = popup.location.href;
            if (popupUrl.includes('gmail_connected=true')) {
              popup.close();
              clearInterval(checkInterval);
              resolve(true);
            } else if (popupUrl.includes('gmail_error=')) {
              popup.close();
              clearInterval(checkInterval);
              const error = new URL(popupUrl).searchParams.get('gmail_error');
              reject(new Error(error || 'OAuth failed'));
            }
          } catch {
            // Cross-origin access denied - popup still on Google
          }
        } catch {
          // Ignore errors from checking popup
        }
      }, 500);

      // Timeout after 5 minutes
      setTimeout(() => {
        clearInterval(checkInterval);
        if (!popup.closed) {
          popup.close();
        }
        reject(new Error('OAuth timed out'));
      }, 300000);
    } catch (error) {
      reject(error);
    }
  });
}
