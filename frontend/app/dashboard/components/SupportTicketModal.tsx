/**
 * Support Ticket Modal Component
 *
 * A contact support form that:
 * - Collects user issues with categories
 * - Validates form fields
 * - Submits to backend API
 * - Shows confirmation with ticket ID
 *
 * v1.0: Initial implementation
 */

'use client';

import { useState, useEffect } from 'react';
import {
  X,
  Send,
  CheckCircle,
  AlertCircle,
  Loader2,
  Mail,
  MessageSquare,
  Tag,
  FileText,
} from 'lucide-react';
import { useAuth } from '@/lib/auth-context';
import { submitSupportTicket, SupportTicketRequest } from '@/lib/support-api';

interface SupportTicketModalProps {
  isOpen: boolean;
  onClose: () => void;
}

type TicketCategory = 'bug_report' | 'feature_request' | 'question' | 'other';

interface FormState {
  subject: string;
  category: TicketCategory;
  description: string;
  email: string;
}

interface FormErrors {
  subject?: string;
  description?: string;
  email?: string;
}

export default function SupportTicketModal({
  isOpen,
  onClose,
}: SupportTicketModalProps) {
  const { user } = useAuth();
  const [formState, setFormState] = useState<FormState>({
    subject: '',
    category: 'question',
    description: '',
    email: user?.email || '',
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitResult, setSubmitResult] = useState<{
    success: boolean;
    ticketId?: string;
    message?: string;
  } | null>(null);

  // Pre-fill email when user changes
  useEffect(() => {
    if (user?.email && !formState.email) {
      setFormState((prev) => ({ ...prev, email: user.email || '' }));
    }
  }, [user?.email, formState.email]);

  // Close on Escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !isSubmitting) {
        onClose();
      }
    };
    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }
    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = '';
    };
  }, [isOpen, onClose, isSubmitting]);

  // Reset form when modal opens
  useEffect(() => {
    if (isOpen) {
      setFormState({
        subject: '',
        category: 'question',
        description: '',
        email: user?.email || '',
      });
      setErrors({});
      setSubmitResult(null);
    }
  }, [isOpen, user?.email]);

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    if (!formState.subject.trim()) {
      newErrors.subject = 'Subject is required';
    } else if (formState.subject.length > 255) {
      newErrors.subject = 'Subject must be less than 255 characters';
    }

    if (!formState.description.trim()) {
      newErrors.description = 'Description is required';
    } else if (formState.description.length < 10) {
      newErrors.description = 'Please provide more details (at least 10 characters)';
    }

    if (formState.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formState.email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) return;

    setIsSubmitting(true);
    setSubmitResult(null);

    try {
      const request: SupportTicketRequest = {
        subject: formState.subject.trim(),
        category: formState.category,
        description: formState.description.trim(),
        email: formState.email.trim() || undefined,
      };

      const result = await submitSupportTicket(request);

      setSubmitResult({
        success: true,
        ticketId: result.ticket_id,
        message: result.message,
      });
    } catch (error) {
      console.error('Failed to submit support ticket:', error);
      setSubmitResult({
        success: false,
        message: error instanceof Error ? error.message : 'Failed to submit ticket. Please try again.',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setFormState((prev) => ({ ...prev, [name]: value }));
    // Clear error when user starts typing
    if (errors[name as keyof FormErrors]) {
      setErrors((prev) => ({ ...prev, [name]: undefined }));
    }
  };

  if (!isOpen) return null;

  const categoryOptions: { value: TicketCategory; label: string; description: string }[] = [
    { value: 'bug_report', label: 'Bug Report', description: 'Something is not working correctly' },
    { value: 'feature_request', label: 'Feature Request', description: 'Suggest a new feature' },
    { value: 'question', label: 'Question', description: 'Need help or clarification' },
    { value: 'other', label: 'Other', description: 'Other feedback or inquiry' },
  ];

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
      onClick={onClose}
    >
      <div
        className="w-full max-w-lg bg-white dark:bg-gray-800 rounded-2xl shadow-2xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-gradient-to-r from-emerald-500 to-teal-500">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center">
                <MessageSquare className="h-5 w-5 text-white" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-white">Contact Support</h2>
                <p className="text-sm text-white/80">We typically respond within 24 hours</p>
              </div>
            </div>
            <button
              onClick={onClose}
              disabled={isSubmitting}
              className="p-2 text-white/80 hover:text-white hover:bg-white/10 rounded-lg transition-colors disabled:opacity-50"
              aria-label="Close"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          {submitResult?.success ? (
            // Success State
            <div className="text-center py-8">
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center">
                <CheckCircle className="h-8 w-8 text-emerald-600 dark:text-emerald-400" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Ticket Submitted!
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                {submitResult.message}
              </p>
              <div className="inline-block px-4 py-2 bg-gray-100 dark:bg-gray-700 rounded-lg">
                <p className="text-sm text-gray-500 dark:text-gray-400">Ticket ID</p>
                <p className="font-mono font-semibold text-gray-900 dark:text-white">
                  {submitResult.ticketId}
                </p>
              </div>
              <div className="mt-6">
                <button
                  onClick={onClose}
                  className="px-6 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors"
                >
                  Close
                </button>
              </div>
            </div>
          ) : submitResult?.success === false ? (
            // Error State
            <div className="text-center py-8">
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
                <AlertCircle className="h-8 w-8 text-red-600 dark:text-red-400" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Submission Failed
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                {submitResult.message}
              </p>
              <div className="flex gap-3 justify-center">
                <button
                  onClick={() => setSubmitResult(null)}
                  className="px-6 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors"
                >
                  Try Again
                </button>
                <button
                  onClick={onClose}
                  className="px-6 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            // Form
            <form onSubmit={handleSubmit} className="space-y-5">
              {/* Subject */}
              <div>
                <label
                  htmlFor="subject"
                  className="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5"
                >
                  <FileText className="h-4 w-4" />
                  Subject <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  id="subject"
                  name="subject"
                  value={formState.subject}
                  onChange={handleChange}
                  placeholder="Brief description of your issue"
                  className={`w-full px-4 py-2.5 rounded-lg border ${
                    errors.subject
                      ? 'border-red-300 dark:border-red-600 focus:ring-red-500'
                      : 'border-gray-300 dark:border-gray-600 focus:ring-emerald-500'
                  } bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                  placeholder-gray-400 focus:ring-2 focus:border-transparent outline-none transition-colors`}
                  disabled={isSubmitting}
                />
                {errors.subject && (
                  <p className="mt-1.5 text-sm text-red-500 flex items-center gap-1">
                    <AlertCircle className="h-4 w-4" />
                    {errors.subject}
                  </p>
                )}
              </div>

              {/* Category */}
              <div>
                <label
                  htmlFor="category"
                  className="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5"
                >
                  <Tag className="h-4 w-4" />
                  Category
                </label>
                <select
                  id="category"
                  name="category"
                  value={formState.category}
                  onChange={handleChange}
                  className="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600
                           bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                           focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none transition-colors"
                  disabled={isSubmitting}
                >
                  {categoryOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label} - {option.description}
                    </option>
                  ))}
                </select>
              </div>

              {/* Description */}
              <div>
                <label
                  htmlFor="description"
                  className="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5"
                >
                  <MessageSquare className="h-4 w-4" />
                  Description <span className="text-red-500">*</span>
                </label>
                <textarea
                  id="description"
                  name="description"
                  value={formState.description}
                  onChange={handleChange}
                  placeholder="Please describe your issue in detail. Include any error messages, steps to reproduce, or relevant context."
                  rows={5}
                  className={`w-full px-4 py-2.5 rounded-lg border ${
                    errors.description
                      ? 'border-red-300 dark:border-red-600 focus:ring-red-500'
                      : 'border-gray-300 dark:border-gray-600 focus:ring-emerald-500'
                  } bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                  placeholder-gray-400 focus:ring-2 focus:border-transparent outline-none transition-colors resize-none`}
                  disabled={isSubmitting}
                />
                {errors.description && (
                  <p className="mt-1.5 text-sm text-red-500 flex items-center gap-1">
                    <AlertCircle className="h-4 w-4" />
                    {errors.description}
                  </p>
                )}
              </div>

              {/* Email */}
              <div>
                <label
                  htmlFor="email"
                  className="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5"
                >
                  <Mail className="h-4 w-4" />
                  Email (optional)
                </label>
                <input
                  type="email"
                  id="email"
                  name="email"
                  value={formState.email}
                  onChange={handleChange}
                  placeholder="your@email.com"
                  className={`w-full px-4 py-2.5 rounded-lg border ${
                    errors.email
                      ? 'border-red-300 dark:border-red-600 focus:ring-red-500'
                      : 'border-gray-300 dark:border-gray-600 focus:ring-emerald-500'
                  } bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                  placeholder-gray-400 focus:ring-2 focus:border-transparent outline-none transition-colors`}
                  disabled={isSubmitting}
                />
                {errors.email && (
                  <p className="mt-1.5 text-sm text-red-500 flex items-center gap-1">
                    <AlertCircle className="h-4 w-4" />
                    {errors.email}
                  </p>
                )}
                <p className="mt-1.5 text-xs text-gray-500 dark:text-gray-400">
                  We&apos;ll use this email to respond to your ticket
                </p>
              </div>

              {/* Submit Button */}
              <div className="pt-2">
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full flex items-center justify-center gap-2 px-6 py-3
                           bg-emerald-600 hover:bg-emerald-700 text-white font-medium rounded-lg
                           transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="h-5 w-5 animate-spin" />
                      Submitting...
                    </>
                  ) : (
                    <>
                      <Send className="h-5 w-5" />
                      Submit Ticket
                    </>
                  )}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
