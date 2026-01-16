/**
 * Support Ticket API Client
 *
 * Handles communication with the backend support ticket endpoints.
 *
 * v1.0: Initial implementation
 */

import { API_BASE_URL } from './constants';

export interface SupportTicketRequest {
  subject: string;
  category: 'bug_report' | 'feature_request' | 'question' | 'other';
  description: string;
  email?: string;
}

export interface SupportTicketResponse {
  success: boolean;
  ticket_id: string;
  message: string;
}

export interface SupportTicket {
  id: number;
  ticket_id: string;
  user_id: number | null;
  subject: string;
  category: string;
  description: string;
  email: string | null;
  status: 'open' | 'in_progress' | 'resolved' | 'closed';
  created_at: string;
  updated_at: string;
}

/**
 * Submit a new support ticket
 */
export async function submitSupportTicket(
  request: SupportTicketRequest
): Promise<SupportTicketResponse> {
  const token = localStorage.getItem('access_token');

  const response = await fetch(`${API_BASE_URL}/support/tickets`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to submit support ticket');
  }

  return response.json();
}

/**
 * Get user's support tickets
 */
export async function getUserTickets(): Promise<SupportTicket[]> {
  const token = localStorage.getItem('access_token');

  if (!token) {
    throw new Error('Authentication required');
  }

  const response = await fetch(`${API_BASE_URL}/support/tickets`, {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to fetch support tickets');
  }

  return response.json();
}

/**
 * Get a specific support ticket by ID
 */
export async function getTicketById(ticketId: string): Promise<SupportTicket> {
  const token = localStorage.getItem('access_token');

  if (!token) {
    throw new Error('Authentication required');
  }

  const response = await fetch(`${API_BASE_URL}/support/tickets/${ticketId}`, {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to fetch support ticket');
  }

  return response.json();
}
